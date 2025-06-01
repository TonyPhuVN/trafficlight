import sys
import tkinter as tk
from src.gui import TrafficLightGUI

def check_dependencies():
    try:
        import cv2
        import numpy
        from PIL import Image
    except ImportError as e:
        print(f"Lỗi: Thiếu thư viện cần thiết. {str(e)}")
        print("Hãy cài đặt các thư viện sau:")
        print("pip install opencv-python numpy pillow")
        return False
    return True

def main():
    if not check_dependencies():
        sys.exit(1)
    
    try:
        root = tk.Tk()
        app = TrafficLightGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Lỗi khởi động ứng dụng: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()