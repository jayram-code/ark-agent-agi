"""
File Transfer Tool for ARK Agent AGI
Handle file uploads and downloads
"""

import os
import shutil
import base64
from typing import Dict, Any, Optional
from utils.logging_utils import log_event

class FileTransferTool:
    """
    File upload and download operations
    """
    
    def __init__(self, upload_dir: str = "data/uploads", download_dir: str = "data/downloads"):
        self.upload_dir = upload_dir
        self.download_dir = download_dir
        
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(download_dir, exist_ok=True)
        
        log_event("FileTransferTool", {
            "event": "initialized",
            "upload_dir": upload_dir,
            "download_dir": download_dir
        })
    
    def upload_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """
        Upload a file
        
        Args:
            filename: Name of the file
            content: File content as bytes
            
        Returns:
            Upload result
        """
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            
            log_event("FileTransferTool", {
                "event": "file_uploaded",
                "filename": filename,
                "size": file_size
            })
            
            return {
                "success": True,
                "message": f"File uploaded: {filename}",
                "filename": filename,
                "path": file_path,
                "size_bytes": file_size
            }
            
        except Exception as e:
            log_event("FileTransferTool", {
                "event": "upload_error",
                "filename": filename,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def download_file(self, filename: str) -> Dict[str, Any]:
        """
        Download a file
        
        Args:
            filename: Name of the file to download
            
        Returns:
            File content and metadata
        """
        try:
            file_path = os.path.join(self.download_dir, filename)
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {filename}"
                }
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            file_size = os.path.getsize(file_path)
            
            log_event("FileTransferTool", {
                "event": "file_downloaded",
                "filename": filename,
                "size": file_size
            })
            
            return {
                "success": True,
                "filename": filename,
                "content": content,
                "content_base64": base64.b64encode(content).decode('utf-8'),
                "size_bytes": file_size
            }
            
        except Exception as e:
            log_event("FileTransferTool", {
                "event": "download_error",
                "filename": filename,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

file_transfer = FileTransferTool()
