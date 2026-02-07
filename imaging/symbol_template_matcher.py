"""
Symbol Template Matching
Matches detected mark blobs against taught symbol templates.
Implements correlation-based template matching like old C++ Correlate() function.
"""
from pathlib import Path
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


MARK_SYMBOLS_DIR = Path("MarkSymbols")


class SymbolTemplateMatcher:
    """
    Template-based symbol recognition using correlation matching.
    Matches detected blobs against taught symbol images.
    """
    
    def __init__(self):
        """Initialize symbol templates from MarkSymbols folder"""
        self.templates = {}  # symbol_char -> (template_image, pixel_count)
        self.load_templates()
    
    def load_templates(self):
        """Load all taught symbol templates from MarkSymbols folder"""
        self.templates = {}
        
        if not MARK_SYMBOLS_DIR.exists():
            return
        
        for symbol_file in MARK_SYMBOLS_DIR.glob("*.png"):
            symbol_char = symbol_file.stem  # Get filename without extension
            
            # Read template as grayscale
            template = cv2.imread(str(symbol_file), cv2.IMREAD_GRAYSCALE)
            if template is None:
                continue
            
            # Store template and its pixel count (for correlation)
            pixel_count = np.count_nonzero(template)
            self.templates[symbol_char] = {
                'image': template,
                'pixel_count': pixel_count,
                'size': template.shape  # (height, width)
            }
    
    def get_correlation_score(
        self,
        blob_image: np.ndarray,
        template_image: np.ndarray,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> int:
        """
        Calculate correlation score between blob and template.
        
        Returns score 0-100 similar to old C++ Correlate() function.
        Higher score = better match
        
        Args:
            blob_image: ROI of detected blob (grayscale)
            template_image: Taught symbol template (grayscale)
            method: OpenCV matching method
        
        Returns:
            Correlation score (0-100)
        """
        try:
            # Ensure same dtype
            blob = blob_image.astype(np.float32)
            template = template_image.astype(np.float32)
            
            # Blob must be at least as large as template
            if blob.shape[0] < template.shape[0] or blob.shape[1] < template.shape[1]:
                return 0
            
            # Perform template matching
            result = cv2.matchTemplate(blob, template, method)
            
            if result.size == 0:
                return 0
            
            # Get best match score (normalized: -1 to 1, convert to 0-100)
            max_val = np.max(result)
            
            # Normalize to 0-100 scale
            score = int(max(0, min(100, (max_val + 1) * 50)))
            
            return score
        except Exception as e:
            return 0
    
    def match_symbol(
        self,
        blob_image: np.ndarray,
        accept_score: int = 70,
        reject_score: int = 50
    ) -> Tuple[Optional[str], int]:
        """
        Find best matching symbol for a blob image.
        
        Matches blob against all taught templates and returns the best match.
        
        Args:
            blob_image: ROI of detected blob (grayscale)
            accept_score: Minimum score to accept match (0-100)
            reject_score: Score below this = definite reject
        
        Returns:
            (symbol_char, correlation_score) or (None, 0) if no good match
        """
        if not self.templates:
            return None, 0
        
        best_symbol = None
        best_score = 0
        
        # Try matching against each taught symbol
        for symbol_char, template_info in self.templates.items():
            template = template_info['image']
            
            score = self.get_correlation_score(blob_image, template)
            
            # Track best match
            if score > best_score:
                best_score = score
                best_symbol = symbol_char
        
        # Only return match if score is acceptable
        if best_score >= accept_score:
            return best_symbol, best_score
        
        # Return None if below accept score
        return None, best_score
    
    def match_all_blobs(
        self,
        image: np.ndarray,
        blob_rects: List[Dict],
        accept_score: int = 70,
        reject_score: int = 50
    ) -> List[Dict]:
        """
        Match all detected blobs against taught symbol templates.
        
        Args:
            image: Source image (grayscale)
            blob_rects: List of blob ROIs [{"x": x, "y": y, "w": w, "h": h}, ...]
            accept_score: Minimum score to accept match
            reject_score: Reject threshold
        
        Returns:
            List of matched symbols with scores:
            [{
                "symbol": "6",
                "score": 95,
                "x": x,
                "y": y,
                "w": w,
                "h": h
            }, ...]
        """
        results = []
        
        if len(self.templates) == 0:
            # No templates taught yet - return blobs as-is
            return [
                {
                    "symbol": None,
                    "score": 0,
                    "x": blob["x"],
                    "y": blob["y"],
                    "w": blob["w"],
                    "h": blob["h"]
                }
                for blob in blob_rects
            ]
        
        for blob in blob_rects:
            x, y, w, h = blob["x"], blob["y"], blob["w"], blob["h"]
            
            # Extract blob ROI
            if y + h <= image.shape[0] and x + w <= image.shape[1]:
                blob_roi = image[y:y+h, x:x+w]
                
                # Match against symbols
                symbol, score = self.match_symbol(
                    blob_roi,
                    accept_score=accept_score,
                    reject_score=reject_score
                )
                
                results.append({
                    "symbol": symbol,
                    "score": score,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h
                })
            else:
                # Invalid ROI
                results.append({
                    "symbol": None,
                    "score": 0,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h
                })
        
        return results
    
    def verify_symbol_sequence(
        self,
        matched_symbols: List[Dict],
        expected_sequence: str = None
    ) -> Tuple[bool, str]:
        """
        Verify that matched symbols form expected sequence.
        
        Args:
            matched_symbols: List of matched symbols from match_all_blobs()
            expected_sequence: Expected string (e.g., "68C") - if None, no check
        
        Returns:
            (is_valid, message)
        """
        # Extract matched symbol characters
        recognized = "".join([m.get("symbol") or "?" for m in matched_symbols])
        
        if expected_sequence is None:
            return True, f"Recognized: {recognized}"
        
        # Check if matches expected sequence
        if recognized == expected_sequence:
            return True, f"Match! Recognized: {recognized}"
        else:
            return False, f"Mismatch! Expected: {expected_sequence}, Got: {recognized}"
    
    def has_templates(self) -> bool:
        """Check if any templates are loaded"""
        return len(self.templates) > 0
    
    def get_template_symbols(self) -> List[str]:
        """Get list of all taught symbols"""
        return sorted(list(self.templates.keys()))
