#!/bin/bash

# Set the full path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Starting from directory: $SCRIPT_DIR"

# Change to correct directory - use the script directory
cd "$SCRIPT_DIR"

# Make sure python3 is in the path
export PATH=$PATH:/usr/bin:/usr/local/bin

# Check if running in graphical environment
if [ -z "$DISPLAY" ] && [ -e "/dev/tty1" ]; then
    echo "No display environment detected, setting DISPLAY=:0"
    export DISPLAY=:0
    
    # If running as a service without X, set to headless mode
    if ! pgrep -x Xorg > /dev/null; then
        echo "No X server running, modifying config to run headless"
        if grep -q "ENABLE_PREVIEW = True" config.py; then
            # Create a temporary file with modified configuration
            sed 's/ENABLE_PREVIEW = True/ENABLE_PREVIEW = False/' config.py > config.py.tmp
            mv config.py.tmp config.py
        fi
    fi
fi

# Check for required dependencies
if ! pip3 list | grep -q adafruit-circuitpython-ssd1306; then
    echo "Installing OLED display dependencies..."
    pip3 install adafruit-circuitpython-ssd1306 pillow
fi

# Check if models exist, download if needed
if [ ! -f "models/yolov4-tiny.weights" ]; then
    echo "Downloading required model files..."
    mkdir -p models
    python3 download_models.py
fi

# Create log directory if it doesn't exist
mkdir -p logs
mkdir -p data_logs

# Print environment for debugging
echo "Environment:"
echo "PATH=$PATH"
echo "PYTHONPATH=$PYTHONPATH"
echo "DISPLAY=$DISPLAY"
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"

echo "Starting vehicle detection system..."
python3 main.py
