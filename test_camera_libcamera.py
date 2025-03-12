import subprocess

def test_camera_libcamera():
    try:
        # Run the libcamera-hello command to test the camera
        subprocess.run(["libcamera-hello"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_camera_libcamera()
