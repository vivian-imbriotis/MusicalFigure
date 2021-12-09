import board
import neopixel
from av_handling import Musician

from time import sleep

import numpy as np

n_led = 30*5 #30 per meter, 5m

pixel_pin = board.D18

order = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, n_led, brightness=0.2,
                  auto_write=True, pixel_order = order)

musician = Musician("jinglebells.mp3")

f = np.linspace(0,1000,n_led)

musician.start_playback()

