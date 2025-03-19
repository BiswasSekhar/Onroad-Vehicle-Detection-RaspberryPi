import os
import urllib.request
import shutil
from config import MODEL_PATH, CONFIG_PATH, CLASSES_PATH

def download_file(url, file_path):
    """Download a file from URL and save it to the specified path"""
    print(f"Downloading {url} to {file_path}...")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Download with progress reporting
    with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
        file_size = int(response.info().get('Content-Length', -1))
        if file_size > 0:
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                downloaded += len(chunk)
                out_file.write(chunk)
                done = int(50 * downloaded / file_size)
                print(f"\r[{'=' * done}{' ' * (50 - done)}] {downloaded/1024/1024:.1f}/{file_size/1024/1024:.1f} MB", 
                      end='', flush=True)
            print()
        else:
            shutil.copyfileobj(response, out_file)

def main():
    """Download all necessary model files for YOLO"""
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Download YOLOv4-tiny weights
    if not os.path.exists(MODEL_PATH):
        download_file(
            "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights",
            MODEL_PATH
        )
    else:
        print(f"Model weights already exist at {MODEL_PATH}")
    
    # Download YOLOv4-tiny config
    if not os.path.exists(CONFIG_PATH):
        download_file(
            "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg",
            CONFIG_PATH
        )
    else:
        print(f"Model config already exists at {CONFIG_PATH}")
    
    # Download COCO class names
    if not os.path.exists(CLASSES_PATH):
        download_file(
            "https://raw.githubusercontent.com/AlexeyAB/darknet/master/data/coco.names",
            CLASSES_PATH
        )
    else:
        print(f"Class names already exist at {CLASSES_PATH}")
    
    print("All model files downloaded successfully!")

if __name__ == "__main__":
    main()
