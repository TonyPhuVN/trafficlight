# 📦 Installation Guide - Smart Traffic AI System

## Quick Fix for sqlite3 Error

The error `Could not find a version that satisfies the requirement sqlite3` occurs because `sqlite3` is part of Python's standard library and doesn't need to be installed via pip.

### ✅ Solution

Use one of these approaches:

### Option 1: Minimal Installation (Recommended)
```bash
# Use the minimal requirements file (sqlite3 issue fixed)
pip install -r requirements-minimal.txt
```

### Option 2: Automated Setup
```bash
# Run the automated setup script
python setup.py
```

### Option 3: Manual Installation
```bash
# Install core dependencies only
pip install numpy opencv-python flask flask-socketio sqlalchemy paho-mqtt loguru
```

## 🔧 Complete Installation Steps

### 1. Clone and Setup
```bash
git clone <your-repo>
cd smart-traffic-ai
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
# Option A: Minimal (fastest)
pip install -r requirements-minimal.txt

# Option B: Full features
pip install -r requirements.txt

# Option C: Automated setup
python setup.py
```

### 4. Run the System
```bash
# Quick demo
python demo.py

# Full system
python run.py
```

## 🐳 Docker Installation

### Quick Start
```bash
# Build and run with minimal dependencies
docker-compose -f docker-compose.yaml up --build
```

### Access the System
- Web Dashboard: http://localhost:5000
- Health Check: http://localhost:5000/health

## 📋 Dependencies Explained

### Core Dependencies (Always Required)
- `sqlite3` - ✅ Built into Python (no installation needed)
- `numpy` - Numerical computing
- `opencv-python` - Computer vision
- `flask` - Web framework
- `sqlalchemy` - Database ORM

### Optional Dependencies
- `torch` - AI/ML models (large download)
- `ultralytics` - YOLO object detection
- `matplotlib` - Plotting and visualization

## 🚨 Troubleshooting

### Common Issues

1. **sqlite3 error**: Use `requirements-minimal.txt` instead
2. **OpenCV issues**: Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libgl1-mesa-glx libglib2.0-0
   
   # MacOS
   brew install opencv
   ```
3. **Large downloads**: Use minimal installation first, add features later

### System Requirements
- Python 3.8+
- 2GB RAM minimum
- 1GB disk space

### Platform-Specific Notes

#### Raspberry Pi
```bash
# Use minimal installation
pip install -r requirements-minimal.txt
# Add hardware-specific packages as needed
```

#### Windows
```bash
# May need Visual C++ Build Tools for some packages
pip install -r requirements-minimal.txt
```

#### macOS
```bash
# Works out of the box with minimal requirements
pip install -r requirements-minimal.txt
```

## 🔍 Verification

Test your installation:
```bash
python -c "import sqlite3, numpy, cv2, flask; print('✅ Core dependencies working')"
```

## 📖 Next Steps

1. ✅ Install dependencies
2. 🔧 Run `python setup.py` for guided setup
3. 🎮 Run `python demo.py` for a quick test
4. 🚦 Run `python run.py` for the full system
5. 🌐 Open http://localhost:5000 in your browser

## 💡 Tips

- Start with minimal installation
- Add features incrementally
- Use Docker for production deployment
- Check logs in the `logs/` directory

For more help, check the documentation in the `docs/` folder.
