# imaging/image_encryption.py
"""
Image encryption/decryption using AES-256-CBC (matches old C++ implementation)

C++ Reference: IniFile.cpp Encrypt/Decrypt functions
Uses AES-256-CBC with fixed key and IV (same as old system)
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import struct

# Match old C++ implementation exactly
# Key: "01234567890123456789012345678901" (32 bytes for AES-256)
ENCRYPTION_KEY = b"01234567890123456789012345678901"

# IV from old C++ code (16 bytes)
# unsigned char iv[] = {65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80}
ENCRYPTION_IV = bytes([65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80])


def encrypt_image_data(image_data: bytes) -> bytes:
    """
    Encrypt image data using AES-256-CBC
    
    Args:
        image_data: Raw image bytes (grayscale or color)
        
    Returns:
        Encrypted bytes
    """
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, ENCRYPTION_IV)
    padded_data = pad(image_data, AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return encrypted


def decrypt_image_data(encrypted_data: bytes) -> bytes:
    """
    Decrypt image data using AES-256-CBC
    
    Args:
        encrypted_data: Encrypted bytes
        
    Returns:
        Decrypted raw image bytes
    """
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, ENCRYPTION_IV)
    decrypted = cipher.decrypt(encrypted_data)
    unpadded = unpad(decrypted, AES.block_size)
    return unpadded


def encrypt_filename(filename: str) -> bytes:
    """
    Encrypt filename string using AES-256-CBC
    
    Args:
        filename: Original filename (e.g., "image001.bmp")
        
    Returns:
        Encrypted filename bytes
    """
    filename_bytes = filename.encode('utf-8')
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, ENCRYPTION_IV)
    padded_data = pad(filename_bytes, AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return encrypted


def decrypt_filename(encrypted_data: bytes) -> str:
    """
    Decrypt filename from encrypted bytes
    
    Args:
        encrypted_data: Encrypted filename bytes
        
    Returns:
        Original filename string
    """
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, ENCRYPTION_IV)
    decrypted = cipher.decrypt(encrypted_data)
    unpadded = unpad(decrypted, AES.block_size)
    return unpadded.decode('utf-8')


def save_encrypted_file(filepath: str, width: int, height: int, image_data: bytes, filename: str):
    """
    Save encrypted image file (matches old C++ format)
    
    File format:
        [4 bytes] width (int32)
        [4 bytes] height (int32)
        [4 bytes] encrypted_data_size (int32)
        [N bytes] encrypted_image_data
        [4 bytes] encrypted_filename_size (int32)
        [N bytes] encrypted_filename
        
    Args:
        filepath: Output file path
        width: Image width
        height: Image height
        image_data: Raw image bytes
        filename: Original filename
    """
    # Encrypt image data and filename
    encrypted_data = encrypt_image_data(image_data)
    encrypted_name = encrypt_filename(filename)
    
    with open(filepath, 'wb') as f:
        # Write width and height
        f.write(struct.pack('<i', width))
        f.write(struct.pack('<i', height))
        
        # Write encrypted image data size and data
        f.write(struct.pack('<i', len(encrypted_data)))
        f.write(encrypted_data)
        
        # Write encrypted filename size and data
        f.write(struct.pack('<i', len(encrypted_name)))
        f.write(encrypted_name)


def load_encrypted_file(filepath: str) -> tuple[int, int, bytes, str]:
    """
    Load encrypted image file (matches old C++ format)
    
    Args:
        filepath: Input encrypted file path
        
    Returns:
        Tuple of (width, height, decrypted_image_data, original_filename)
        
    Raises:
        ValueError: If file format is invalid
        FileNotFoundError: If file doesn't exist
    """
    with open(filepath, 'rb') as f:
        # Read width and height
        width_bytes = f.read(4)
        if len(width_bytes) != 4:
            raise ValueError("Invalid file format: cannot read width")
        width = struct.unpack('<i', width_bytes)[0]
        
        height_bytes = f.read(4)
        if len(height_bytes) != 4:
            raise ValueError("Invalid file format: cannot read height")
        height = struct.unpack('<i', height_bytes)[0]
        
        # Read encrypted image data size and data
        data_size_bytes = f.read(4)
        if len(data_size_bytes) != 4:
            raise ValueError("Invalid file format: cannot read data size")
        data_size = struct.unpack('<i', data_size_bytes)[0]
        
        encrypted_data = f.read(data_size)
        if len(encrypted_data) != data_size:
            raise ValueError("Invalid file format: incomplete image data")
        
        # Read encrypted filename size and data
        name_size_bytes = f.read(4)
        if len(name_size_bytes) != 4:
            raise ValueError("Invalid file format: cannot read filename size")
        name_size = struct.unpack('<i', name_size_bytes)[0]
        
        encrypted_name = f.read(name_size)
        if len(encrypted_name) != name_size:
            raise ValueError("Invalid file format: incomplete filename data")
    
    # Decrypt data
    decrypted_data = decrypt_image_data(encrypted_data)
    decrypted_name = decrypt_filename(encrypted_name)
    
    return width, height, decrypted_data, decrypted_name
