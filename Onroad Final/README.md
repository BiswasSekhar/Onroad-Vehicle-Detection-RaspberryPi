# Onroad Vehicle Detection System

A Raspberry Pi-based system for detecting vehicles on road using the Camera Module 2 and YOLOv4-tiny.

## Hardware Requirements

- Raspberry Pi 4 (recommended) or Raspberry Pi 3B+
- Raspberry Pi Camera Module 2
- 4-pin OLED Display (SSD1306 or compatible)
- Power supply for Raspberry Pi
- (Optional) Display for visual feedback
- (Optional) Battery pack for portable use

## Hardware Setup

### Camera Module
Connect the Raspberry Pi Camera Module 2 to the camera port on the Raspberry Pi.

### OLED Display
Connect the 4-pin OLED display to the Raspberry Pi as follows:
- VCC → 3.3V (Pin 1)
- GND → Ground (Pin 6)
- SDA → GPIO2 (Pin 3)
- SCL → GPIO3 (Pin 5)

## Software Setup

1. Install required packages:
```
sudo apt update
sudo apt install -y python3-opencv python3-picamera2 python3-numpy
sudo pip3 install adafruit-circuitpython-ssd1306 pillow
```

2. Clone or copy this repository to your Raspberry Pi

3. Make the start script executable:
```
chmod +x start.sh
```

4. Run the start script to begin detection:
```
./start.sh
```

The script will automatically download the YOLOv4-tiny model files if they don't exist.

## Configuration

You can customize the detection parameters by editing the `config.py` file:

- Adjust camera resolution and framerate
- Change detection thresholds
- Enable/disable preview
- Configure logging options
- Adjust OLED display settings

## OLED Display

The OLED display shows:
- Total number of vehicles detected in large text
- Count of each type of vehicle detected (car, bus, truck, etc.)
- Vehicle types are sorted by count with the most common types shown first
- Only the top 3 vehicle types are shown to ensure readability

If you're having issues with the OLED display:
- Check the I2C address in config.py (common values are 0x3C or 0x3D)
- Ensure I2C is enabled on your Raspberry Pi (`sudo raspi-config`)
- Verify the connections are secure
- Run the test script to check if the display is working: `python3 test_oled.py`

## Performance Tips

- YOLOv4-tiny is used for balance between speed and accuracy
- Lower resolution increases speed but reduces detection accuracy
- Increase CONFIDENCE_THRESHOLD for fewer but more reliable detections
- For better performance, consider overclocking your Raspberry Pi

## Troubleshooting

- If the camera isn't detected, ensure it's properly connected and enabled
- Low FPS? Try reducing resolution or disabling the preview
- For memory errors, restart your Raspberry Pi and try again
- OLED not working? Check your I2C connections and address
