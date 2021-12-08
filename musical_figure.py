# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 14:52:10 2021

@author: vivia
"""
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np


from time import time

from av_handling import Musician, freq_to_color, TOP_FREQ, SPECTROGRAMS_PER_SEC

class MusicalFigure:
    def __init__(self,file):
        self.musician = Musician(file)
        
        #Set up the plot.
        self.fig,(detailed_ax,display_ax) = plt.subplots(nrows=2)
        self.fig.set_facecolor('black')
        detailed_ax.set_facecolor('black')
        
        #We need to know how tall to make our plot, so we need the max
        #spectral power density
        max_extent = self.musician.Sxx.max()
        detailed_ax.set_ylim(0, max_extent)
        
        self.detailed_ax = detailed_ax
        
        #This artist will draw the periodogram each frame in blue
        f,Sxx = self.musician.get_periodogram()
        self.frequency_artist, = detailed_ax.plot(f, Sxx)
        
        #Locate spectrogram peaks and draw dotted vertical lines, colored
        #based on which note they represent
        
        f, peaks = self.musician.get_key_frequencies()
        self.peak_artist = detailed_ax.vlines(f[peaks],0,max_extent,
                          color=[freq_to_color(i) for i in f[peaks]], 
                          linestyle="--")
        
        
        #Start building our second, bottom axis. This will display an image
        #where the x-axis represents frequency, but frequencies are colored
        #based on nearby key (i.e. peak spectral density) frequencies/tones
        display_ax.set_facecolor('black')
        self.frequencies_for_image = np.linspace(0,TOP_FREQ,300)
        
        #We can memoize many of the results of calls to our musician class
        #to save us interframe computation
        self.musician.precompute_all_colorspaces(self.frequencies_for_image)
        
        colorspace = self.musician.get_colors_for_frequencies(self.frequencies_for_image)
        self.display_artist = display_ax.imshow(colorspace.reshape(1,-1,3), aspect='auto')
        
        #Define our animation, which just calls MusicalFigure.update
        #               every 1/SPECTROGRAMS_PER_SEC seconds
        self.ani = FuncAnimation(self.fig,self.update,
                                 interval=1000/SPECTROGRAMS_PER_SEC-15)
        self.fig.canvas.mpl_connect('close_event', self.on_close)
            
    def update(self,frame):
        '''
        Update all artists by making calls to the underlying musician object.
        Called repeatedly to animate the figure.
        '''
        if frame==0:
            self.musician.start_playback()
        t = time()
        f, peaks = self.musician.get_key_frequencies(t=t)
        self.peak_artist.remove()
        self.peak_artist = self.detailed_ax.vlines(
            f[peaks],0,self.musician.Sxx.max(), 
            color=[freq_to_color(i) for i in f[peaks]],
            linestyle = '--')
        
        
        colors = self.musician.get_colors_for_frequencies(self.frequencies_for_image,
                                                          t=t)
        self.display_artist.set_data(colors.reshape(1,-1,3))
        f, periodogram = self.musician.get_periodogram(t=t)
        self.frequency_artist.set_data(f, periodogram)
    
    #When the figure is closed, the music should stop
    def on_close(self,event):
        self.musician.stop_playback()
    
    def show(self):
        '''
        Display the animated figure.
        '''
        self.fig.show()

        

if __name__=="__main__":
    fig = MusicalFigure(file = "jinglebells.mp3")
    fig.show()
