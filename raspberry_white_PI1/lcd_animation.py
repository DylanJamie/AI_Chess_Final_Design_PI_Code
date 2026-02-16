import time
import digitalio
import board
import random
import busio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import gc9a01a

BORDER = 20
FONTSIZE = 24
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
BAUDRATE = 24000000

class LCD:
    def __init__(self):
        ## Inits images and sets up LCD screen ##
        
        dc_pin = digitalio.DigitalInOut(board.D25)
        reset_pin = digitalio.DigitalInOut(board.D27)

        spi = busio.SPI(
            clock=board.SCLK,
            MOSI=board.MOSI,
            MISO=None
        )

        # Wait for SPI to be ready (important on Pi 5)
        while not spi.try_lock():
            pass

        spi.configure(baudrate=BAUDRATE, phase=0, polarity=0)
        spi.unlock()

        self.disp = gc9a01a.GC9A01A(
            spi,
            rotation=0,
            width=240,
            height=240,
            x_offset=0,
            y_offset=0,
            cs=None,
            dc=dc_pin,
            rst=reset_pin,
        )

        self.width = self.disp.width
        self.height = self.disp.height
        self.fonts = {}


        ######### Chess Board Code ###########
        self.chessback = Image.open("images/8-bit_chess.png")
        scaled_width = self.width
        scaled_height = self.chessback.height * self.width // self.chessback.width
        self.chessback = self.chessback.resize((scaled_width, scaled_height), Image.BICUBIC)
        x = scaled_width // 2 - self.width // 2
        y = scaled_height // 2 - self.height // 2
        self.chessback = self.chessback.crop((x, y, x + self.width, y + self.height))
        ######### Change Alpha Value ################
        self.chessback = self.chessback.convert("RGBA")
        background = Image.new("RGBA", self.chessback.size, (0, 0, 0, 255))
        alpha = 120
        self.chessback.putalpha(alpha)
        self.chessback = Image.alpha_composite(background, self.chessback)
        self.chessback = self.chessback.convert("RGB")


        ####### Victory Code #######
        self.victory = Image.open("images/victory.webp")
        self.victory = self.victory.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.victory = self.victory.crop((x, y, x + self.width, y + self.height))
        self.victory_rot = self.victory.rotate(270)  ## Copy for rotation


        ####### Loss Code #######
        self.lose = Image.open("images/sad_pic.jpg")
        self.lose = self.lose.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.lose = self.lose.crop((x, y, x + self.width, y + self.height))
        self.lose_left_rot = self.lose.rotate(25)
        self.lose_right_rot = self.lose.rotate(-25)


        ###### Off screen #########
        self.black = Image.new("RGB", (self.width, self.height), (0, 0, 0))

        ###### Draw Image ########
        self.draw = Image.open("images/draw.png")
        self.draw = self.draw.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.draw = self.draw.crop((x, y, x + self.width, y + self.height))

        ##### Player Icon #######
        self.player_icon = Image.open("images/chess_icon.png")
        self.player_icon = self.player_icon.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.player_icon = self.player_icon.crop((x, y, x + self.width, y + self.height))



    def get_box(self, draw, text, font):
        ### Gets measurements to format text to fit on LCD Screen ###
        
        bbox = draw.multiline_textbbox((0, 0), text, font=font)
        width  = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    def draw_centered_text(self, image, text, BOLD, font_size, fill):

        ## Writes text onto screen ###
        draw = ImageDraw.Draw(image)
        if font_size not in self.fonts:
            self.fonts[font_size] = ImageFont.truetype(BOLD, font_size)
        font = self.fonts[font_size]
        text_width, text_height = self.get_box(draw, text, font)

        # Center position
        x = (self.width  - text_width)  // 2
        y = (self.height - text_height) // 2

        draw.text((x,y),text,font=font,fill=fill, align="center")

    def turn_off(self):
        ### Turns off screen ###
        self.disp.image(self.black)

    def game_selection(self):
        ### Game selection mode before game starts ###
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,"Waiting for game \n selection...",BOLD,FONTSIZE - 1,fill="white")
        self.disp.image(chess_copy)


    def show_victory(self, steps=20, delay=0.02):
        ### Victory screen to show if player wins! ###

        for i in range(steps + 1):
            angle = (361 / steps) * i
            frame = self.victory.rotate(angle)
            self.disp.image(frame)
            time.sleep(delay)

    def show_lose(self):
        ### Screen to show if player loses ###
        
        self.disp.image(self.lose_left_rot)
        time.sleep(0.5)
        self.disp.image(self.lose_right_rot)
        time.sleep(0.5)

    def show_score(self, score):
        ### Screen to show score ###
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,f"Score: {score}",BOLD,FONTSIZE+12,fill="white")
        self.disp.image(chess_copy)

    def show_prop(self, prop):
        ### Screen to show win probability ###
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,f"Probability\nWin: {prop}%",BOLD,FONTSIZE+5,fill="white")
        self.disp.image(chess_copy)

    def show_draw(self,):
        ### Screen to show if players draw
        self.disp.image(self.draw)

    def show_screen(self, screen_type, value=None, steps=20, delay=0.02):

        ### Driver function: takes screen type as input and selects screen to show
        match screen_type:
            case "selection":
                self.game_selection()

            case "victory":
                self.show_victory()

                #for i in range(steps + 1):
                 #   angle = (361 / steps) * i
                  #  frame = self.victory.rotate(angle)
                   # self.disp.image(frame)
                    #time.sleep(delay)

            case "lose":
                self.disp.image(self.lose_left_rot)
                time.sleep(0.5)
                self.disp.image(self.lose_right_rot)
                time.sleep(0.5)

            case "score":
                if value is None:
                    value = 0
                self.show_score(value)

            case "prob":
                if value is None:
                    value = 0
                self.show_prop(value)

            case "draw":
                self.show_draw()

            case "off":
                self.turn_off()

            case _:
                raise ValueError(f"Unknown screen type: {screen_type}")



    def show_from_file(self, filename):

        ### Called from main: reads LCD_mode.txt to obtain and send mode to file and send mode to .show_screen()
        while True:
            try:
                with open(filename, "r") as f:
                    data = f.read().strip()
            except OSError:
                time.sleep(0.05)
                continue
        
            if not data:
                time.sleep(0.02)
                continue
            
            parts = data.split()
            
            screen_type = parts[0]
            value = int(parts[1]) if len(parts) > 1 else None
        
            self.show_screen(screen_type, value=value) ## show_screen() includes case statements which selectst the correct mode to show. ##
            
            time.sleep(0.02)
        
def main():

    myLCD = LCD()
    myLCD.turn_off()
    myLCD.show_from_file("display_mode.txt")


    

    #while True:
        
     #   myLCD.show_screen("selection")
      #  time.sleep(2)
       # myLCD.show_screen("victory")
        #time.sleep(2)
        #myLCD.show_screen("lose")
        #time.sleep(2)
        #myLCD.show_screen("score", value=random.randint(0, 100))
        #time.sleep(2)
        #myLCD.show_screen("prob", value=random.randint(0, 100))
        #time.sleep(2)
        #myLCD.show_screen("draw")

if __name__ == "__main__":
    main()
