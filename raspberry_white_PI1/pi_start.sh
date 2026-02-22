#!/usr/bin/env bash

# pi_start.py
# this script will run and start up the python pi_chess_server, lcd and LED code

# if any of the scripts fail stop the whole process
set -e

# Print a User Message
echo "Press Ctrl+C to stop all programs"

# Clean up and stop all programs
cleanup() {
    echo
    echo "Stopping all processes..."
    kill 0 # Kill all processes in current Group
}

# when you press Ctrl+C Stop all the processes in this group
trap cleanup SIGINT SIGTERM

# Access the enviorment
source ~/pi-env/bin/activate

# Run the LCD Code
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/lcd_animation.py &

# Run the LED Code
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/LED_Program.py &

# Run the Main Program
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/pi_chess_server_white.py &

wait
