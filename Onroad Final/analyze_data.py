import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime

def analyze_log_file(log_file):
    """Analyze vehicle detection data from CSV log file"""
    print(f"Analyzing data from {log_file}...")
    
    # Read the CSV file
    df = pd.read_csv(log_file)
    
    # Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Basic statistics
    total_duration = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds() / 60
    avg_fps = df['FPS'].mean()
    max_vehicles = df['Total_Vehicles'].max()
    total_vehicles_detected = df['Total_Vehicles'].sum()
    
    print(f"\nAnalysis Summary:")
    print(f"Duration: {total_duration:.1f} minutes")
    print(f"Average FPS: {avg_fps:.1f}")
    print(f"Maximum vehicles in frame: {max_vehicles}")
    print(f"Total vehicle detections: {total_vehicles_detected}")
    
    # Create a simple visualization
    plt.figure(figsize=(12, 8))
    
    # Plot vehicle counts over time
    plt.subplot(2, 1, 1)
    plt.plot(df['Timestamp'], df['Cars'], label='Cars')
    plt.plot(df['Timestamp'], df['Trucks'], label='Trucks')
    plt.plot(df['Timestamp'], df['Buses'], label='Buses')
    plt.plot(df['Timestamp'], df['Motorbikes'], label='Motorbikes')
    plt.plot(df['Timestamp'], df['Bicycles'], label='Bicycles')
    plt.title('Vehicle Detection Over Time')
    plt.ylabel('Count')
    plt.legend()
    
    # Plot FPS over time
    plt.subplot(2, 1, 2)
    plt.plot(df['Timestamp'], df['FPS'])
    plt.title('Performance (FPS) Over Time')
    plt.ylabel('Frames Per Second')
    
    # Save the plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_file = os.path.join(os.path.dirname(log_file), f"analysis_{timestamp}.png")
    plt.tight_layout()
    plt.savefig(plot_file)
    
    print(f"Analysis plot saved to {plot_file}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Analyze vehicle detection data')
    parser.add_argument('log_file', help='Path to the CSV log file to analyze')
    args = parser.parse_args()
    
    if not os.path.exists(args.log_file):
        print(f"Error: Log file {args.log_file} not found")
        return
    
    analyze_log_file(args.log_file)

if __name__ == "__main__":
    main()
