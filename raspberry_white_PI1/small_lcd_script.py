import time
from lcd_animation import LCD
test = LCD()
test.show_screen("victory")
time.sleep(1)
print("If you see the score, your LCD is wired correctly!")
test.stop_all()
