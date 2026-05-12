# 🤖 Sanhum Robot Control System

A Qt-based robot control system for Raspberry Pi with web interface and motor control.

## Quick Start

### Automated Setup (Recommended)
```bash
python3 setup_and_run.py
```

### Manual Setup
```bash
# Install dependencies
sudo apt install qt5-qmake qtbase5-dev build-essential python3 libgpiod2 libgpiod-dev

# Build
mkdir build && cd build
qmake ../Sanhum.pro
make

# Run
./Sanhum
```

## Access

Web interface: `http://<rpi-ip>:8080`

## Features

- Real-time robot control (50Hz update loop)
- Web-based interface for remote control
- Python GPIO motor driver integration
- Arm kinematics calculations
- HTTP API for external integrations
- Hotspot support for direct device connection

## Requirements

- Raspberry Pi 4+ (recommended)
- Raspberry Pi OS
- Qt5, Python 3.7+, libgpiod

## Project Structure

```
sanhum/
├── src/                    # C++ source code
│   ├── main.cpp           # Application entry
│   ├── httpserver.cpp     # Web server
│   ├── robotmodel.cpp     # Robot state
│   ├── motordriver.cpp    # Motor control
│   ├── armkinematics.cpp  # Kinematics
│   └── motor_control.py   # Python GPIO driver
├── www/                   # Web interface
├── setup_and_run.py       # Automated setup
└── Sanhum.pro            # Qt project file
```

## Configuration

- Motor settings: `src/motor_control.py`
- Web interface: `www/` directory
- Network settings: `src/httpserver.cpp`

## Troubleshooting

**Build fails**: Clean build directory and rebuild
**GPIO errors**: Add user to gpio group or run with sudo
**Network issues**: Check `ip addr show` and test with curl

## License

MIT License