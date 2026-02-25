# hardware_controller.py
# this will create a way for the LEDs and LCD screens to run

# import the libraries
import threading
import time
from lcd_animation import LCD
from LED_Program import RingLed
import board

# Chess hardware class
class ChessHardware:
    def __init__(self):
        self.led = RingLed(pixel_pin=board.D18, num_pixels=16, ORDER="GRBW")
        self.lcd = LCD()
        
        # State Management
        self.current_animation = "off"
        self._running = True
        
        # Start the PERMANENT background thread immediately
        self.animation_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.animation_thread.start()

    def _main_loop(self):
        """The only thread that ever runs. It just switches logic based on state."""
        while self._running:
            state = self.current_animation
            
            if state == "thinking":
                # Only call these if we are still in thinking mode
                self.led.thinking() 
                self.lcd.show_screen("score", 15)
                time.sleep(0.1)

            elif state == "win":
                # Play the LED win sequence once
                self.led.game_win()
                # Stay on the victory screen until state changes
                while self.current_animation == "win" and self._running:
                    self.lcd.show_screen("victory")
                    time.sleep(0.1)

            elif state == "lose":
                self.led.game_lose()
                while self.current_animation == "lose" and self._running:
                    self.lcd.show_screen("lose")
                    time.sleep(0.1)

            elif state == "off":
                self.lcd.show_screen("off")
                time.sleep(0.5)
            
            else:
                time.sleep(0.1) # Idle sleep

    def start_animation(self, animation_type):
        """Now this just updates the state variable. No new threads!"""
        print(f"Hardware State Change: {animation_type}")
        self.current_animation = animation_type

    def stop_all(self):
        """Sets state to off"""
        self.current_animation = "off"

    def is_animating(self):
        return self.current_animation != "off"
