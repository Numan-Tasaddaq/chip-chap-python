# ui/encrypt_decrypt_dialog.py
"""
Encrypt/Decrypt Images Dialog

Matches old C++ EncryptDecryptImages dialog:
- Encrypt: Select source images (BMP) and destination folder
- Decrypt: Select encrypted images and destination folder
- Create FPC File: Generate fail/pass count file
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import cv2
import numpy as np
from imaging.image_encryption import (
    save_encrypted_file, load_encrypted_file
)


class EncryptDecryptDialog(QDialog):
    """Encrypt/Decrypt Images Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encrypt / Decrypt Images")
        self.resize(600, 400)
        
        # State
        self.encrypt_src_files = []  # List of selected source files
        self.encrypt_dst_folder = ""
        self.decrypt_src_folder = ""
        self.decrypt_dst_folder = ""
        
        self._build_ui()
    
    def _build_ui(self):
        """Build dialog UI"""
        main_layout = QVBoxLayout(self)
        
        # Encrypt Group
        encrypt_group = self._build_encrypt_group()
        main_layout.addWidget(encrypt_group)
        
        # Decrypt Group
        decrypt_group = self._build_decrypt_group()
        main_layout.addWidget(decrypt_group)
        
        # Create FPC Button
        fpc_layout = QHBoxLayout()
        fpc_layout.addStretch()
        self.btn_create_fpc = QPushButton("Create Fail/Pass Images Count File")
        self.btn_create_fpc.clicked.connect(self._create_fpc_file)
        fpc_layout.addWidget(self.btn_create_fpc)
        main_layout.addLayout(fpc_layout)
        
        # Close Button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        close_layout.addWidget(btn_close)
        main_layout.addLayout(close_layout)
    
    def _build_encrypt_group(self) -> QGroupBox:
        """Build encrypt section"""
        group = QGroupBox("Encrypt")
        layout = QFormLayout()
        
        # Source (with browse)
        src_layout = QHBoxLayout()
        self.edit_encrypt_src = QLineEdit()
        self.edit_encrypt_src.setReadOnly(True)
        self.edit_encrypt_src.setPlaceholderText("Select source images...")
        btn_encrypt_src = QPushButton("...")
        btn_encrypt_src.setFixedWidth(30)
        btn_encrypt_src.clicked.connect(self._browse_encrypt_src)
        src_layout.addWidget(self.edit_encrypt_src)
        src_layout.addWidget(btn_encrypt_src)
        layout.addRow("Source:", src_layout)
        
        # Destination (with browse)
        dst_layout = QHBoxLayout()
        self.edit_encrypt_dst = QLineEdit()
        self.edit_encrypt_dst.setReadOnly(True)
        self.edit_encrypt_dst.setPlaceholderText("Select destination folder...")
        btn_encrypt_dst = QPushButton("...")
        btn_encrypt_dst.setFixedWidth(30)
        btn_encrypt_dst.clicked.connect(self._browse_encrypt_dst)
        dst_layout.addWidget(self.edit_encrypt_dst)
        dst_layout.addWidget(btn_encrypt_dst)
        layout.addRow("Destination:", dst_layout)
        
        # Encrypt button
        btn_encrypt = QPushButton("Encrypt")
        btn_encrypt.clicked.connect(self._encrypt_images)
        layout.addRow("", btn_encrypt)
        
        group.setLayout(layout)
        return group
    
    def _build_decrypt_group(self) -> QGroupBox:
        """Build decrypt section"""
        group = QGroupBox("Decrypt")
        layout = QFormLayout()
        
        # Source (with browse)
        src_layout = QHBoxLayout()
        self.edit_decrypt_src = QLineEdit()
        self.edit_decrypt_src.setReadOnly(True)
        self.edit_decrypt_src.setPlaceholderText("Select encrypted images folder...")
        btn_decrypt_src = QPushButton("...")
        btn_decrypt_src.setFixedWidth(30)
        btn_decrypt_src.clicked.connect(self._browse_decrypt_src)
        src_layout.addWidget(self.edit_decrypt_src)
        src_layout.addWidget(btn_decrypt_src)
        layout.addRow("Source:", src_layout)
        
        # Destination (with browse)
        dst_layout = QHBoxLayout()
        self.edit_decrypt_dst = QLineEdit()
        self.edit_decrypt_dst.setReadOnly(True)
        self.edit_decrypt_dst.setPlaceholderText("Select destination folder...")
        btn_decrypt_dst = QPushButton("...")
        btn_decrypt_dst.setFixedWidth(30)
        btn_decrypt_dst.clicked.connect(self._browse_decrypt_dst)
        dst_layout.addWidget(self.edit_decrypt_dst)
        dst_layout.addWidget(btn_decrypt_dst)
        layout.addRow("Destination:", dst_layout)
        
        # Decrypt button
        btn_decrypt = QPushButton("Decrypt")
        btn_decrypt.clicked.connect(self._decrypt_images)
        layout.addRow("", btn_decrypt)
        
        group.setLayout(layout)
        return group
    
    # ===== Encrypt Handlers =====
    
    def _browse_encrypt_src(self):
        """Browse for source images to encrypt"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images to Encrypt",
            "",
            "BMP Files (*.bmp);;All Files (*.*)"
        )
        
        if files:
            self.encrypt_src_files = files
            if len(files) == 1:
                self.edit_encrypt_src.setText(files[0])
            else:
                folder = str(Path(files[0]).parent)
                self.edit_encrypt_src.setText(f"{folder} ({len(files)} files)")
    
    def _browse_encrypt_dst(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder for Encrypted Images"
        )
        
        if folder:
            self.encrypt_dst_folder = folder
            self.edit_encrypt_dst.setText(folder)
    
    def _encrypt_images(self):
        """Encrypt selected images"""
        if not self.encrypt_src_files:
            QMessageBox.warning(self, "Encrypt", "Please select source images")
            return
        
        if not self.encrypt_dst_folder:
            QMessageBox.warning(self, "Encrypt", "Please select destination folder")
            return
        
        dst_path = Path(self.encrypt_dst_folder)
        dst_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        for src_file in self.encrypt_src_files:
            try:
                # Load image
                img = cv2.imread(src_file, cv2.IMREAD_UNCHANGED)
                if img is None:
                    print(f"[WARN] Failed to load: {src_file}")
                    fail_count += 1
                    continue
                
                height, width = img.shape[:2]
                
                # Convert to bytes (flatten image data)
                image_bytes = img.tobytes()
                
                # Get filename
                filename = Path(src_file).name
                
                # Save encrypted
                output_path = dst_path / filename
                save_encrypted_file(
                    str(output_path),
                    width,
                    height,
                    image_bytes,
                    filename
                )
                
                success_count += 1
                print(f"[ENCRYPT] {filename} -> {output_path}")
                
            except Exception as e:
                print(f"[ERROR] Failed to encrypt {src_file}: {e}")
                fail_count += 1
        
        # Show result
        total = success_count + fail_count
        if success_count > 0 and fail_count == 0:
            QMessageBox.information(
                self,
                "Encrypt",
                f"Successfully Encrypted All {success_count} Images"
            )
        elif success_count > 0:
            QMessageBox.warning(
                self,
                "Encrypt",
                f"Encrypted {success_count} of {total} Images\n{fail_count} failed"
            )
        else:
            QMessageBox.critical(
                self,
                "Encrypt",
                f"Failed to Encrypt All {total} Images"
            )
    
    # ===== Decrypt Handlers =====
    
    def _browse_decrypt_src(self):
        """Browse for encrypted images folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Encrypted Images Folder"
        )
        
        if folder:
            self.decrypt_src_folder = folder
            self.edit_decrypt_src.setText(folder)
    
    def _browse_decrypt_dst(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder for Decrypted Images"
        )
        
        if folder:
            self.decrypt_dst_folder = folder
            self.edit_decrypt_dst.setText(folder)
    
    def _decrypt_images(self):
        """Decrypt images from source folder"""
        if not self.decrypt_src_folder:
            QMessageBox.warning(self, "Decrypt", "Please select source folder")
            return
        
        if not self.decrypt_dst_folder:
            QMessageBox.warning(self, "Decrypt", "Please select destination folder")
            return
        
        src_path = Path(self.decrypt_src_folder)
        dst_path = Path(self.decrypt_dst_folder)
        dst_path.mkdir(parents=True, exist_ok=True)
        
        # Find all .bmp files in source folder
        bmp_files = list(src_path.glob("*.bmp"))
        
        if not bmp_files:
            QMessageBox.warning(self, "Decrypt", "No Images Found to decrypt")
            return
        
        success_count = 0
        fail_count = 0
        
        for enc_file in bmp_files:
            try:
                # Load encrypted file
                width, height, image_data, original_filename = load_encrypted_file(str(enc_file))
                
                # Reconstruct image array
                # Determine if color or grayscale based on data size
                expected_gray = width * height
                expected_color = width * height * 3
                
                if len(image_data) == expected_color:
                    # Color image (BGR)
                    img = np.frombuffer(image_data, dtype=np.uint8).reshape((height, width, 3))
                elif len(image_data) == expected_gray:
                    # Grayscale image
                    img = np.frombuffer(image_data, dtype=np.uint8).reshape((height, width))
                else:
                    print(f"[WARN] Unexpected data size for {enc_file.name}")
                    fail_count += 1
                    continue
                
                # Save decrypted image
                output_path = dst_path / original_filename
                cv2.imwrite(str(output_path), img)
                
                success_count += 1
                print(f"[DECRYPT] {enc_file.name} -> {output_path}")
                
            except Exception as e:
                print(f"[ERROR] Failed to decrypt {enc_file}: {e}")
                fail_count += 1
        
        # Show result
        total = success_count + fail_count
        if success_count > 0 and fail_count == 0:
            QMessageBox.information(
                self,
                "Decrypt",
                f"Successfully Decrypted All {success_count} Images"
            )
        elif success_count > 0:
            QMessageBox.warning(
                self,
                "Decrypt",
                f"Decrypted {success_count} of {total} Images\n{fail_count} failed"
            )
        else:
            QMessageBox.critical(
                self,
                "Decrypt",
                f"Failed to Decrypt All {total} Images"
            )
    
    # ===== FPC File Creation =====
    
    def _create_fpc_file(self):
        """Create Fail/Pass Count file (fpc format)"""
        # This would scan the current configuration folder structure
        # and count images in Track1-8 folders
        QMessageBox.information(
            self,
            "Create FPC File",
            "FPC file creation not yet implemented.\n\n"
            "This feature counts images in:\n"
            "- Track folders (Doc1-Doc8)\n"
            "- FailImages subfolders (PkgLoc, Dimension, Body, Terminal, Other)\n"
            "- PassImages folder\n\n"
            "And saves counts to .fpc file."
        )
