# config/inspection_parameters.py
from dataclasses import dataclass,field


@dataclass
class InspectionParameters:
    """
    Central storage for inspection parameter limits.
    This is edited by dialogs and read by Teach/Test.
    """
    ranges: dict[str, int] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)
    # ---- Parameter & Measurement ----

    # Unit Parameter
    pkg_loc_min: int = 0
    pkg_loc_max: int = 0

    terminal_length_min: int = 0
    terminal_length_max: int = 0

    term_term_length_min: int = 0
    term_term_length_max: int = 0

    term_term_length_diff_min: int = 0
    term_term_length_diff_max: int = 0

    # Dimension Measurement
    body_contrast_min: int = 0
    body_contrast_max: int = 0

    terminal_contrast_min: int = 0
    terminal_contrast_max: int = 0

    edge_pixel_count_min: int = 0
    edge_pixel_count_max: int = 0

    measurement_count_min: int = 0
    measurement_count_max: int = 0

    terminal_search_offset_min: int = 0
    terminal_search_offset_max: int = 0

    top_offset_min: int = 0
    top_offset_max: int = 0

    bottom_offset_min: int = 0
    bottom_offset_max: int = 0

    # Image Quality
    body_intensity_min: int = 0
    body_intensity_max: int = 255

    terminal_intensity_min: int = 0
    terminal_intensity_max: int = 255

    # ---- Unit Parameters (example – we expand later) ----
    body_length_min: int = 0
    body_length_max: int = 0

    body_width_min: int = 0
    body_width_max: int = 0

    terminal_width_min: int = 0
    terminal_width_max: int = 0

    # ---- State flags ----
    is_defined: bool = False  # becomes True after user applies parameters
    
    # ---- Inspection Item Selection ----

    # Package & Pocket
    enable_package_location: bool = False
    enable_pocket_location: bool = False
    enable_pocket_post_seal: bool = False

    # Dimension Measurement
    check_body_length: bool = False
    check_body_width: bool = False
    check_terminal_width: bool = False
    check_terminal_length: bool = False
    check_term_term_length: bool = False
    adjust_pkgloc_by_body_height: bool = False

    # Terminal Inspection
    check_terminal_pogo: bool = False
    check_incomplete_termination_1: bool = False
    check_incomplete_termination_2: bool = False
    check_terminal_length_diff: bool = False
    check_terminal_to_body_gap: bool = False
    check_terminal_color: bool = False
    check_terminal_oxidation: bool = False

    # Terminal Chipoff
    check_inner_term_chipoff: bool = False
    check_outer_term_chipoff: bool = False

    # Body Inspection
    check_body_stain_1: bool = False
    check_body_stain_2: bool = False
    check_body_color: bool = False
    check_body_to_term_width: bool = False
    check_body_width_diff: bool = False

    # Body Crack
    check_body_crack: bool = False
    check_low_high_contrast: bool = False
    check_black_defect: bool = False
    check_white_defect: bool = False

    # Body Smear
    check_body_smear_1: bool = False
    check_body_smear_2: bool = False
    check_body_smear_3: bool = False
    check_reverse_chip: bool = False
    check_smear_white: bool = False

    # Body Edge
    check_body_edge_black: bool = False
    check_body_edge_white: bool = False

    # TQS
    enable_sealing_stain: bool = False
    enable_sealing_stain2: bool = False
    enable_sealing_shift: bool = False
    enable_black_to_white_scar: bool = False
    enable_hole_reference: bool = False
    enable_white_to_black_scan: bool = False
    enable_emboss_tape_pickup: bool = False

    # Auto Fill
    auto_body_length: bool = False
    auto_terminal_width: bool = False
    auto_terminal_length: bool = False
    auto_term_term_length: bool = False
# inspection width
    check_insp_width_left: bool = False
    check_insp_width_right: bool = False
    check_insp_width_top: bool = False
    check_insp_width_bottom: bool = False

# Binariese Imge option
    pocket_contrast: int = 75


    # ==================================================
    # ---- TEACH RESULTS (Station-specific geometry) ----
    # ==================================================

    # Rotation (used by TOP / BOTTOM and FEED)
    rotation_angle: float = 0.0

    # Package Location ROI (all stations)
    package_x: int = 0
    package_y: int = 0
    package_w: int = 0
    package_h: int = 0

    # Pocket Location ROI (FEED station only)
    pocket_x: int = 0
    pocket_y: int = 0
    pocket_w: int = 0
    pocket_h: int = 0
