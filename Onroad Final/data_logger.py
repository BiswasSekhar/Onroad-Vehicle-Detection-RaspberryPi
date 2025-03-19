import csv
import os
import time
from datetime import datetime

class VehicleDataLogger:
    def __init__(self, log_dir="/home/pi/Project/Onroad Final/data_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a new CSV file for each session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(log_dir, f"vehicle_data_{timestamp}.csv")
        
        # Initialize CSV file with headers
        with open(self.csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Timestamp', 'Total_Vehicles', 'Cars', 'Trucks', 
                'Buses', 'Bicycles', 'Motorbikes', 'FPS'
            ])
        
        print(f"Data logger initialized, saving to: {self.csv_path}")
    
    def log_data(self, vehicle_count, vehicle_types, fps):
        """Log detection data to CSV file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract vehicle counts by type (0 if not detected)
        cars = vehicle_types.get('car', 0)
        trucks = vehicle_types.get('truck', 0)
        buses = vehicle_types.get('bus', 0)
        bicycles = vehicle_types.get('bicycle', 0)
        motorbikes = vehicle_types.get('motorbike', 0)
        
        # Write to CSV
        with open(self.csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                timestamp, vehicle_count, cars, trucks, 
                buses, bicycles, motorbikes, round(fps, 2)
            ])
