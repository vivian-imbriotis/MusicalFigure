import board
import neopixel

n_led = 30*5 #30 per meter, 5m

pixel_pin = board.D18

order = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, n_led, brightness=0.2,
                  auto_write=True, pixel_order = order)
