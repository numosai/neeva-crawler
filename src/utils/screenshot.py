"""
Screenshot processing utilities
"""
import base64
import io
from pathlib import Path
from PIL import Image


class ScreenshotProcessor:
    """Handles screenshot compression and processing"""
    
    @staticmethod
    def save_compressed_screenshot(screenshot_data, output_path: Path, quality: int = 85) -> bool:
        """
        Save screenshot with JPEG compression to reduce file size
        
        Args:
            screenshot_data: Base64 encoded screenshot or raw bytes
            output_path: Path to save the compressed screenshot
            quality: JPEG quality (0-100, higher = better quality)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Decode if base64 string
            if isinstance(screenshot_data, str):
                screenshot_bytes = base64.b64decode(screenshot_data)
            else:
                screenshot_bytes = screenshot_data
            
            # Open image and convert to RGB if needed
            png_image = Image.open(io.BytesIO(screenshot_bytes))
            if png_image.mode in ('RGBA', 'LA'):
                png_image = png_image.convert('RGB')
            
            # Save as JPEG with compression
            png_image.save(output_path, 'JPEG', quality=quality, optimize=True)
            return True
            
        except Exception as e:
            print(f"❌ Error processing screenshot: {e}")
            return False