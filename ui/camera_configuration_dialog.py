"""
Camera Configuration Dialog
Allows user to configure camera parameters: shutter, gain, brightness, 
bytes per packet, and light control intensity for RGB channels.

Matches old C++ CameraSetupDlg from ChipCapacitorAppTool.

⚠️ IMPORTANT - HARDWARE INTEGRATION REQUIRED:
================================================
This dialog saves settings to memory and to a legacy .cam file.
The settings are NOT automatically applied to real camera hardware.

TO MAKE SETTINGS WORK WITH REAL CAMERAS:
1. Use the same SDK as the old system: Teli USB3 Vision (TeliU3vApi / GenICam)
2. Create a camera hardware abstraction layer (e.g., device/camera_hardware.py)
3. Implement apply_to_hardware() method that calls SDK APIs
4. Call apply_to_hardware() in main_window._open_camera_configuration_dialog()

See old C++ OnOK handler in CameraSetupDlg for reference implementation.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class CameraConfigurationDialog(QDialog):
    """Camera Configuration Dialog"""
    
    # Signals
    settings_changed = Signal(dict)  # Emitted when settings change
    
    def __init__(self, parent=None, track_num=1):
        super().__init__(parent)
        self.track_num = track_num
        self.setWindowTitle(f"Camera Configuration - Track{track_num}")
        self.setFixedSize(500, 700)
        self.setModal(True)
        
        # Camera parameters (from old C++)
        self.shutter_1 = 3
        self.shutter_2 = 2
        self.gain = 4
        self.brightness = 1
        self.bytes_per_packet = 1072
        
        # Light control channels (RGB) - Min: 0, Max: 255
        self.lc_intensity_1 = 158  # Channel 1 (Red)
        self.lc_intensity_2 = 255  # Channel 2 (Green)
        self.lc_intensity_3 = 100  # Channel 3 (Blue)
        
        # RGB Gain values (0.0 - 2.0 range typically)
        self.red_gain = 1.0
        self.green_gain = 1.0
        self.blue_gain = 1.0
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel(f"Camera Configuration - Track{self.track_num}")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # ========== Camera Parameters Group ==========
        camera_group = QGroupBox("Camera Parameters", self)
        camera_layout = QGridLayout(camera_group)
        camera_layout.setSpacing(10)
        
        # Shutter 1
        camera_layout.addWidget(QLabel("Shutter 1 (µs):"), 0, 0)
        self.spin_shutter_1 = QSpinBox()
        self.spin_shutter_1.setRange(1, 10000)
        self.spin_shutter_1.setValue(self.shutter_1)
        self.spin_shutter_1.setSingleStep(1)
        camera_layout.addWidget(self.spin_shutter_1, 0, 1)
        
        # Shutter 2
        camera_layout.addWidget(QLabel("Shutter 2 (µs):"), 1, 0)
        self.spin_shutter_2 = QSpinBox()
        self.spin_shutter_2.setRange(1, 10000)
        self.spin_shutter_2.setValue(self.shutter_2)
        self.spin_shutter_2.setSingleStep(1)
        camera_layout.addWidget(self.spin_shutter_2, 1, 1)
        
        # Gain
        camera_layout.addWidget(QLabel("Gain:"), 2, 0)
        self.spin_gain = QSpinBox()
        self.spin_gain.setRange(0, 100)
        self.spin_gain.setValue(self.gain)
        self.spin_gain.setSingleStep(1)
        camera_layout.addWidget(self.spin_gain, 2, 1)
        
        # Brightness
        camera_layout.addWidget(QLabel("Brightness:"), 3, 0)
        self.spin_brightness = QSpinBox()
        self.spin_brightness.setRange(0, 100)
        self.spin_brightness.setValue(self.brightness)
        self.spin_brightness.setSingleStep(1)
        camera_layout.addWidget(self.spin_brightness, 3, 1)
        
        # Bytes per packet
        camera_layout.addWidget(QLabel("Bytes per packet:"), 4, 0)
        self.spin_bytes_per_pkt = QSpinBox()
        self.spin_bytes_per_pkt.setRange(1, 10000)
        self.spin_bytes_per_pkt.setValue(self.bytes_per_packet)
        self.spin_bytes_per_pkt.setSingleStep(1)
        camera_layout.addWidget(self.spin_bytes_per_pkt, 4, 1)
        
        main_layout.addWidget(camera_group)
        
        # ========== Light Controller Group ==========
        light_group = QGroupBox("Light Controller", self)
        light_layout = QVBoxLayout(light_group)
        light_layout.setSpacing(12)
        
        # Channel 1 (Red)
        ch1_layout = QHBoxLayout()
        ch1_layout.addWidget(QLabel("Channel 1 (Red):"))
        ch1_layout.addStretch()
        self.slider_ch1 = QSlider(Qt.Horizontal)
        self.slider_ch1.setRange(0, 255)
        self.slider_ch1.setValue(self.lc_intensity_1)
        self.slider_ch1.setFixedWidth(200)
        self.slider_ch1.sliderMoved.connect(self._on_ch1_slider_moved)
        ch1_layout.addWidget(self.slider_ch1)
        self.label_ch1_value = QLabel(str(self.lc_intensity_1))
        self.label_ch1_value.setFixedWidth(40)
        ch1_layout.addWidget(self.label_ch1_value)
        light_layout.addLayout(ch1_layout)
        
        # Channel 1 Min/Max
        ch1_range_layout = QHBoxLayout()
        ch1_range_layout.addSpacing(100)
        ch1_range_layout.addWidget(QLabel("Min:"))
        self.spin_ch1_min = QSpinBox()
        self.spin_ch1_min.setRange(0, 255)
        self.spin_ch1_min.setValue(0)
        self.spin_ch1_min.setFixedWidth(60)
        ch1_range_layout.addWidget(self.spin_ch1_min)
        ch1_range_layout.addWidget(QLabel("Max:"))
        self.spin_ch1_max = QSpinBox()
        self.spin_ch1_max.setRange(0, 255)
        self.spin_ch1_max.setValue(255)
        self.spin_ch1_max.setFixedWidth(60)
        ch1_range_layout.addWidget(self.spin_ch1_max)
        ch1_range_layout.addStretch()
        light_layout.addLayout(ch1_range_layout)
        
        # Channel 2 (Green)
        ch2_layout = QHBoxLayout()
        ch2_layout.addWidget(QLabel("Channel 2 (Green):"))
        ch2_layout.addStretch()
        self.slider_ch2 = QSlider(Qt.Horizontal)
        self.slider_ch2.setRange(0, 255)
        self.slider_ch2.setValue(self.lc_intensity_2)
        self.slider_ch2.setFixedWidth(200)
        self.slider_ch2.sliderMoved.connect(self._on_ch2_slider_moved)
        ch2_layout.addWidget(self.slider_ch2)
        self.label_ch2_value = QLabel(str(self.lc_intensity_2))
        self.label_ch2_value.setFixedWidth(40)
        ch2_layout.addWidget(self.label_ch2_value)
        light_layout.addLayout(ch2_layout)
        
        # Channel 2 Min/Max
        ch2_range_layout = QHBoxLayout()
        ch2_range_layout.addSpacing(100)
        ch2_range_layout.addWidget(QLabel("Min:"))
        self.spin_ch2_min = QSpinBox()
        self.spin_ch2_min.setRange(0, 255)
        self.spin_ch2_min.setValue(0)
        self.spin_ch2_min.setFixedWidth(60)
        ch2_range_layout.addWidget(self.spin_ch2_min)
        ch2_range_layout.addWidget(QLabel("Max:"))
        self.spin_ch2_max = QSpinBox()
        self.spin_ch2_max.setRange(0, 255)
        self.spin_ch2_max.setValue(255)
        self.spin_ch2_max.setFixedWidth(60)
        ch2_range_layout.addWidget(self.spin_ch2_max)
        ch2_range_layout.addStretch()
        light_layout.addLayout(ch2_range_layout)
        
        # Channel 3 (Blue)
        ch3_layout = QHBoxLayout()
        ch3_layout.addWidget(QLabel("Channel 3 (Blue):"))
        ch3_layout.addStretch()
        self.slider_ch3 = QSlider(Qt.Horizontal)
        self.slider_ch3.setRange(0, 255)
        self.slider_ch3.setValue(self.lc_intensity_3)
        self.slider_ch3.setFixedWidth(200)
        self.slider_ch3.sliderMoved.connect(self._on_ch3_slider_moved)
        ch3_layout.addWidget(self.slider_ch3)
        self.label_ch3_value = QLabel(str(self.lc_intensity_3))
        self.label_ch3_value.setFixedWidth(40)
        ch3_layout.addWidget(self.label_ch3_value)
        light_layout.addLayout(ch3_layout)
        
        # Channel 3 Min/Max
        ch3_range_layout = QHBoxLayout()
        ch3_range_layout.addSpacing(100)
        ch3_range_layout.addWidget(QLabel("Min:"))
        self.spin_ch3_min = QSpinBox()
        self.spin_ch3_min.setRange(0, 255)
        self.spin_ch3_min.setValue(0)
        self.spin_ch3_min.setFixedWidth(60)
        ch3_range_layout.addWidget(self.spin_ch3_min)
        ch3_range_layout.addWidget(QLabel("Max:"))
        self.spin_ch3_max = QSpinBox()
        self.spin_ch3_max.setRange(0, 255)
        self.spin_ch3_max.setValue(255)
        self.spin_ch3_max.setFixedWidth(60)
        ch3_range_layout.addWidget(self.spin_ch3_max)
        ch3_range_layout.addStretch()
        light_layout.addLayout(ch3_range_layout)
        
        main_layout.addWidget(light_group)
        
        # ========== RGB Gain Group ==========
        rgb_group = QGroupBox("RGB Color Gains", self)
        rgb_layout = QGridLayout(rgb_group)
        rgb_layout.setSpacing(10)
        
        # Red Gain
        rgb_layout.addWidget(QLabel("Red Gain:"), 0, 0)
        self.spin_red_gain = QSpinBox()
        self.spin_red_gain.setRange(0, 200)
        self.spin_red_gain.setValue(int(self.red_gain * 100))
        self.spin_red_gain.setSuffix("%")
        rgb_layout.addWidget(self.spin_red_gain, 0, 1)
        
        # Green Gain
        rgb_layout.addWidget(QLabel("Green Gain:"), 1, 0)
        self.spin_green_gain = QSpinBox()
        self.spin_green_gain.setRange(0, 200)
        self.spin_green_gain.setValue(int(self.green_gain * 100))
        self.spin_green_gain.setSuffix("%")
        rgb_layout.addWidget(self.spin_green_gain, 1, 1)
        
        # Blue Gain
        rgb_layout.addWidget(QLabel("Blue Gain:"), 2, 0)
        self.spin_blue_gain = QSpinBox()
        self.spin_blue_gain.setRange(0, 200)
        self.spin_blue_gain.setValue(int(self.blue_gain * 100))
        self.spin_blue_gain.setSuffix("%")
        rgb_layout.addWidget(self.spin_blue_gain, 2, 1)
        
        main_layout.addWidget(rgb_group)
        
        # ========== Buttons ==========
        button_layout = QHBoxLayout()
        
        btn_balance = QPushButton("Balance")
        btn_balance.clicked.connect(self._on_balance_clicked)
        button_layout.addWidget(btn_balance)
        
        button_layout.addStretch()
        
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedWidth(80)
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        main_layout.addLayout(button_layout)
    
    def _on_ch1_slider_moved(self, value):
        """Update Channel 1 label when slider moves"""
        self.lc_intensity_1 = value
        self.label_ch1_value.setText(str(value))
    
    def _on_ch2_slider_moved(self, value):
        """Update Channel 2 label when slider moves"""
        self.lc_intensity_2 = value
        self.label_ch2_value.setText(str(value))
    
    def _on_ch3_slider_moved(self, value):
        """Update Channel 3 label when slider moves"""
        self.lc_intensity_3 = value
        self.label_ch3_value.setText(str(value))
    
    def _on_balance_clicked(self):
        """Balance button clicked - auto-adjust channels"""
        # Calculate average of all three channels
        avg = (self.lc_intensity_1 + self.lc_intensity_2 + self.lc_intensity_3) // 3
        
        # Set all channels to average
        self.slider_ch1.setValue(avg)
        self.slider_ch2.setValue(avg)
        self.slider_ch3.setValue(avg)
        
        self.lc_intensity_1 = avg
        self.lc_intensity_2 = avg
        self.lc_intensity_3 = avg
        
        self.label_ch1_value.setText(str(avg))
        self.label_ch2_value.setText(str(avg))
        self.label_ch3_value.setText(str(avg))
        
        QMessageBox.information(
            self,
            "Balance",
            f"All light channels balanced to {avg}"
        )
    
    def get_settings(self) -> dict:
        """Get all camera settings"""
        return {
            "shutter_1": self.spin_shutter_1.value(),
            "shutter_2": self.spin_shutter_2.value(),
            "gain": self.spin_gain.value(),
            "brightness": self.spin_brightness.value(),
            "bytes_per_packet": self.spin_bytes_per_pkt.value(),
            "lc_intensity_1": self.lc_intensity_1,
            "lc_intensity_2": self.lc_intensity_2,
            "lc_intensity_3": self.lc_intensity_3,
            "lc_min_1": self.spin_ch1_min.value(),
            "lc_max_1": self.spin_ch1_max.value(),
            "lc_min_2": self.spin_ch2_min.value(),
            "lc_max_2": self.spin_ch2_max.value(),
            "lc_min_3": self.spin_ch3_min.value(),
            "lc_max_3": self.spin_ch3_max.value(),
            "red_gain": self.spin_red_gain.value() / 100.0,
            "green_gain": self.spin_green_gain.value() / 100.0,
            "blue_gain": self.spin_blue_gain.value() / 100.0,
        }
    
    def set_settings(self, settings: dict):
        """Load settings into dialog"""
        if "shutter_1" in settings:
            self.spin_shutter_1.setValue(settings["shutter_1"])
        if "shutter_2" in settings:
            self.spin_shutter_2.setValue(settings["shutter_2"])
        if "gain" in settings:
            self.spin_gain.setValue(settings["gain"])
        if "brightness" in settings:
            self.spin_brightness.setValue(settings["brightness"])
        if "bytes_per_packet" in settings:
            self.spin_bytes_per_pkt.setValue(settings["bytes_per_packet"])
        if "lc_intensity_1" in settings:
            self.slider_ch1.setValue(settings["lc_intensity_1"])
            self.lc_intensity_1 = settings["lc_intensity_1"]
            self.label_ch1_value.setText(str(settings["lc_intensity_1"]))
        if "lc_intensity_2" in settings:
            self.slider_ch2.setValue(settings["lc_intensity_2"])
            self.lc_intensity_2 = settings["lc_intensity_2"]
            self.label_ch2_value.setText(str(settings["lc_intensity_2"]))
        if "lc_intensity_3" in settings:
            self.slider_ch3.setValue(settings["lc_intensity_3"])
            self.lc_intensity_3 = settings["lc_intensity_3"]
            self.label_ch3_value.setText(str(settings["lc_intensity_3"]))
        if "lc_min_1" in settings:
            self.spin_ch1_min.setValue(settings["lc_min_1"])
        if "lc_max_1" in settings:
            self.spin_ch1_max.setValue(settings["lc_max_1"])
        if "lc_min_2" in settings:
            self.spin_ch2_min.setValue(settings["lc_min_2"])
        if "lc_max_2" in settings:
            self.spin_ch2_max.setValue(settings["lc_max_2"])
        if "lc_min_3" in settings:
            self.spin_ch3_min.setValue(settings["lc_min_3"])
        if "lc_max_3" in settings:
            self.spin_ch3_max.setValue(settings["lc_max_3"])
        if "red_gain" in settings:
            self.spin_red_gain.setValue(int(settings["red_gain"] * 100))
        if "green_gain" in settings:
            self.spin_green_gain.setValue(int(settings["green_gain"] * 100))
        if "blue_gain" in settings:
            self.spin_blue_gain.setValue(int(settings["blue_gain"] * 100))
