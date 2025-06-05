#!/usr/bin/env python3
"""
Debug configuration loading to identify why camera is still accessing hardware
"""

from config.config import load_config, SystemMode

# Test configuration loading
print("=== Configuration Debug Test ===")

config = load_config()
print(f"Mode: {config.mode}")
print(f"Camera ID: {config.camera.camera_id}")
print(f"AI Model Path: {config.ai_model.model_path}")

# Test explicit simulation mode
config_sim = load_config(mode=SystemMode.SIMULATION)
print(f"\nExplicit Simulation Mode:")
print(f"Mode: {config_sim.mode}")
print(f"Camera ID: {config_sim.camera.camera_id}")
print(f"AI Model Path: {config_sim.ai_model.model_path}")

# Test camera manager with debug config
from src.camera_system.camera_manager import CameraManager

print(f"\n=== Camera Manager Test ===")
camera_manager = CameraManager(config_sim)
print(f"Camera Manager Config Camera ID: {camera_manager.config.camera.camera_id}")
print(f"Camera Status Camera ID: {camera_manager.camera_status.camera_id}")

# Test initialization
print(f"\n=== Camera Initialization Test ===")
result = camera_manager.initialize_camera()
print(f"Initialization result: {result}")
print(f"Camera object type: {type(camera_manager.camera)}")
