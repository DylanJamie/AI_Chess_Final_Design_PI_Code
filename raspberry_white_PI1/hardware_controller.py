# hardware_controller.py
# this will create a way for the LEDs and LCD screens to run

# import the libraries
import threading
import time
from lcd_animation import LCD
from LED_Program import RingLed
import board

# Create a class to import to pi_chess_server_white.py
class ChessHardware:
    def __init__(self):
        self.led = RingLed(pixel_pin=board.D18, num_pixels=16, ORDER="GRBW")
        self.lcd = LCD()
        self.animation_thread = None
        self._stop_event = threading.Event()
        self._current_anim = None
        
    def _run_animation(self, animation_type):
        """Internal loop to run animaitons without blocking the code from pi_chess_server_white"""
        if animation_type == "thinking":
            while not self._stop_event.is_set():
                self.led.thinking()
                self.lcd.show_screen("score", 15)
                time.sleep(0.1)
        elif animation_type == "win":
            # Start LED sequence
            self.led.game_win()
            # Keep the LCD on "victory" until the next game starts
            while not self._stop_event.is_set():
                self.lcd.show_screen("victory")
                time.sleep(1)
        elif animation_type == "lose":
            self.led.game_lose() # Make sure this is in LED_Program.py
            while not self._stop_event.is_set():
                self.lcd.show_screen("lose")
                time.sleep(1)
                # self.lcd.display_text("CHECKMATE! I WIN")

                # this is where lose, draw and start patterns will go

    def is_animating(self):
        """Returns True if a thread is currently running"""
        return self.animation_thread is not None and self.animation_thread.is_alive()
                
    def start_animation(self, animation_type):
        """Start a new animation in the background"""
        if self.is_animating() and self.current_animation == animation_type:
            return
        
        self.stop_all()
        self.current_animation = animation_type
        self._stop_event.clear()
        self.animation_thread = threading.Thread(target=self._run_animation, args=(animation_type,))
        # self.animation_thread.daemon = True # Make sure it dies if the main program exits
        self.animation_thread.start()
            
    def stop_all(self):
        """Stops any running background animations"""
        self._stop_event.set()
        if self.animation_thread:
            self.animation_thread.join(timeout=0.2) # Give it 200ms to exit gracefully
        self._stop_event.clear()
