#!/usr/bin/env bash

# pi_start.py
# This script starts the python pi_chess_server, lcd, and LED code

set -e

# Array to keep track of process IDs
pids=()

# Clean up and stop all programs function
cleanup() {
    trap - SIGINT SIGTERM
    echo
    echo "Stopping all processes: ${pids[*]}"
    # Kill the specific PIDs we started
    if [ ${#pids[@]} -ne 0 ]; then
        kill "${pids[@]}" 2>/dev/null
    fi
    exit 0
}

# Trap Ctrl+C (SIGINT) and termination signals
trap cleanup SIGINT SIGTERM

echo "Press Ctrl+C to stop all programs"

# Access the environment
# Note: Ensure this path is correct for your Pi
source ~/pi-env/bin/activate

# 1. Run the LCD Code
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/lcd_animation.py &
pids+=($!)
echo "LCD Program started (PID: $!)"
sleep 1

# 2. Run the LED Code
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/LED_Program.py &
pids+=($!)
echo "LED Program started (PID: $!)"
sleep 1

# 3. Run the Main Program
python ~/Downloads/PIGAME_TEST/raspberry_white_PI1/pi_chess_server_white.py &
pids+=($!)
echo "Main Server started (PID: $!)"

echo "Environment fully started. Waiting for processes..."

# Wait for the background processes to finish (or for a Ctrl+C)
wait
