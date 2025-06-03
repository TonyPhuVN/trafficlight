# System Patterns - Smart Traffic AI System

## Architecture Overview

### High-Level System Design
The Smart Traffic AI System follows a **modular, event-driven architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                        │
│                     (run.py)                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ AI Engine   │ │ Camera      │ │ Traffic     │
│ Module      │ │ System      │ │ Controller  │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
              ┌─────────────┐
              │ Database &  │
              │ Analytics   │
              └─────────────┘
                      │
                      ▼
              ┌─────────────┐
              │ Web         │
              │ Interface   │
              └─────────────┘
```

## Core Architectural Patterns

### 1. Main Orchestrator Pattern
**File**: `run.py` - `SmartTrafficSystem` class

**Purpose**: Central coordination hub that manages all system components and orchestrates the traffic management workflow.

**Key Responsibilities**:
- Component initialization and lifecycle management
- Multi-threaded processing coordination
- System monitoring and performance tracking
- Graceful shutdown handling

**Threading Model**:
- **Main Processing Loop**: Coordinates AI analysis and traffic control
- **Performance Monitor**: Tracks system metrics and logs statistics
- **Web Interface**: Runs the dashboard server
- **Component Threads**: Each major component runs in its own thread

### 2. Component-Based Architecture
Each major functionality is encapsulated in dedicated modules:

#### AI Engine (`src/ai_engine/`)
- **Vehicle Detector**: YOLO-based object detection and vehicle counting
- **Traffic Predictor**: ML models for traffic flow forecasting
- **Pattern Recognition**: Identifies traffic trends and anomalies

#### Camera System (`src/camera_system/`)
- **Camera Manager**: Coordinates multiple camera feeds
- **Image Processing**: Real-time frame analysis and preprocessing
- **Motion Detection**: Optimizes processing by focusing on active areas

#### Traffic Controller (`src/traffic_controller/`)
- **Light Controller**: Manages traffic light state changes
- **Timing Optimizer**: Calculates optimal light timing based on AI input
- **Emergency Handler**: Manages priority vehicles and emergency situations

#### Database Layer (`src/database/`)
- **Database Manager**: Handles all data persistence operations
- **Analytics Engine**: Processes historical data for insights

### 3. Data Flow Pattern

```
Camera Feeds → AI Analysis → Traffic Prediction → Light Control → Database Logging
      ↓              ↓              ↓              ↓              ↓
  Frame Capture   Vehicle Count   Flow Forecast   Timing Adjust   Performance Log
      ↓              ↓              ↓              ↓              ↓
  Motion Detect   Classification   Optimization    State Change    Analytics
```

**Processing Cycle** (per intersection):
1. **Capture**: Get latest frames from all cameras
2. **Detect**: AI vehicle detection and counting
3. **Predict**: Generate traffic flow predictions
4. **Optimize**: Calculate optimal traffic light timing
5. **Control**: Apply timing changes to traffic lights
6. **Log**: Record all data for analytics

### 4. Configuration-Driven Design
The system uses centralized configuration management:

**Configuration Hierarchy**:
- System-level settings (mode, intervals, thresholds)
- AI model parameters (confidence, detection classes)
- Camera configurations (resolution, detection zones)
- Traffic light settings (timing constraints, safety rules)
- Database and logging preferences

### 5. Error Handling and Resilience Patterns

#### Graceful Degradation
- **Camera Failure**: System continues with remaining cameras
- **AI Model Error**: Falls back to sensor data or default timing
- **Network Issues**: Local processing continues, sync when restored
- **Component Crash**: Automatic restart and error logging

#### Circuit Breaker Pattern
- Monitor component health and performance
- Temporarily disable failing components
- Automatic recovery when components are healthy

#### Monitoring and Alerting
- Continuous health checks for all components
- Performance metric tracking
- Database logging of all system events
- Real-time alerting through web interface

## Key Design Decisions

### 1. Multi-Threading Architecture
**Decision**: Use threading for concurrent processing
**Rationale**: 
- Real-time processing requirements
- Independent component operation
- Scalability for multiple intersections
- Non-blocking user interface

### 2. Database-Centric Logging
**Decision**: Comprehensive database logging of all system activities
**Rationale**:
- Historical analysis and reporting
- Performance monitoring and optimization
- Audit trail for system actions
- Data-driven decision making

### 3. Modular Component Design
**Decision**: Separate components with clear interfaces
**Rationale**:
- Independent development and testing
- Easy component replacement or upgrade
- Clear separation of concerns
- Maintainable codebase

### 4. Configuration-First Approach
**Decision**: Externalize all configurable parameters
**Rationale**:
- Easy deployment to different environments
- Runtime parameter adjustment
- A/B testing and optimization
- No code changes for configuration updates

## Integration Patterns

### 1. Camera Integration
- **USB/IP Camera Support**: Standard camera protocols
- **Multi-Camera Coordination**: Synchronized frame capture
- **Dynamic Camera Management**: Hot-plug support for cameras

### 2. IoT Sensor Integration
- **MQTT Protocol**: Standard IoT communication
- **Sensor Data Fusion**: Combine camera and sensor data
- **Real-Time Processing**: Low-latency sensor data integration

### 3. Web Interface Integration
- **Real-Time Updates**: WebSocket communication for live data
- **REST API**: Standard API for system control and data access
- **Responsive Design**: Works on desktop and mobile devices

## Performance Optimization Patterns

### 1. Processing Optimization
- **Frame Skipping**: Process every Nth frame to reduce load
- **Region of Interest**: Focus processing on traffic areas
- **Model Caching**: Cache AI model inference results
- **Parallel Processing**: Concurrent intersection processing

### 2. Database Optimization
- **Batch Inserts**: Group database operations for efficiency
- **Index Strategy**: Optimize queries for real-time dashboard
- **Data Archiving**: Move old data to archive tables
- **Connection Pooling**: Reuse database connections

### 3. Memory Management
- **Frame Buffer Management**: Limited frame retention in memory
- **Model Loading**: Load AI models once at startup
- **Resource Cleanup**: Proper cleanup of camera and sensor resources

## Security Patterns

### 1. Data Privacy
- **Camera Data**: No permanent storage of camera feeds
- **Personal Information**: Automatic deletion of identifiable data
- **Access Control**: Role-based access to system functions

### 2. System Security
- **API Authentication**: Secure access to control functions
- **Network Security**: Encrypted communication where applicable
- **Input Validation**: Sanitize all external inputs

## Scalability Patterns

### 1. Horizontal Scaling
- **Multiple Intersections**: Each intersection processed independently
- **Load Distribution**: Distribute processing across available resources
- **Component Scaling**: Add more camera or sensor instances as needed

### 2. Vertical Scaling
- **Resource Optimization**: Efficient use of CPU, memory, and storage
- **Performance Tuning**: Configurable processing intervals and thresholds
- **Hardware Optimization**: Support for GPU acceleration where available

This system architecture provides a robust, scalable foundation for intelligent traffic management while maintaining flexibility for future enhancements and integrations.
