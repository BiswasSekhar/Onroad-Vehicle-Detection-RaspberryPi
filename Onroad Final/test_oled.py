import time
from utils import initialize_oled, update_oled_display

def main():
    print("Testing OLED display...")
    oled = initialize_oled()
    
    if oled is None:
        print("OLED initialization failed. Check connections and I2C settings.")
        return
    
    # Test with sample data
    sample_vehicles = {"car": 2, "truck": 1, "bus": 1}
    
    # Display test pattern
    for i in range(5):
        update_oled_display(4, sample_vehicles, 15.5)
        print(f"OLED update {i+1}/5")
        time.sleep(2)
    
    print("OLED display test completed!")

if __name__ == "__main__":
    main()
