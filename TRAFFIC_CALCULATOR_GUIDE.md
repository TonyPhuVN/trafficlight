# 🚦 Traffic Light Timing Calculator Guide

## Overview
The Traffic Light Timing Calculator is a user-friendly tool that calculates optimal green and red light times based on vehicle counts you enter. It uses the same AI optimization engine as the main traffic system but provides a simple interface for manual calculations.

## How to Use

### 🚀 Quick Demo (Recommended First Step)
```bash
python demo_calculator.py
```
This shows 6 different traffic scenarios with automatic calculations. Perfect for understanding how the system works!

### 🎮 Interactive Calculator
```bash
python traffic_light_calculator.py
```
Choose option 1 for interactive mode where you enter your own vehicle counts.

## What You Can Input

### Vehicle Counts
- **North direction**: Number of vehicles waiting to go north
- **South direction**: Number of vehicles waiting to go south  
- **East direction**: Number of vehicles waiting to go east
- **West direction**: Number of vehicles waiting to go west

### Additional Factors
- **Emergency vehicles**: Yes/No (gets priority timing)
- **Weather conditions**: normal, rain, fog, snow (affects timing for safety)

## Example Calculations

### Scenario 1: Morning Rush Hour
**Input:**
- North: 18 vehicles, South: 12 vehicles
- East: 6 vehicles, West: 4 vehicles
- Emergency: No, Weather: Normal

**Output:**
- **North-South**: 🟢 90s green, 🟡 3s yellow, 🔴 39s red
- **East-West**: 🟢 36s green, 🟡 3s yellow, 🔴 93s red
- **Total cycle**: 132 seconds
- **Efficiency**: 100%

*Logic: Heavy north-south traffic (75%) gets more green time*

### Scenario 2: Light Night Traffic  
**Input:**
- North: 2 vehicles, South: 1 vehicle
- East: 3 vehicles, West: 1 vehicle
- Emergency: No, Weather: Normal

**Output:**
- **North-South**: 🟢 26s green, 🟡 3s yellow, 🔴 32s red
- **East-West**: 🟢 29s green, 🟡 3s yellow, 🔴 29s red
- **Total cycle**: 61 seconds
- **Efficiency**: 95%+

*Logic: Minimal traffic gets shorter, balanced timing*

### Scenario 3: Emergency Vehicle Priority
**Input:**
- North: 8 vehicles, South: 6 vehicles
- East: 7 vehicles, West: 5 vehicles
- Emergency: Yes, Weather: Normal

**Output:**
- **North-South**: 🟢 64s green, 🟡 3s yellow, 🔴 48s red
- **East-West**: 🟢 45s green, 🟡 3s yellow, 🔴 67s red
- **Total cycle**: 115 seconds
- **Efficiency**: 95%+

*Logic: Emergency priority extends green time for priority direction*

## Key Features

### ✅ Smart Optimization
- **Vehicle-based timing**: 90% based on actual vehicle counts, 10% on time patterns
- **Proportional allocation**: More vehicles = more green time
- **Minimum safety**: Always at least 15 seconds green
- **Maximum wait**: Never more than 90 seconds green

### ✅ Safety Features
- **Emergency priority**: Automatic priority routing
- **Weather adjustment**: Extended timing in rain/snow for safety
- **Standard yellow**: Always 3 seconds yellow light
- **Balanced minimum**: Fair timing even for light traffic

### ✅ Efficiency Optimization  
- **95%+ efficiency**: Smart algorithms ensure high performance
- **Minimal wait times**: Optimized cycle times
- **Traffic matching**: Timing allocation matches traffic distribution
- **Real-time calculation**: Instant results

## Understanding the Output

### Timing Display
```
┌─ North-South Direction ─┐
│ 🟢 Green Light: 45 seconds │
│ 🟡 Yellow Light: 3 seconds │  
│ 🔴 Red Light:   48 seconds │
└─────────────────────────┘
```

### Analysis Metrics
- **Total cycle time**: Complete red-green-yellow cycle
- **Efficiency score**: How well timing serves traffic (target: 95%+)
- **Confidence level**: Reliability of calculation (higher with more vehicles)
- **Traffic distribution**: Percentage of vehicles in each direction
- **Time allocation**: Percentage of green time given to each direction

### Reasoning Logic
Shows why the system made timing decisions:
- Vehicle counts and ratios
- Emergency vehicle considerations
- Weather adjustments applied
- Time-of-day pattern influences

## File Output Options

### Save Results
The interactive calculator can save results to JSON files:
```json
{
  "timestamp": "2025-01-06T08:30:00",
  "input": {
    "vehicle_counts": {"North": 10, "South": 8, "East": 6, "West": 4},
    "emergency_vehicles": 0,
    "weather_condition": "normal"
  },
  "results": {
    "north_south": {
      "green_duration": 45,
      "yellow_duration": 3,
      "red_duration": 36
    },
    "east_west": {
      "green_duration": 33,
      "yellow_duration": 3,
      "red_duration": 48
    }
  }
}
```

## Tips for Best Results

### 💡 Accurate Vehicle Counting
- Count vehicles actually waiting at the intersection
- Include all vehicle types (cars, trucks, motorcycles)
- Don't count vehicles that just passed through

### 💡 Consider Context
- Use emergency option for ambulance/fire truck situations
- Select appropriate weather conditions
- Consider time of day (system automatically adjusts)

### 💡 Interpreting Results
- Higher vehicle counts = longer green times
- Emergency vehicles get priority
- Rain/snow extends timing for safety
- Balanced traffic gets balanced timing

## Integration with Main System

This calculator uses the same `TrafficLightOptimizer` engine as the full Smart Traffic AI System, so results are consistent with:
- `enhanced_web_app.py` - Full web dashboard
- `minimal_run.py` - Basic system demo
- Main traffic control system

## Troubleshooting

### Common Issues
- **Import errors**: Make sure you're in the project root directory
- **Invalid input**: Enter numbers only for vehicle counts
- **File save errors**: Check write permissions in current directory

### Getting Help
- Run the demo first: `python demo_calculator.py`
- Check example scenarios for reference
- Verify input format (integers for vehicle counts)

## Next Steps

After using the calculator:
1. **Try the web dashboard**: `python enhanced_web_app.py`
2. **Run full simulation**: `python minimal_run.py`
3. **Explore the AI system**: Check other demo files

The calculator is perfect for:
- 📚 **Learning** how traffic light timing works
- 🧪 **Testing** different traffic scenarios
- 📊 **Planning** traffic management strategies
- 🎯 **Understanding** AI optimization decisions

Happy calculating! 🚦✨
