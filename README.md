# 🚦 Hệ Thống AI Điều Khiển Đèn Giao Thông Thông Minh

## 📋 Mô tả dự án
Hệ thống AI tích hợp camera và cảm biến để phân tích lưu lượng giao thông theo thời gian thực và tự động điều chỉnh thời gian đèn giao thông để tối ưu hóa luồng xe cộ.

## 🎯 Tính năng chính

### 🤖 AI & Machine Learning
- **Phát hiện xe cộ**: Sử dụng YOLO/OpenCV để đếm và phân loại phương tiện
- **Dự đoán lưu lượng**: Mô hình AI dự báo mật độ giao thông
- **Học từ dữ liệu**: Cải thiện hiệu suất dựa trên lịch sử giao thông
- **Nhận diện biển số**: Theo dõi tốc độ và vi phạm giao thông

### 📹 Camera & Cảm biến
- **Camera đa góc**: Theo dõi tất cả làn đường
- **Cảm biến áp suất**: Đếm xe qua điểm đo
- **Cảm biến thời tiết**: Điều chỉnh theo điều kiện thời tiết
- **IoT Integration**: Kết nối với hệ thống giao thông đô thị

### 🚦 Điều khiển thông minh
- **Thời gian động**: Tự động điều chỉnh chu kỳ đèn
- **Ưu tiên xe cứu thương**: Phát hiện và ưu tiên xe ưu tiên
- **Tối ưu hóa luồng**: Giảm thiểu thời gian chờ và ùn tắc
- **Điều khiển từ xa**: Quản lý tập trung qua web interface

## 🏗️ Kiến trúc hệ thống

```
📁 smart_traffic_ai_system/
├── 📁 src/                          # Mã nguồn chính
│   ├── 🤖 ai_engine/               # Module AI
│   ├── 📹 camera_system/           # Xử lý camera
│   ├── 🚦 traffic_controller/      # Điều khiển đèn
│   ├── 📊 data_processor/          # Xử lý dữ liệu
│   └── 🌐 web_interface/           # Giao diện web
├── 📁 models/                       # Mô hình AI đã train
├── 📁 data/                        # Dữ liệu training và logs
├── 📁 config/                      # File cấu hình
├── 📁 tests/                       # Test cases
└── 📁 docs/                        # Tài liệu
```

## 🚀 Khởi chạy nhanh

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình hệ thống
```bash
python config/setup.py
```

### 3. Chạy hệ thống
```bash
# Chế độ mô phỏng (không cần camera thật)
python run.py --simulation

# Chế độ thực tế (cần camera và cảm biến)
python run.py --production

# Giao diện web
python run.py --web-interface
```

## 🛠️ Yêu cầu hệ thống

### Phần cứng
- **Camera**: USB/IP Camera (tối thiểu 1080p)
- **Cảm biến**: Arduino/Raspberry Pi với sensors
- **Máy tính**: CPU 4+ cores, RAM 8GB+, GPU khuyến nghị
- **Kết nối**: Internet cho cập nhật và đồng bộ

### Phần mềm
- Python 3.8+
- OpenCV 4.0+
- TensorFlow/PyTorch
- FastAPI cho web interface
- SQLite/PostgreSQL cho database

## 📊 Modules chính

### 🤖 AI Engine (`ai_engine/`)
- `vehicle_detector.py` - Phát hiện và đếm xe
- `traffic_predictor.py` - Dự đoán lưu lượng
- `optimization_engine.py` - Tối ưu hóa thời gian đèn
- `learning_system.py` - Học và cải thiện

### 📹 Camera System (`camera_system/`)
- `camera_manager.py` - Quản lý camera
- `image_processor.py` - Xử lý hình ảnh
- `motion_detector.py` - Phát hiện chuyển động
- `calibration.py` - Hiệu chỉnh camera

### 🚦 Traffic Controller (`traffic_controller/`)
- `light_controller.py` - Điều khiển đèn giao thông
- `timing_optimizer.py` - Tối ưu thời gian
- `emergency_handler.py` - Xử lý tình huống khẩn cấp
- `scheduler.py` - Lập lịch tự động

### 📊 Data Processor (`data_processor/`)
- `data_collector.py` - Thu thập dữ liệu
- `analytics.py` - Phân tích thống kê
- `database_manager.py` - Quản lý database
- `report_generator.py` - Tạo báo cáo

### 🌐 Web Interface (`web_interface/`)
- `dashboard.py` - Dashboard chính
- `api_endpoints.py` - REST API
- `real_time_monitor.py` - Theo dõi thời gian thực
- `config_panel.py` - Panel cấu hình

## 📈 Tính năng nâng cao

### 🧠 Machine Learning
- **Deep Learning**: CNN cho object detection
- **Time Series**: LSTM cho dự đoán lưu lượng
- **Reinforcement Learning**: Tối ưu hóa policy
- **Computer Vision**: Phân tích hành vi giao thông

### 🌍 IoT Integration
- **MQTT Protocol**: Giao tiếp với sensors
- **Cloud Sync**: Đồng bộ dữ liệu cloud
- **Edge Computing**: Xử lý local real-time
- **5G Ready**: Hỗ trợ kết nối 5G

### 📱 Mobile App
- **Traffic Monitor**: Ứng dụng giám sát
- **Admin Panel**: Quản lý từ xa
- **Citizen Reports**: Báo cáo từ người dân
- **Real-time Alerts**: Cảnh báo thời gian thực

## 🔧 Cấu hình và tùy chỉnh

### Camera Settings
```python
CAMERA_CONFIG = {
    'resolution': (1920, 1080),
    'fps': 30,
    'detection_zones': [...],
    'sensitivity': 0.8
}
```

### AI Model Settings
```python
AI_CONFIG = {
    'model_type': 'YOLOv8',
    'confidence_threshold': 0.7,
    'nms_threshold': 0.45,
    'classes': ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
}
```

### Traffic Light Settings
```python
TRAFFIC_CONFIG = {
    'min_green_time': 15,  # seconds
    'max_green_time': 120, # seconds
    'yellow_time': 3,      # seconds
    'red_clearance': 2     # seconds
}
```

## 📊 Monitoring & Analytics

### Real-time Dashboard
- Lưu lượng xe theo thời gian thực
- Hiệu suất hệ thống
- Thống kê vi phạm
- Báo cáo sự cố

### Historical Analysis
- Xu hướng giao thông theo giờ/ngày/tháng
- Hiệu quả cải thiện
- So sánh với hệ thống cũ
- Dự đoán tương lai

## 🛡️ Bảo mật và Quyền riêng tư

### Data Security
- Mã hóa dữ liệu camera
- Xóa dữ liệu cá nhân tự động
- Tuân thủ GDPR
- Audit logs đầy đủ

### System Security
- Authentication & Authorization
- API Security với JWT
- Network Security
- Regular Security Updates

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch
3. Implement tính năng
4. Viết tests
5. Submit pull request

## 📄 License

MIT License - Chi tiết trong file `LICENSE`

## 👥 Team

- **AI Engineer**: Phát triển mô hình ML/DL
- **Backend Developer**: API và database
- **IoT Engineer**: Tích hợp sensors và hardware
- **Frontend Developer**: Web/mobile interface
- **DevOps Engineer**: Deployment và monitoring

---

🚀 **Hệ thống giao thông thông minh cho thành phố tương lai!**
