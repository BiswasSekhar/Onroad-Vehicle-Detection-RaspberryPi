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

## Performance Optimization

To fix frame drops and improve performance:

1. Run the performance test to find optimal settings for your Pi:
```
python3 performance_test.py
```

2. Update your configuration based on the recommendations:
   - Adjust `BLOB_SIZE` for inference (smaller = faster, less accurate)
   - Set `DETECTION_INTERVAL` to process every Nth frame (higher = faster)
   - Set `USE_THREADING` to true for parallel processing
   - Set `ENABLE_GPU` if your Pi supports OpenCL
   - Adjust `OLED_UPDATE_INTERVAL` to reduce display overhead

3. For maximum performance:
   - Disable camera preview with `ENABLE_PREVIEW = False`
   - Use a smaller camera resolution (e.g., 320x240)
   - Close other applications running on the Pi
   - Consider overclocking your Raspberry Pi

4. Other optimizations:
   - Mount your SD card in read-only mode to prevent corruption
   - Use a properly sized power supply (at least 2.5A)
   - Add a heatsink or fan to prevent thermal throttling

## Automatic Startup

To make the vehicle detection system start automatically when your Raspberry Pi boots:

1. Run the included installation script:
```
chmod +x install_service.sh
./install_service.sh
```

2. The script will create and enable a systemd service. You can choose to start it immediately or wait until the next reboot.

3. To verify it's working:
```
sudo systemctl status vehicle-detection
```

4. To view the logs from the auto-started service:
```
sudo journalctl -u vehicle-detection -f
```

5. If you need to disable auto-start:
```
sudo systemctl disable vehicle-detection
```

### Alternative Auto-start Methods

If the systemd service doesn't work for your needs, there are alternative methods:

#### Using crontab:
```
crontab -e
```
Then add this line:
```
@reboot sleep 30 && cd /home/pi/Project/Onroad Final && ./start.sh >> /home/pi/vehicle_detection.log 2>&1
```

#### Using rc.local:
Edit the rc.local file:
```
sudo nano /etc/rc.local
```
Add this line before the `exit 0` line:
```
(sleep 30 && cd /home/pi/Project/Onroad Final && ./start.sh) &
```

The 30-second sleep allows time for the system to fully boot before starting the application.

## Troubleshooting

- If the camera isn't detected, ensure it's properly connected and enabled
- Low FPS? Try reducing resolution or disabling the preview
- For memory errors, restart your Raspberry Pi and try again
- OLED not working? Check your I2C connections and address
