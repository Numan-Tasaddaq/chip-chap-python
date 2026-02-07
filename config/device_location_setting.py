from dataclasses import dataclass

@dataclass
class DeviceLocationSetting:
    # Basic Settings
    enable_pkg: bool = True
    teach_pos: bool = False
    
    # Edge Scan Settings
    enable_edge_scan: bool = True
    enable_reverse_edge: bool = False
    edge_scan_angle: int = 90
    reverse_edge_angle: int = 180
    
    # Color & Image Settings
    enable_4color: bool = True
    four_color_threshold: int = 80
    ignore_blue: bool = True
    ignore_blue_threshold: int = 150
    
    # Flip Detection
    enable_flip_check: bool = False
    flip_white_body: bool = True
    flip_top: bool = True
    flip_bot: bool = True
    flip_white_tol: int = 10
    flip_bot_tol: int = 5
    
    # Package Location Recheck
    pkg_loc_recheck: bool = True
    pkg_loc_recheck_val: int = 30
    contrast: int = 50
    contrast_plus: int = 0
    
    # Shift Tolerance
    x_pkg_shift_tol: int = 50
    y_pkg_shift_tol: int = 50
    
    # Sampling
    x_sampling_size: int = 1
    y_sampling_size: int = 1
    
    # Angle & Height
    max_parallel_angle: int = 10
    terminal_height_diff: int = 10
    
    # Edge Scan Details
    edge_scan_part_size: int = 4
    dilate_size: int = 3
    
    # Index Gap
    index_gap_enable: bool = True
    index_gap_contrast: int = 50
    index_gap_min_y: int = 100
    
    # Image Processing
    enable_reflection_mask: bool = True
    enable_shot_2: bool = False
    edge_scan_mask_y: int = 50
    
    # Scan Masks
    ignore_top: bool = False
    ignore_left: bool = False
    ignore_bottom: bool = False
    ignore_right: bool = False
    
    # Mark Detection
    enable_mark_inspection: bool = False
    enable_reverse: bool = False
    enable_mix: bool = False
    mark_reverse: bool = False
    
    # Color Image Settings
    insp_img_merge: bool = False
    insp_img_red: bool = True
    insp_img_green: bool = False
    insp_img_blue: bool = False
    insp_img_rg: bool = False
    insp_img_rb: bool = False
    insp_img_gb: bool = False
    
    # Red Mark Filtering
    enable_red_pkg_location: bool = False
    filter_red_enable: bool = False
    filter_red_value: int = 100
    filter_green_value: int = 100
    
    # Line Mask
    line_mask_count: int = 0
