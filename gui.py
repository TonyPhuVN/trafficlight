import tkinter as tk
from tkinter import ttk, messagebox
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
except ImportError as e:
    tk.messagebox.showerror("Lỗi", f"Thiếu thư viện: {str(e)}\nHãy cài đặt: pip install opencv-python numpy pillow")
    raise

from traffic_monitor import TrafficLightMonitor
import threading

class TrafficLightGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Hệ Thống Phát Hiện Đèn Giao Thông")
            
            # Khởi tạo TrafficLightMonitor
            self.monitor = TrafficLightMonitor()
            self.is_running = False
            
            self.setup_gui()
        except Exception as e:
            messagebox.showerror("Lỗi Khởi Tạo", str(e))
            raise
        
    def setup_gui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame video
        self.video_frame = ttk.LabelFrame(main_frame, text="Camera", padding="5")
        self.video_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Label hiển thị video
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.grid(row=0, column=0)
        
        # Frame điều khiển
        control_frame = ttk.LabelFrame(main_frame, text="Điều Khiển", padding="5")
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Nút Start/Stop
        self.start_button = ttk.Button(control_frame, text="Bắt Đầu", command=self.toggle_detection)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Thanh trượt điều chỉnh độ nhạy
        ttk.Label(control_frame, text="Độ nhạy:").grid(row=0, column=1, padx=5, pady=5)
        self.sensitivity_scale = ttk.Scale(control_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL,
                                        length=200, value=1.0)
        self.sensitivity_scale.grid(row=0, column=2, padx=5, pady=5)
        
        # Frame thông tin
        info_frame = ttk.LabelFrame(main_frame, text="Thông Tin", padding="5")
        info_frame.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Label hiển thị trạng thái
        self.status_label = ttk.Label(info_frame, text="Trạng thái: Chưa phát hiện")
        self.status_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Nút chọn nguồn video
        ttk.Button(control_frame, text="Chọn Camera", 
                  command=lambda: self.select_camera(0)).grid(row=0, column=3, padx=5, pady=5)
        
        # Cấu hình grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
    def select_camera(self, source):
        try:
            self.monitor.setup_camera(source)
            messagebox.showinfo("Thành công", "Đã kết nối với camera!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể kết nối camera: {str(e)}")
    
    def toggle_detection(self):
        if not self.is_running:
            if not self.monitor.camera:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn camera trước!")
                return
                
            self.is_running = True
            self.start_button.configure(text="Dừng")
            self.detection_thread = threading.Thread(target=self.update_frame)
            self.detection_thread.daemon = True
            self.detection_thread.start()
        else:
            self.is_running = False
            self.start_button.configure(text="Bắt Đầu")
    
    def update_frame(self):
        while self.is_running:
            if not self.monitor.camera:
                break
                
            ret, frame = self.monitor.camera.read()
            if not ret:
                break
            
            # Cập nhật độ nhạy từ thanh trượt
            self.monitor.sensitivity = self.sensitivity_scale.get()
            
            # Xử lý frame
            processed_frame, status = self.monitor.detect_traffic_light(frame)
            
            # Chuyển đổi frame để hiển thị trong tkinter
            img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            
            # Điều chỉnh kích thước để vừa với cửa sổ
            width = min(800, img.width)
            height = int((width/img.width) * img.height)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
            # Cập nhật trạng thái
            self.status_label.configure(text=f"Trạng thái: {status}")
            
            # Cập nhật GUI
            self.root.update_idletasks()
        
        if self.monitor.camera:
            self.monitor.camera.release()

def main():
    root = tk.Tk()
    app = TrafficLightGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()