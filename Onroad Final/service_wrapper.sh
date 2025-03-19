#!/bin/bash
# This script sets up the proper environment before running the main script
# It resolves issues with systemd services not having the correct PATH or environment

# Set up environment variables
export PATH=$PATH:/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
export PYTHONPATH=$PYTHONPATH:/home/pi/Project/Onroad Final
export DISPLAY=:0

# Change to project directory to ensure relative paths work
cd "/home/pi/Project/Onroad Final"

# Run the main script
/bin/bash "/home/pi/Project/Onroad Final/start.sh"
