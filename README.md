# Hệ Thống Phát Hiện Đèn Giao Thông Sử Dụng AI

Chương trình này sử dụng xử lý ảnh và thị giác máy tính để phát hiện và phân loại trạng thái đèn giao thông từ camera hoặc video.

## Yêu Cầu Hệ Thống

1. Python 3.8 trở lên
2. Webcam (nếu muốn sử dụng camera trực tiếp)
3. Các thư viện Python:
   - OpenCV (cv2)
   - NumPy

## Hướng Dẫn Cài Đặt

1. Cài đặt Python từ [python.org](https://www.python.org/downloads/)
   - Trong quá trình cài đặt, nhớ đánh dấu vào ô "Add Python to PATH"

2. Mở Terminal/Command Prompt và cài đặt các thư viện cần thiết:
   ```
   python -m pip install opencv-python numpy
   ```

## Cách Sử Dụng

1. Mở terminal trong thư mục dự án
2. Chạy chương trình bằng lệnh:
   ```
   python src/traffic_monitor.py
   ```

3. Điều khiển chương trình:
   - Nhấn 'q' để thoát khỏi chương trình
   - Chương trình sẽ hiển thị trạng thái đèn (ĐỎ, VÀNG, XANH) trên màn hình

## Các Tính Năng

- Phát hiện đèn giao thông trong thời gian thực
- Nhận diện màu đèn (đỏ, vàng, xanh)
- Hiển thị trạng thái hiện tại của đèn
- Vẽ khung xung quanh đèn được phát hiện

## Triển Khai Bằng Docker

### Yêu Cầu
- Docker
- Docker Compose
- Hệ điều hành có X Server (Linux) hoặc VcXsrv (Windows)

### Cài Đặt Trên Windows
1. Cài đặt VcXsrv Windows X Server:
   - Tải VcXsrv từ: https://sourceforge.net/projects/vcxsrv/
   - Cài đặt và chạy XLaunch
   - Chọn "Multiple windows" trong cấu hình
   - Chọn "Start no client"
   - Chọn "Disable access control"
   - Lưu cấu hình

2. Build và chạy container:
   ```bash
   docker-compose build
   docker-compose up
   ```

### Cài Đặt Trên Linux
1. Cấp quyền cho X Server:
   ```bash
   xhost +local:docker
   ```

2. Build và chạy container:
   ```bash
   docker-compose build
   docker-compose up
   ```

### Xử Lý Sự Cố Docker

1. Nếu gặp lỗi về quyền truy cập camera:
   - Đảm bảo camera được kết nối
   - Kiểm tra quyền truy cập thiết bị trong docker-compose.yml

2. Nếu gặp lỗi về display:
   - Windows: Đảm bảo VcXsrv đang chạy
   - Linux: Chạy lệnh `xhost +local:docker`

3. Nếu container không thể truy cập GUI:
   - Kiểm tra biến môi trường DISPLAY
   - Đảm bảo X Server đang chạy và được cấu hình đúng

## Xử Lý Sự Cố

1. Nếu gặp lỗi "No module named 'cv2'":
   - Chạy lại lệnh: `python -m pip install opencv-python`

2. Nếu camera không hoạt động:
   - Kiểm tra quyền truy cập camera
   - Thử đổi số camera trong dòng `monitor.setup_camera(0)` thành 1 hoặc 2

## Ghi Chú

- Chương trình sử dụng không gian màu HSV để phát hiện màu chính xác hơn
- Độ nhạy có thể điều chỉnh bằng cách thay đổi các giá trị ngưỡng trong mã nguồn