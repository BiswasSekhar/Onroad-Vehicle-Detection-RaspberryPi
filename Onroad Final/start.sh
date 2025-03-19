#!/bin/bash

cd /home/pi/Project/Onroad Final

# Check for required dependencies
if ! pip3 list | grep -q adafruit-circuitpython-ssd1306; then
    echo "Installing OLED display dependencies..."
    pip3 install adafruit-circuitpython-ssd1306 pillow
fi

# Check if models exist, download if needed
if [ ! -f "models/yolov4-tiny.weights" ]; then
    echo "Downloading required model files..."
    python3 download_models.py
fi

# Create log directory if it doesn't exist
mkdir -p logs

echo "Starting vehicle detection system..."
python3 main.py
