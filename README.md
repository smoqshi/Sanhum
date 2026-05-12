# 🤖 Sanhum Robot Control System

All-in-one Python robot control system with WebSocket communication, gamepad support, and real-time control capabilities.

## 🚀 Quick Start

### On Raspberry Pi (Server)
```bash
# Install dependencies
sudo apt update
sudo apt install python3-websockets

# Run the robot server
python3 sanhum_robot.py --mode server
```

### On Windows (Client)
```bash
# Install dependencies
pip install websockets

# Optional: For gamepad support
pip install inputs

# Run the control client
python3 sanhum_robot.py --mode client
```

## 🌐 Access

- **WebSocket Server**: `ws://192.168.0.140:8081`
- **Web Interface**: `http://192.168.0.140:8080` (if enabled)
- **Direct Control**: `python3 sanhum_robot.py --mode client`

## ✨ Features

### 🎮 Control Methods
- **Gamepad Support**: Full gamepad control with auto-calibration
- **Keyboard Control**: Terminal-based keyboard commands
- **GUI Interface**: Windows GUI with sliders and telemetry (optional)
- **Web Interface**: Browser-based control panel

### 📡 Communication
- **WebSocket**: Real-time, low-latency communication
- **No HTTP**: Eliminated all HTTP requests for better performance
- **20Hz Control Rate**: Smooth, responsive robot control
- **Telemetry**: Real-time speed and battery monitoring

### 🛠️ Cross-Platform
- **Windows**: Full GUI and gamepad support
- **Raspberry Pi**: Lightweight terminal mode
- **Python 3.14+**: Compatible with latest Python versions
- **Multiple Gamepad Libraries**: pygame, inputs, pyjoystick support

### 🔧 Robot Control
- **Motor Control**: Linear and angular velocity control
- **Arm Control**: Extension, gripper, and turret control
- **Emergency Stop**: One-click emergency shutdown
- **Calibration**: Automatic gamepad calibration

## 📋 Requirements

### Minimum Requirements
- Python 3.7+
- websockets library

### Optional Requirements
- **Gamepad Support**: `pip install inputs` (recommended for Python 3.14+)
- **GUI Support**: `pip install matplotlib numpy` (Windows only)
- **Alternative Gamepad**: `pip install pygame` or `pip install pyjoystick`

## 🏗️ Project Structure

```
sanhum/
├── sanhum_robot.py          # Main all-in-one application
├── src/
│   ├── motor_control.py     # Hardware motor control
│   ├── websocket_server.py   # WebSocket server
│   ├── armkinematics.cpp/h   # Arm kinematics calculations
│   ├── motordriver.cpp/h     # Motor driver interface
│   ├── robotmodel.cpp/h      # Robot state management
│   └── httpserver.cpp/h      # Legacy HTTP server
├── www/                      # Web interface files
│   ├── index.html           # Main web interface
│   └── js/                  # JavaScript files
└── README.md                 # This file
```

## 🎮 Gamepad Setup

### For Python 3.14+ (Recommended)
```bash
pip install inputs
```

### For Older Python Versions
```bash
pip install pygame
```

### Gamepad Controls
- **Left Stick**: Movement (forward/backward/turn)
- **Right Stick**: Arm control (extend/gripper/turret)
- **A Button**: Emergency stop
- **Select Button**: Recalibrate gamepad

## ⌨️ Keyboard Controls

### Movement
- `w/s` - Forward/Backward
- `a/d` - Turn Left/Right
- `space` - Stop

### Arm Control
- `q/e` - Extend/Retract Arm
- `r/f` - Open/Close Gripper
- `t/g` - Rotate Turret Left/Right

### System
- `x` - Emergency Stop
- `g` - Initialize Gamepad
- `c` - Connect/Disconnect
- `Ctrl+C` - Exit

## 🔧 Configuration

### Network Settings
```bash
# Custom IP and port
python3 sanhum_robot.py --mode client --ip 192.168.0.140 --port 8081
```

### Motor Settings
- Edit `src/motor_control.py` for motor parameters
- Wheel radius: 40mm
- Max speed: 333 rpm

## 🐛 Troubleshooting

### Gamepad Issues
- **Python 3.14**: Use `pip install inputs` instead of pygame
- **No gamepad found**: Check gamepad connection and drivers
- **Calibration**: Press 'g' to recalibrate gamepad

### Connection Issues
- **Cannot connect**: Check RPi IP address and firewall
- **WebSocket errors**: Ensure server is running on RPi
- **Network timeout**: Verify network connectivity

### Python Issues
- **Module not found**: Install required packages with pip
- **Permission errors**: May need admin rights for gamepad access
- **Python version**: Use Python 3.7+ for best compatibility

## 🔄 Migration from Old System

The old Qt-based system has been replaced with a modern Python WebSocket system:

1. **No more Qt compilation required**
2. **WebSocket instead of HTTP for better performance**
3. **All-in-one Python application**
4. **Cross-platform compatibility**
5. **Enhanced gamepad support**

## 📊 Performance

- **Latency**: <50ms WebSocket communication
- **Update Rate**: 20Hz control loop
- **CPU Usage**: Minimal on RPi
- **Memory**: Lightweight Python application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both server and client modes
5. Submit a pull request

## 📄 License

MIT License

---

**🤖 Happy Robot Controlling!**