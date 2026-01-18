# Chip-Chap Python

A PySide6-based desktop application for device inspection and imaging analysis with license management.

## Features

- **Device Inspection**: Comprehensive device inspection and analysis tools
- **Image Processing**: Advanced image capture and processing using OpenCV
- **License Management**: Built-in license verification system
- **Configuration Management**: Persistent configuration storage for app settings
- **GUI Interface**: Modern desktop interface built with PySide6/Qt

## Requirements

- Python 3.8+
- PySide6 >= 6.0.0
- OpenCV (opencv-python) >= 4.5.0

## Installation

1. Clone or download the project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## License Generation

Before using the application, you must generate a license:

1. Run the license generator:
```bash
python license/licensce_genrator.py
```

2. Follow the prompts to generate a license file
3. The generated license will be saved as `license.json` in the project root
4. This license file is required to run the application

## Usage

Run the application:
```bash
python main.py
```

The application requires a valid license to start. On first run, if a license is not found, a license dialog will be presented. Ensure you have generated a valid license using the license generator before starting the application.

## Project Structure

```
chip-chap-python/
├── main.py                      # Application entry point
├── requirements.txt             # Project dependencies
├── app/                         # Application UI components
│   └── main_window.py          # Main application window
├── config/                      # Configuration management
│   ├── alert_messages.py
│   ├── auto_run_setting.py
│   ├── debug_flags.py
│   ├── device_location_setting.py
│   ├── ignore_fail_count.py
│   ├── inspection_parameters.py
│   ├── lot_information.py
│   └── store.py                # Configuration store
├── device/                      # Device handling
│   └── camera_device.py        # Camera device interface
├── imaging/                     # Image processing
│   ├── grab_service.py
│   ├── image_loader.py
│   ├── pocket_teach_overlay.py
│   └── roi.py                  # Region of Interest
├── inspection/                  # Inspection logic
├── license/                     # License management
│   ├── manager.py
│   └── licensce_genrator.py
├── ui/                          # UI dialogs and components
├── resources/                   # Application resources
├── teaching/                    # Teaching/training modules
└── tests/                       # Test files
```

## Configuration

The application manages various configuration files stored in JSON format:
- `alert_messages.json` - Alert message settings
- `auto_run_setting.json` - Auto-run configuration
- `device_location_setting.json` - Device location configuration
- `inspection_parameters.json` - Inspection parameter settings
- `license.json` - License information

## License

This project includes a license management system. Refer to the `license/` directory for details.
