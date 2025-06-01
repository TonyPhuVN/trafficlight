import sys
import subprocess
import tkinter as tk
import traceback
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log.txt'),
        logging.StreamHandler()
    ]
)

def check_dependencies():
    required = ['opencv-python', 'numpy', 'pillow']
    for package in required:
        try:
            logging.info(f'Đang cài đặt {package}...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            logging.info(f'✓ Đã cài đặt {package}')
        except subprocess.CalledProcessError as e:
            logging.error(f'✕ Lỗi cài đặt {package}: {str(e)}')
            return False
        except Exception as e:
            logging.error(f'✕ Lỗi không xác định khi cài đặt {package}: {str(e)}')
            return False
    return True

def main():
    try:
        logging.info('Bắt đầu kiểm tra môi trường...')
        
        # Kiểm tra Python version
        logging.info(f'Python version: {sys.version}')
        
        # Kiểm tra và cài đặt thư viện
        if not check_dependencies():
            logging.error('Không thể cài đặt các thư viện cần thiết')
            return

        logging.info('Khởi động chương trình...')
        
        # Import các module cần thiết
        try:
            import cv2
            logging.info(f'OpenCV version: {cv2.__version__}')
        except ImportError as e:
            logging.error(f'Lỗi import OpenCV: {str(e)}')
            return
            
        try:
            import numpy as np
            logging.info(f'NumPy version: {np.__version__}')
        except ImportError as e:
            logging.error(f'Lỗi import NumPy: {str(e)}')
            return
            
        try:
            from PIL import Image, ImageTk
            logging.info(f'Pillow version: {Image.__version__}')
        except ImportError as e:
            logging.error(f'Lỗi import Pillow: {str(e)}')
            return

        # Khởi động ứng dụng
        try:
            from src.gui import TrafficLightGUI
            root = tk.Tk()
            app = TrafficLightGUI(root)
            root.mainloop()
        except Exception as e:
            logging.error(f'Lỗi khởi động ứng dụng: {str(e)}')
            logging.error(f'Chi tiết lỗi:\n{traceback.format_exc()}')
            return

    except Exception as e:
        logging.error(f'Lỗi không xác định: {str(e)}')
        logging.error(f'Chi tiết lỗi:\n{traceback.format_exc()}')

if __name__ == '__main__':
    main()