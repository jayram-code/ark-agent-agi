"""
Image Processing Tool for ARK Agent AGI
Resize, crop, and convert images
"""

import os
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from utils.logging_utils import log_event

class ImageProcessingTool:
    """
    Image manipulation operations using PIL/Pillow
    """
    
    def __init__(self, output_dir: str = "data/processed_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        log_event("ImageProcessingTool", {"event": "initialized", "output_dir": output_dir})
    
    def resize_image(self, image_path: str, width: int, height: int, 
                     output_name: str = None) -> Dict[str, Any]:
        """
        Resize an image
        
        Args:
            image_path: Path to input image
            width: Target width
            height: Target height
            output_name: Output filename (optional)
            
        Returns:
            Processing result
        """
        try:
            img = Image.open(image_path)
            original_size = img.size
            
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            if not output_name:
                base = os.path.basename(image_path)
                name, ext = os.path.splitext(base)
                output_name = f"{name}_resized_{width}x{height}{ext}"
            
            output_path = os.path.join(self.output_dir, output_name)
            resized.save(output_path)
            
            log_event("ImageProcessingTool", {
                "event": "image_resized",
                "original_size": original_size,
                "new_size": (width, height)
            })
            
            return {
                "success": True,
                "operation": "resize",
                "input": image_path,
                "output": output_path,
                "original_size": original_size,
                "new_size": (width, height)
            }
            
        except Exception as e:
            log_event("ImageProcessingTool", {"event": "resize_error", "error": str(e)})
            return {"success": False, "error": str(e)}
    
    def crop_image(self, image_path: str, left: int, top: int, right: int, bottom: int,
                   output_name: str = None) -> Dict[str, Any]:
        """Crop an image"""
        try:
            img = Image.open(image_path)
            cropped = img.crop((left, top, right, bottom))
            
            if not output_name:
                base = os.path.basename(image_path)
                name, ext = os.path.splitext(base)
                output_name = f"{name}_cropped{ext}"
            
            output_path = os.path.join(self.output_dir, output_name)
            cropped.save(output_path)
            
            return {
                "success": True,
                "operation": "crop",
                "output": output_path,
                "crop_box": (left, top, right, bottom)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def convert_format(self, image_path: str, target_format: str,
                       output_name: str = None) -> Dict[str, Any]:
        """Convert image format"""
        try:
            img = Image.open(image_path)
            
            if not output_name:
                base = os.path.basename(image_path)
                name, _ = os.path.splitext(base)
                output_name = f"{name}.{target_format.lower()}"
            
            output_path = os.path.join(self.output_dir, output_name)
            
            # Handle RGBA for JPEG
            if target_format.upper() == 'JPEG' and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            img.save(output_path, format=target_format.upper())
            
            return {
                "success": True,
                "operation": "convert",
                "output": output_path,
                "format": target_format
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

image_processor = ImageProcessingTool()
