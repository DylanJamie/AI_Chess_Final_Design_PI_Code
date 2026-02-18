import time
import digitalio
import board
import random
import busio
from PIL import Image, ImageDraw, ImageFont
import socket
from adafruit_rgb_display import gc9a01a


# Have code run in an infinite loop that checks for the states of the LCD

BORDER = 20
FONTSIZE = 24
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
BAUDRATE = 24000000
HOST = "127.0.0.1"
PORT = 1234

class LCD:
    def __init__(self):
#        cs_pin = digitalio.DigitalInOut(board.CE0)
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
        self.chessback = Image.open("./images/8-bit_chess.png")
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
        self.victory = Image.open("./images/victory.webp")
        self.victory = self.victory.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.victory = self.victory.crop((x, y, x + self.width, y + self.height))
        self.victory_rot = self.victory.rotate(270)  ## Copy for rotation


        ####### Loss Code #######
        self.lose = Image.open("./images/sad_pic.jpg")
        self.lose = self.lose.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.lose = self.lose.crop((x, y, x + self.width, y + self.height))
        self.lose_left_rot = self.lose.rotate(25)
        self.lose_right_rot = self.lose.rotate(-25)


        ###### Off screen #########
        self.black = Image.new("RGB", (self.width, self.height), (0, 0, 0))

        ###### Draw Image ########
        self.draw = Image.open("./images/draw.png")
        self.draw = self.draw.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.draw = self.draw.crop((x, y, x + self.width, y + self.height))

        ##### Player Icon #######
        self.player_icon = Image.open("./images/chess_icon.png")
        self.player_icon = self.player_icon.resize((scaled_width, scaled_height), Image.BICUBIC)
        self.player_icon = self.player_icon.crop((x, y, x + self.width, y + self.height))



    def get_box(self, draw, text, font):
        bbox = draw.multiline_textbbox((0, 0), text, font=font)
        width  = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    def draw_centered_text(self, image, text, BOLD, font_size, fill):
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
        self.disp.image(self.black)






    def game_selection(self):
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,"Waiting for game \n selection...",BOLD,FONTSIZE - 1,fill="white")
        self.disp.image(chess_copy)


    def show_victory(self, steps=20, delay=0.02):
        # rotate the victory image gradually from 0 → 270 degrees
        for i in range(steps + 1):
            angle = (361 / steps) * i
            frame = self.victory.rotate(angle)
            self.disp.image(frame)
            time.sleep(delay)


    #def show_victory(self):
        # self.disp.image(self.victory)
        # self.disp.image(self.victory_rot)


    def show_lose(self):
        self.disp.image(self.lose_left_rot)
        time.sleep(0.5)
        self.disp.image(self.lose_right_rot)
        time.sleep(0.5)

    def turn_off(self):
        self.disp.image(self.black)

    def show_score(self, score):
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,f"Score: {score}",BOLD,FONTSIZE+12,fill="white")
        self.disp.image(chess_copy)

    def show_prop(self, prop):
        chess_copy = self.chessback.copy()
        self.draw_centered_text(chess_copy,f"Probability\nWin: {prop}%",BOLD,FONTSIZE+5,fill="white")
        self.disp.image(chess_copy)

    def show_draw(self,):
        self.disp.image(self.draw)

    def show_screen(self, screen_type, value=None, steps=20, delay=0.02):
        match screen_type:
            case "selection":
                self.game_selection()

            case "victory":
                for i in range(steps + 1):
                    angle = (361 / steps) * i
                    frame = self.victory.rotate(angle)
                    self.disp.image(frame)
                    time.sleep(delay)

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
                self.show_draw()


## Header ##
myLCD = LCD()  # create LCD object
myLCD.turn_off()
## init socket that recieves 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

# recieve input from socket as screentype   
conn, addr = s.accept()
screen_type = None
conn.settimeout(0.1)

### Poll for new screentype
### if screen type is new, send to LCD, else, send keep running current LCD

while True:

    try:
        data = conn.recv(1024)
        data_dec = data.decode().strip()

        if data_dec != "":
            screen_type = data_dec
            
        
        print("screen type: ", type(screen_type))    
        
    except socket.timeout:
        pass
    

    myLCD.show_screen(screen_type) ## Send what was recieved from socket to LCD code to update screen
    
conn.close()
s.close()
print("code is done")
