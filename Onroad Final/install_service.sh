#!/bin/bash

echo "Creating systemd service for auto-starting vehicle detection..."

# Ensure we're in the correct directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
echo "Using project directory: $PROJECT_DIR"

# Make sure start.sh is executable
if [ ! -x "$PROJECT_DIR/start.sh" ]; then
    echo "Making start.sh executable..."
    chmod +x "$PROJECT_DIR/start.sh"
fi

# Create a wrapper script that properly sets up the environment
cat > "$PROJECT_DIR/service_wrapper.sh" << EOF
#!/bin/bash
# This script sets up the proper environment before running the main script
# It resolves issues with systemd services not having the correct PATH or environment

# Set up environment variables
export PATH=\$PATH:/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
export PYTHONPATH=\$PYTHONPATH:$PROJECT_DIR
export DISPLAY=:0

# Change to project directory to ensure relative paths work
cd "$PROJECT_DIR"

# Run the main script
/bin/bash "$PROJECT_DIR/start.sh"
EOF

# Make the wrapper executable
chmod +x "$PROJECT_DIR/service_wrapper.sh"

# Create service file with properly quoted paths
cat > vehicle-detection.service << EOF
[Unit]
Description=Vehicle Detection System
After=network.target
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=/bin/bash "$PROJECT_DIR/service_wrapper.sh"
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd directory
echo "Installing service file to /etc/systemd/system/..."
sudo cp vehicle-detection.service /etc/systemd/system/

# Fix any possible permission issues
echo "Setting proper permissions..."
sudo chown pi:pi "$PROJECT_DIR" -R

# Enable and start service
echo "Enabling service to auto-start on boot..."
sudo systemctl daemon-reload
sudo systemctl enable vehicle-detection.service

echo "Do you want to start the service now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Starting service..."
    sudo systemctl start vehicle-detection.service
    sleep 2
    echo "Service status:"
    sudo systemctl status vehicle-detection.service
else
    echo "Service will start on next reboot."
fi

echo "Service installation complete! Vehicle detection will now start automatically on boot."
echo ""
echo "Use these commands to manage the service:"
echo "  sudo systemctl status vehicle-detection  # Check status"
echo "  sudo systemctl stop vehicle-detection    # Stop service"
echo "  sudo systemctl start vehicle-detection   # Start service"
echo "  sudo systemctl disable vehicle-detection # Disable autostart"
echo ""
echo "To view logs from the service:"
echo "  sudo journalctl -u vehicle-detection -f"
