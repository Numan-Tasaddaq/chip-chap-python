"""
Mark Symbol Images Dialog
Allows user to capture and store mark symbol images for 0-9, A-Z characters.
Matches old C++ MarkSymbolImages dialog functionality.
"""
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QMessageBox, QLabel
)
from PySide6.QtGui import QIcon, QPixmap

SYMBOLS = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H",
    "I", "J", "K", "L", "M", "N", "O", "P", "Q",
    "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
]

# Mapping of symbol to grid position for display
SYMBOL_GRID = {
    "0": (0, 0), "1": (0, 1), "2": (0, 2), "3": (0, 3), "4": (0, 4), "5": (0, 5), "6": (0, 6), "7": (0, 7), "8": (0, 8), "9": (0, 9),
    "A": (1, 0), "B": (1, 1), "C": (1, 2), "D": (1, 3), "E": (1, 4), "F": (1, 5), "G": (1, 6), "H": (1, 7),
    "I": (2, 0), "J": (2, 1), "K": (2, 2), "L": (2, 3), "M": (2, 4), "N": (2, 5), "O": (2, 6), "P": (2, 7), "Q": (2, 8),
    "R": (3, 0), "S": (3, 1), "T": (3, 2), "U": (3, 3), "V": (3, 4), "W": (3, 5), "X": (3, 6), "Y": (3, 7), "Z": (3, 8),
}

MARK_SYMBOLS_DIR = Path("MarkSymbols")


class MarkSymbolImagesDialog(QDialog):
    """
    Dialog for teaching mark symbol images.
    
    User can:
    1. Click on a symbol button (0-9, A-Z)
    2. Be asked if they want to rotate the image
    3. Draw a red ROI box around the symbol
    4. Press Next to capture the symbol
    5. Symbol image is stored in MarkSymbols folder
    """
    
    symbol_captured = Signal(str, np.ndarray)  # (symbol_char, image)
    
    def __init__(self, parent=None, current_image=None):
        super().__init__(parent)
        
        self.setWindowTitle("Mark Symbol Images")
        self.setFixedSize(600, 350)
        
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        
        self.current_image = current_image
        self.current_symbol = None
        self.symbol_images = {}  # symbol_char -> numpy image
        
        # Ensure MarkSymbols directory exists
        MARK_SYMBOLS_DIR.mkdir(exist_ok=True)
        
        # Load existing symbol images
        self._load_symbol_images()
        
        # Build UI
        self._build_ui()
    
    def _load_symbol_images(self):
        """Load existing symbol images from MarkSymbols folder"""
        for symbol in SYMBOLS:
            symbol_file = MARK_SYMBOLS_DIR / f"{symbol}.png"
            if symbol_file.exists():
                self.symbol_images[symbol] = cv2.imread(str(symbol_file), cv2.IMREAD_GRAYSCALE)
    
    def _build_ui(self):
        """Build the dialog UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("Mark Symbols - Click a symbol to teach its image")
        main_layout.addWidget(title)
        
        # Create symbol grid
        grid = QGridLayout()
        grid.setSpacing(5)
        
        self.symbol_buttons = {}
        
        for symbol in SYMBOLS:
            row, col = SYMBOL_GRID[symbol]
            btn = QPushButton(symbol)
            btn.setFixedSize(50, 40)
            btn.clicked.connect(lambda checked=False, s=symbol: self._on_symbol_clicked(s))
            
            # Style button based on whether image is already taught
            if symbol in self.symbol_images:
                btn.setStyleSheet("background-color: #90EE90; font-weight: bold;")
            
            self.symbol_buttons[symbol] = btn
            grid.addWidget(btn, row, col)
        
        main_layout.addLayout(grid)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh All")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._load_symbol_images)
        btn_layout.addWidget(refresh_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _on_symbol_clicked(self, symbol):
        """Handle symbol button click"""
        self.current_symbol = symbol
        
        # Ask if user wants to rotate
        reply = QMessageBox.question(
            self,
            "Rotate Image?",
            f"Do you want to rotate the image for symbol '{symbol}'?\n"
            "Yes - To Rotate the number\n"
            "No - No Rotate the number",
            QMessageBox.Yes | QMessageBox.No
        )
        
        self.rotate_image = (reply == QMessageBox.Yes)
        
        # Hide this dialog (don't close it) so parent can handle ROI selection
        self.hide()
        
        # Emit signal that parent should handle symbol teaching
        self.symbol_captured.emit(symbol, self.current_image if self.current_image is not None else np.array([]))
    
    def set_current_image(self, image):
        """Set the current image for symbol capture"""
        self.current_image = image
    
    def add_symbol_image(self, symbol: str, image: np.ndarray):
        """
        Add a symbol image to storage and update UI.
        
        Args:
            symbol: Symbol character (0-9, A-Z)
            image: NumPy image array
        """
        if symbol not in SYMBOLS:
            return
        
        # Save to MarkSymbols folder
        symbol_file = MARK_SYMBOLS_DIR / f"{symbol}.png"
        cv2.imwrite(str(symbol_file), image)
        
        # Store in memory
        self.symbol_images[symbol] = image
        
        # Update button style
        if symbol in self.symbol_buttons:
            self.symbol_buttons[symbol].setStyleSheet(
                "background-color: #90EE90; font-weight: bold;"
            )
    
    def get_symbol_images(self):
        """Get all captured symbol images"""
        return self.symbol_images
    
    def get_symbol_image(self, symbol: str):
        """Get image for specific symbol"""
        return self.symbol_images.get(symbol)
