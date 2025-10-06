# USB Display System Monitor

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
[![GitHub Stars](https://img.shields.io/github/stars/FRAOTIAC/WeActStudio.SystemMonitor?style=social)](https://github.com/FRAOTIAC/WeActStudio.SystemMonitor)

**Personal fork with Raspberry Pi ARM64 support and cross-platform improvements**

[English](#) | [中文文档](#中文文档)

</div>

---

## 📖 Overview

A **personal fork** of the excellent [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) project, enhanced with:
- **Full Raspberry Pi ARM64 support** - Tested on Raspberry Pi OS
- **Improved cross-platform compatibility** - Better Linux/macOS support
- **Headless environment optimization** - Works without X display
- **Bug fixes** - Runtime errors and dependency issues resolved

This Python application transforms small USB serial displays into real-time system monitors, photo albums, and customizable information displays.

### ✨ Key Features

- 🖥️ **Real-time System Monitoring**: CPU, GPU, RAM, Disk, Network stats
- 🌡️ **Hardware Sensors**: Temperature, humidity (on supported models)
- 🎨 **59 Built-in Themes**: Customizable layouts and styles
- 📸 **Photo Album Mode**: Slideshow from local directories
- 🌐 **Weather Integration**: OpenWeatherMap API support
- 📊 **Dynamic Widgets**: Progress bars, radial gauges, charts
- 🔧 **GUI Configuration Tool**: Easy setup without editing files
- 🐧 **Cross-Platform**: Windows, Linux (including Raspberry Pi), macOS

---

## 🖼️ Supported Hardware

This fork supports small LCD displays using USB serial communication (CDC protocol), primarily tested with:

### 3.5" Display (Revision A)
- **Resolution**: 320 × 480 RGB565
- **Connection**: USB Type-A to serial (CDC)
- **Sensors**: Temperature + Humidity sensor support
- **Use Case**: Large display, ideal for detailed monitoring

### 0.96" Display (Revision B)
- **Resolution**: 80 × 160 RGB565
- **Connection**: USB Type-A to serial (CDC)
- **Use Case**: Compact form factor for space-constrained setups

> **Note**: This project works with LCD displays that communicate via USB serial (CDC protocol). The displays typically use a standard USB Type-A connector.

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Operating System**: Windows 10+, Linux (Debian/Ubuntu/Raspberry Pi OS), macOS 10.14+
- **Hardware**: USB port for connecting the display (standard USB Type-A)

### Installation

#### 🐧 Linux / Raspberry Pi (Recommended for ARM64)

```bash
# 1. Clone the repository
git clone https://github.com/FRAOTIAC/WeActStudio.SystemMonitor.git
cd WeActStudio.SystemMonitor

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add user to dialout group (for serial port access)
sudo usermod -a -G dialout $USER
# ⚠️ Log out and back in for this to take effect

# 5. Connect your display and run
python3 main.py
```

#### 🪟 Windows

```powershell
# 1. Clone the repository
git clone https://github.com/FRAOTIAC/WeActStudio.SystemMonitor.git
cd WeActStudio.SystemMonitor

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py

# Or use the provided batch file
"System Monitor Main.bat"
```

#### 🍎 macOS

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python
brew install python@3.11

# 3. Clone and setup
git clone https://github.com/FRAOTIAC/WeActStudio.SystemMonitor.git
cd WeActStudio.SystemMonitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run
python3 main.py
```

---

## ⚙️ Configuration

### First-Time Setup

Run the configuration tool for guided setup:

```bash
python3 configure.py
```

The configuration wizard will help you:
- 🔌 Detect and select COM port
- 📺 Choose display model (3.5" or 0.96")
- 🎨 Select theme
- 💡 Set brightness level
- 🌐 Configure network interfaces
- 🌤️ Set up weather API (optional)

### Manual Configuration

Edit `config.yaml` to customize:

```yaml
config:
  COM_PORT: /dev/ttyACM0          # Auto-detect or specify port
  THEME: Digital_CPU_0.96Inch     # Theme name
  HW_SENSORS: AUTO                # PYTHON | LHM | AUTO
  ETH: 'eth0'                     # Ethernet interface
  WLO: 'wlan0'                    # WiFi interface

display:
  REVISION: B_80x160              # A_320x480 | B_80x160
  BRIGHTNESS: 10                  # 0-100 (keep ≤50 for 3.5")
  DISPLAY_REVERSE: false          # Rotate 180°
```

---

## 🎨 Themes

### Available Themes

Choose from 59 pre-built themes optimized for different display sizes:

**For 3.5" Display (320×480)**:
- `3.5inchTheme2` - Modern dark theme
- `Cyberdeck` - Retro terminal style
- `LandscapeMagicBlue` - Vibrant blue theme
- And 40+ more...

**For 0.96" Display (80×160)**:
- `Digital_CPU_0.96Inch` - CPU-focused display
- `Example_0.96Inch_1` - Balanced system info
- `Example_0.96Inch_Clock` - Large clock with stats

### Creating Custom Themes

1. Copy an existing theme from `res/themes/`
2. Edit `theme.yaml` to customize:
   - Layout and positioning
   - Colors and fonts
   - Data sources
3. Set your theme in `config.yaml`

```yaml
THEME: YourCustomTheme
```

See [Theme Documentation](res/themes/README.md) for details.

---

## 🔧 Advanced Usage

### Running as Service (Linux/systemd)

Create `/etc/systemd/system/systemmonitor.service`:

```ini
[Unit]
Description=WeAct Studio System Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/WeActStudio.SystemMonitor
ExecStart=/path/to/.venv/bin/python3 /path/to/main.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable systemmonitor.service
sudo systemctl start systemmonitor.service
```

### Simple Test Program

Test your display without full monitoring:

```bash
python3 simple-program.py
```

This displays a basic demo with clock and progress bars.

---

## 🐛 Troubleshooting

### Display Not Detected

**Linux/Raspberry Pi**:
```bash
# Check if device is connected
ls /dev/ttyACM*

# Verify user permissions
groups | grep dialout

# Check device info
dmesg | grep tty
```

**Windows**:
- Open Device Manager
- Look for "Ports (COM & LPT)"
- Note the COM port number (e.g., COM3)

### No GPU Data on Raspberry Pi

This is expected - the warning can be safely ignored:
```
[WARNING] No supported GPU found
```

Raspberry Pi GPU monitoring is not supported by the underlying libraries.

### Permission Denied (Linux)

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or temporarily grant permission
sudo chmod 666 /dev/ttyACM0
```

### pynput Errors (Headless Systems)

If running over SSH without X11 forwarding:
```
[WARNING] pynput not available (needs X display)
```

This is normal. The `FREE_OFF` feature will be disabled, but all monitoring functions work normally.

### High CPU Usage

- Reduce theme complexity (fewer animations)
- Increase refresh intervals in theme YAML
- Disable unused sensors in configuration

---

## 🌍 Platform-Specific Notes

### Raspberry Pi (ARM64)

**Tested on**: Raspberry Pi OS (Debian 12, ARM64)

✅ **Supported**:
- All system monitoring features
- 0.96" and 3.5" displays
- Photo album mode
- Custom themes

⚠️ **Limitations**:
- GPU monitoring not available
- `pynput` requires X display (use VNC or direct connection)
- Some Windows-specific features disabled

**Performance Tips**:
- Use landscape orientation for 0.96" display
- Keep brightness ≤50% to reduce heat
- Disable fastlz compression if experiencing issues

### Windows

**Special Features**:
- LibreHardwareMonitor integration (requires admin)
- System volume monitoring
- Better GPU support (NVIDIA/AMD)

**Note**: Run as Administrator for full hardware access.

### macOS

**Limitations**:
- No GPU monitoring
- Some sensor data may be unavailable
- Tray icon behavior differs

---

## 📁 Project Structure

```
SystemMonitor/
├── main.py                 # Main application entry
├── simple-program.py       # Simple demo program
├── configure.py            # Configuration GUI
├── config.yaml             # User configuration
├── requirements.txt        # Python dependencies
├── library/                # Core library
│   ├── lcd/               # Display drivers
│   │   ├── lcd_comm.py           # Base class
│   │   ├── lcd_comm_weact_a.py   # 3.5" driver
│   │   └── lcd_comm_weact_b.py   # 0.96" driver
│   ├── sensors/           # Hardware sensors
│   ├── display.py         # Display management
│   └── stats.py           # Data collection
└── res/                   # Resources
    ├── themes/            # 59 pre-built themes
    ├── fonts/             # 92 font files
    └── backgrounds/       # Background images
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/FRAOTIAC/WeActStudio.SystemMonitor.git
cd WeActStudio.SystemMonitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### Credits & Acknowledgments

This is a **personal fork** maintained independently with focus on ARM64/Raspberry Pi support.

- **Original Project**: [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) by Matthieu Houdebine
- **Fork Maintainer**: [FRAOTIAC](https://github.com/FRAOTIAC)
- **Hardware Documentation**: Based on publicly available USB-C display specifications

---

## 🔗 Related Projects

- **Original Project**: [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) by Matthieu Houdebine
- **Hardware Reference**: [WeAct Studio GitHub](https://github.com/WeActStudio) (Hardware manufacturer's technical resources)

---

## 📝 Changelog

### [Latest] - 2025-10-06

#### Added
- ✨ Full Raspberry Pi ARM64 support
- 🐧 Optimized for headless Linux environments
- 📦 Graceful degradation for optional dependencies

#### Fixed
- 🐛 ARM64 package compatibility (pyfastlz, pyamdgpuinfo)
- 🔧 Platform-specific GUI attributes
- 🚀 Runtime path errors in process checking
- 🎨 Theme font paths for Unix systems

#### Changed
- 📝 Improved error handling and logging
- 🔌 pynput is now optional (FREE_OFF feature)
- ⚙️ Better cross-platform compatibility

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=FRAOTIAC/WeActStudio.SystemMonitor&type=Date)](https://star-history.com/#FRAOTIAC/WeActStudio.SystemMonitor&Date)

---

## 💬 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/FRAOTIAC/WeActStudio.SystemMonitor/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/FRAOTIAC/WeActStudio.SystemMonitor/discussions)
- 📧 **Email**: Create an issue for support

---

<div align="center">

**Personal fork maintained by [FRAOTIAC](https://github.com/FRAOTIAC)**

Based on the excellent work of the [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) community

[⬆ Back to Top](#usb-display-system-monitor)

</div>
