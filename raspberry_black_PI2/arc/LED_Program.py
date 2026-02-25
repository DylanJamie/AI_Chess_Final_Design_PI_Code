# Import all libraries
import board
import neopixel
import time
import math
from random import randint

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
GREY = (100,100,100)
ORANGE = (139, 64, 0)

pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 24

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

class RingLed:
    def __init__(self, pixel_pin, num_pixels, ORDER):
        self.pixel_pin = pixel_pin
        self.num_pixels = num_pixels
        self.ORDER = ORDER
        self.pixels = neopixel.NeoPixel(self.pixel_pin, self.num_pixels, brightness=0.2, auto_write=False, pixel_order=self.ORDER)

    def _norm(self, num):
        return (num / 255.0) * 0.2

    ## Create spinning pattern on ring. Input color and number of rotations
    def _spin(self, trail_length=18, delay=0.02, max_brightness=255, duration = 5, color = None):

        original_brightness = self.pixels.brightness
        start_time = time.time()
        while time.time() - start_time < duration:
            for head in range(num_pixels):
                self.pixels.fill((0, 0, 0))

                for t in range(trail_length):
                    index = (head - t) % num_pixels
                    # Fade brightness for trailing pixels
                    brightness = int(max_brightness * (1 - t / trail_length))
                    fade = 1 - (t / trail_length)  # 1.0 → 0.0
                    if color is None:
                        self.pixels[index] = (randint(1,brightness), randint(brightness-5, brightness), randint(1,brightness) // 2)
                    else:
                        #self.pixels[index] = (255,165,0)
                        self.pixels[index] = tuple(int(c * fade) for c in color)
                self.pixels.show()
                time.sleep(delay)
        self.pixels.brightness = original_brightness  # RESTORE    


    def _flash(self, delay = 0.00001, duration = 3, steps = 1000, min_brightness = 1, max_brightness = 255, color = None ):
        
        original_brightness = self.pixels.brightness
        start_time = time.time()
        while time.time() - start_time < duration:
            for i in range(min_brightness,max_brightness):

                green = int((i/max_brightness) * max_brightness)

                if color is None:
                    fill_color = (i, i, i)   # default grayscale
                else:
                    fill_color = color       # user-provided color

                self.pixels.fill(fill_color)
                self.pixels.brightness = (float(self._norm(green)))
                self.pixels.show()
                time.sleep(delay)

            for i in range(max_brightness, min_brightness, -1):
                green = int((i/max_brightness) * max_brightness)

                 # Decide which color to use
                if color is None:
                    fill_color = (randint(1,10),255,randint(1,10))   # default grayscale
                else:
                    fill_color = color       # user-provided color

                self.pixels.fill(fill_color)
                self.pixels.brightness = (float(self._norm(green)))
                self.pixels.show()
                time.sleep(delay)
        self.pixels.brightness = original_brightness  # RESTORE    

    def _breath(self, delay = 0.0001, duration = 3, steps = 1000, min_brightness = 1, max_brightness = 255, color = None ):
        original_brightness = self.pixels.brightness
        start_time = time.time()
        t = 0
        while time.time() - start_time < duration:
            # Sin wave: 0 → 1 → 0
            for index in range(num_pixels):
                breathe = (math.sin(0.1*t) + 1) / 2
                # Brightness scaling
                brightness_scale = 0.2 + 0.5 * breathe  # never fully off

                if color is None:
                        # Shade shift: blue → cyan → blue
                    r = 0
                    g = int(80 * breathe)                   # add green as it "inhales"
                    b = int(255 * brightness_scale)
                    self.pixels[index] = (0,randint(0,g),randint(0,b))
                else:
                    r  = int(color[0] * breathe)
                    g = int(color[1] * breathe)
                    b = int(color[2] * brightness_scale)
                    self.pixels.fill((r,g,b))
                
                self.pixels.show()
                t += 0.08
                time.sleep(delay)
        self.pixels.brightness = original_brightness  # RESTORE    

    def game_win(self):
        self._spin(duration = 2)
        self._flash(duration = 2)
        return()

    def game_lose(self):
        self._flash(color = RED, delay = 0.001, min_brightness = 40)
        return()
    def game_draw(self):
        self._flash(color = GREY, delay = 0.001, min_brightness = 40)
        return()

    def under_attack(self):
        self._spin(color = ORANGE, trail_length = 23)
        return()
    def thinking(self):
        self._breath(duration = 10, delay = 0.001)   
        return()

while True:

    player = RingLed(pixel_pin, num_pixels, ORDER)

    #LED Pattern for player Victory
    player.game_win()
    time.sleep(0.25)
    player.game_lose()
    time.sleep(0.25)
    player.game_draw()
    time.sleep(0.25)
    player.under_attack()
    time.sleep(0.25)
    player.thinking()



    time.sleep(0.05)
    player.pixels.fill((0,0,0))
    player.pixels.show()
    pixels.deinit()



