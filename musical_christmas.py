import board
import neopixel

import numpy as np

from musical_figure import Musician

from time import sleep

MAX_FREQ = 1000

n_led = 30*5 #30 per meter, 5m

pixel_pin = board.D18

order = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, n_led, brightness=0.2,
                  auto_write=False, pixel_order = order)

led_freqs = np.linspace(1,MAX_FREQ, n_led)


i = 0

def update(musician):
  global i
#  new_colors = musician.get_colors_for_frequencies(led_freqs)
  i += 0.025
  i = i%1
  pixels[:] = (np.ones((150,3)) * i * 255).astype(int)
  print(pixels)
  pixels.show()

if __name__=="__main__":
 # music = Musician('jinglebells.mp3')
 # music.start_playback()
  while True:
    music=None
    with pixels:
      update(music)
      sleep(1)
