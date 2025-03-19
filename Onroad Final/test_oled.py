import time
from utils import initialize_oled, update_oled_display

def main():
    print("Testing OLED display with new large font format...")
    oled = initialize_oled()
    
    if oled is None:
        print("OLED initialization failed. Check connections and I2C settings.")
        return
    
    # Test with different vehicle combinations
    test_cases = [
        # Total count, vehicle types dictionary
        (4, {"car": 2, "truck": 1, "bus": 1}),
        (3, {"car": 3}),
        (2, {"motorbike": 1, "bicycle": 1}),
        (5, {"car": 2, "truck": 1, "bus": 1, "motorbike": 1}),
        (0, {})  # No vehicles
    ]
    
    # Display each test case
    for i, (count, vehicles) in enumerate(test_cases):
        print(f"Test {i+1}/{len(test_cases)}: {count} vehicles - {vehicles}")
        update_oled_display(count, vehicles)
        time.sleep(3)  # Show each test case for 3 seconds
    
    print("OLED display test completed!")

if __name__ == "__main__":
    main()
