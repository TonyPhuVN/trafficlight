# Sử dụng Python 3.8 làm base image
FROM python:3.8-slim

# Cài đặt các gói phụ thuộc cho OpenCV và GUI
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép requirements.txt
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt thư viện cho GUI
RUN pip install --no-cache-dir python-tk

# Sao chép mã nguồn
COPY src/ ./src/

# Thiết lập biến môi trường cho display
ENV DISPLAY=:0

# Command để chạy ứng dụng
CMD ["python", "src/gui.py"]