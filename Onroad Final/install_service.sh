#!/bin/bash

echo "Creating systemd service for auto-starting vehicle detection..."

# Create service file
cat > vehicle-detection.service << EOF
[Unit]
Description=Vehicle Detection System
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/Project/Onroad Final/start.sh
WorkingDirectory=/home/pi/Project/Onroad Final
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd directory
sudo cp vehicle-detection.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vehicle-detection.service
sudo systemctl start vehicle-detection.service

echo "Service installed! Vehicle detection will now start automatically on boot."
echo "Use these commands to manage the service:"
echo "  sudo systemctl status vehicle-detection  # Check status"
echo "  sudo systemctl stop vehicle-detection    # Stop service"
echo "  sudo systemctl start vehicle-detection   # Start service"
echo "  sudo systemctl disable vehicle-detection # Disable autostart"
