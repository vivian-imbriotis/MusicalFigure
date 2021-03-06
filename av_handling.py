# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 17:58:29 2021

@author: vivia
"""

import colorsys
import numpy as np

import pydub
import simpleaudio
from pydub.playback import _play_with_simpleaudio as play
from scipy.signal import spectrogram, find_peaks

from time import time

from helpers import memoized

twlth_rt_2 = 2**(1/12)
SPECTROGRAMS_PER_SEC = 10
TOP_FREQ = 1500

def pydub_to_np(audio: pydub.AudioSegment) -> (np.ndarray, int):
    """
    Converts pydub audio segment into np.float32 of shape [duration_in_seconds*sample_rate, channels],
    where each value is in range [-1.0, 1.0]. 
    Returns tuple (audio_np_array, sample_rate).
    """
    return np.array(audio.get_array_of_samples(), dtype=np.float32).reshape((-1, audio.channels)) / (
            1 << (8 * audio.sample_width - 1)), audio.frame_rate

def note_to_freq(note: float) -> float:
    '''
    Convert a musical note representation to it's equal temprament 
    440hz-A-tuning frequency representation

    Parameters
    ----------
    note : float
        The note; 0 is 440hz A, then each tone is an additional 1.

    Returns
    -------
    frequency : float
        The corresponding frequency in Hz
    '''
    return 440 * (twlth_rt_2)**note


def freq_to_note(freq: float) -> float:
    return np.log(freq/440) / np.log(twlth_rt_2)

def freq_to_color(freq: float, luminosity: float = 0.5) -> float:
    return colorwheel((freq_to_note(freq)%12)/12, luminosity)


def colorwheel(x: float, luminosity: float = 0.5) -> (float,float,float):
    '''
    Map a float input X into a pure hue. X is mapped to the same color
    as X + N for integer N.

    Parameters
    ----------
    x : float
        A float input.
    luminosity : float, optional
        The luminosity of the output. The default is 0.5.

    Returns
    -------
    (float,float,float)
        The RBG color representation.

    '''
    return colorsys.hls_to_rgb(x%1,luminosity,1)


@memoized
def construct_colorspace(key_fs, frequencies) -> (np.ndarray, np.ndarray):
    colors = np.zeros((len(frequencies),3),dtype=float)
    averages = [(key_fs[i]+key_fs[i+1])/2 for i in range(len(key_fs)-1)]
    averages.append(frequencies[-1])
    averages.insert(0,0)
    averages = np.asarray(averages)
    if len(key_fs)>0:
        for idx,f in enumerate(frequencies):
            nearest_key_frequency = min(key_fs, key=lambda x:abs(x-f))
            nearest_average = min(averages, key=lambda x:abs(x-nearest_key_frequency))
            total_gradient_distance = np.abs(nearest_key_frequency - nearest_average)
            current_distance = np.abs(f - nearest_key_frequency)
            luminosity = max(0,0.5 - 0.5*(current_distance / total_gradient_distance))
            colors[idx] = freq_to_color(nearest_key_frequency, luminosity)
    
        # colors[frequencies<key_fs[0]] = freq_to_color(key_fs[0])
        # colors[frequencies>key_fs[-1]] = freq_to_color(key_fs[-1])
    else:
        colors[:] = freq_to_color(440,luminosity=0)
    return colors

class Musician:
    '''
    An object that plays back the music_file, and during playback can 
    supply information about the music, such as the intantenous periodogram,
    the current 'key frequencenies', i.e. those frequencies/notes with the
    highest power spectral density.
    '''
    def __init__(self, music_file):
        
        #Get our music
        self.seg = pydub.AudioSegment.from_file(music_file)
        self.duration = len(self.seg)/1000 #Duration in seconds
        
        #Draw samples from it and generate a tukey-filter spectrogram
        samples, freq = pydub_to_np(self.seg)
        f, t, Sxx = spectrogram(samples.mean(axis=-1), freq, mode="magnitude",
                                nperseg = self.seg.frame_rate//SPECTROGRAMS_PER_SEC,
                                noverlap=0)
        self.find_peaks = memoized(lambda pgram: find_peaks(pgram, 
                                                            distance = 5, 
                                                            height = 0.007))
        
        #Eliminate frequencies above a certain cutoff
        top_freq = np.searchsorted(f,TOP_FREQ) + 1
        self.f, self.t, self.Sxx = f[:top_freq], t, Sxx[:top_freq,:]
        
        self.start_time = None
        self.playing = False
    
    def start_playback(self):
        if not self.playing:
            self.playing= True
            play(self.seg)
            self.start_time = time()
    
    def get_song_time(self,t):
        '''
        Get time elapsed since the song began (0 if not playing).
        t should be the result of a call to time.time()
        '''
        if self.start_time is not None:
            playtime = t - self.start_time
            if playtime > self.duration and self.playing:
                self.start_playback()
            return playtime
        return 0
        
    def get_key_frequencies(self,t = time()):
        f, periodogram = self.get_periodogram(t)
        periodogram = tuple(periodogram) #numpy arrays aren't hashable
        peaks, peak_attributes = self.find_peaks(periodogram)
        return f, peaks
    
    def get_colors_for_frequencies(self,frequencies,t=time()):
        frequencies = tuple(frequencies)
        f, key_fs = self.get_key_frequencies(t)
        colorspace = construct_colorspace(tuple(f[key_fs]), frequencies)
        return colorspace
    
    def get_periodogram(self,t = time()):
        song_t = self.get_song_time(t)
        time_idx = np.searchsorted(self.t,song_t)
        return self.f, self.Sxx[:,time_idx]
    
    def stop_playback(self):
        simpleaudio.stop_all()
        self.playing = False
    
    def precompute_all_colorspaces(self, frequencies):
        frequencies = tuple(frequencies)
        for time_idx, t in enumerate(self.t):
            periodogram = self.Sxx[:,time_idx]
            periodogram = tuple(periodogram)
            print(periodogram)
            peaks, peak_attributes = self.find_peaks(periodogram)
            construct_colorspace(tuple(self.f[peaks]), frequencies)
                    
        
    def __del__(self):
        self.stop_playback()
        
    
