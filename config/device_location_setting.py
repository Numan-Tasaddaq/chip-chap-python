from dataclasses import dataclass

@dataclass
class DeviceLocationSetting:
    enable_package_location: bool = False
    enable_teach_pos: bool = False
    edge_scan_angle: int = 90
    reverse_edge_angle: int = 180
    four_color_threshold: int = 80

    x_pkg_shift_tol: int = 50
    y_pkg_shift_tol: int = 50
