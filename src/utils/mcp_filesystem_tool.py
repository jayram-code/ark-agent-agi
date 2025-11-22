"""
MCP FileSystem Tool for reading knowledge base documents
Provides a standardized interface for agents to access files in data/kb_docs/
"""

import os
import json
import glob
from typing import Dict, Any, List, Optional
from utils.logging_utils import log_event

class MCPFileSystemTool:
    """
    Model Context Protocol FileSystem Tool
    Allows agents to read and search files in the knowledge base directory
    """
    
    def __init__(self, kb_directory: str = None):
        self.kb_directory = kb_directory or os.path.join(os.getcwd(), "data", "kb_docs")
        self.ensure_kb_directory()
    
    def ensure_kb_directory(self):
        """Ensure the knowledge base directory exists"""
        if not os.path.exists(self.kb_directory):
            os.makedirs(self.kb_directory, exist_ok=True)
            log_event("MCPFileSystemTool", {"event": "created_kb_directory", "path": self.kb_directory})
    
    def list_documents(self, pattern: str = "*.txt") -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base matching a pattern
        
        Args:
            pattern: File pattern to match (default: *.txt)
            
        Returns:
            List of document metadata
        """
        search_pattern = os.path.join(self.kb_directory, pattern)
        files = glob.glob(search_pattern)
        
        documents = []
        for file_path in files:
            try:
                stat = os.stat(file_path)
                documents.append({
                    "filename": os.path.basename(file_path),
                    "path": file_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": self._get_file_type(file_path)
                })
            except OSError as e:
                log_event("MCPFileSystemTool", {"event": "file_stat_error", "file": file_path, "error": str(e)})
        
        log_event("MCPFileSystemTool", {"event": "listed_documents", "count": len(documents), "pattern": pattern})
        return documents
    
    def read_document(self, filename: str, max_chars: int = 10000) -> Dict[str, Any]:
        """
        Read a specific document from the knowledge base
        
        Args:
            filename: Name of the file to read
            max_chars: Maximum characters to read (default: 10000)
            
        Returns:
            Document content and metadata
        """
        file_path = os.path.join(self.kb_directory, filename)
        
        if not os.path.exists(file_path):
            error_msg = f"Document not found: {filename}"
            log_event("MCPFileSystemTool", {"event": "document_not_found", "filename": filename})
            return {
                "success": False,
                "error": error_msg,
                "filename": filename
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(max_chars)
            
            stat = os.stat(file_path)
            
            log_event("MCPFileSystemTool", {"event": "document_read", "filename": filename, "size": len(content)})
            
            return {
                "success": True,
                "filename": filename,
                "content": content,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "type": self._get_file_type(file_path)
            }
            
        except Exception as e:
            error_msg = f"Error reading document {filename}: {str(e)}"
            log_event("MCPFileSystemTool", {"event": "document_read_error", "filename": filename, "error": error_msg})
            return {
                "success": False,
                "error": error_msg,
                "filename": filename
            }
    
    def search_documents(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents containing specific text
        
        Args:
            query: Search query text
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents with relevance scores
        """
        query_lower = query.lower()
        documents = self.list_documents()
        
        matches = []
        for doc_info in documents:
            try:
                doc_result = self.read_document(doc_info["filename"], max_chars=5000)
                if doc_result["success"]:
                    content_lower = doc_result["content"].lower()
                    
                    # Simple relevance scoring based on term frequency
                    relevance_score = self._calculate_relevance(content_lower, query_lower)
                    
                    if relevance_score > 0:
                        matches.append({
                            "filename": doc_info["filename"],
                            "relevance_score": relevance_score,
                            "content_preview": doc_result["content"][:500] + "..." if len(doc_result["content"]) > 500 else doc_result["content"],
                            "size": doc_info["size"],
                            "modified": doc_info["modified"]
                        })
            
            except Exception as e:
                log_event("MCPFileSystemTool", {"event": "search_error", "file": doc_info["filename"], "error": str(e)})
        
        # Sort by relevance score and limit results
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = matches[:max_results]
        
        log_event("MCPFileSystemTool", {"event": "search_completed", "query": query, "results": len(results)})
        return results
    
    def get_document_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Get metadata for a specific document without reading its content
        
        Args:
            filename: Name of the file
            
        Returns:
            Document metadata
        """
        file_path = os.path.join(self.kb_directory, filename)
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Document not found: {filename}",
                "filename": filename
            }
        
        try:
            stat = os.stat(file_path)
            return {
                "success": True,
                "filename": filename,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "type": self._get_file_type(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting metadata for {filename}: {str(e)}",
                "filename": filename
            }
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.txt': 'text',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.csv': 'csv',
            '.pdf': 'pdf',
            '.doc': 'doc',
            '.docx': 'docx'
        }
        return type_map.get(ext, 'unknown')
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """
        Calculate simple relevance score based on term frequency
        
        Args:
            content: Document content (lowercase)
            query: Search query (lowercase)
            
        Returns:
            Relevance score (0-1)
        """
        # Split query into terms
        query_terms = query.split()
        
        if not query_terms:
            return 0.0
        
        # Count occurrences of each term
        term_matches = 0
        for term in query_terms:
            if len(term) > 2:  # Only count terms longer than 2 characters
                if term in content:
                    term_matches += 1
        
        # Calculate relevance as percentage of matched terms
        relevance = term_matches / len(query_terms)
        
        # Bonus for exact phrase match
        if query in content:
            relevance = min(1.0, relevance + 0.3)
        
        return relevance
    
    def create_sample_documents(self):
        """Create sample knowledge base documents for testing"""
        sample_docs = [
            ("refund_policy.txt", "Refund Policy\n\nWe offer full refunds within 30 days of purchase. To request a refund, please contact our customer support team with your order ID and reason for refund. Refunds are processed within 3-5 business days."),
            ("shipping_info.txt", "Shipping Information\n\nStandard shipping takes 5-7 business days. Express shipping is available for 2-3 business day delivery. Tracking information is provided once your order ships."),
            ("technical_support.txt", "Technical Support\n\nFor technical issues, please provide your device model, operating system, and a detailed description of the problem. Our technical team will respond within 24 hours."),
            ("account_management.txt", "Account Management\n\nYou can manage your account settings, update payment methods, and view order history in your account dashboard. For account-related questions, contact support."),
            ("troubleshooting_guide.txt", "Troubleshooting Guide\n\nCommon solutions: 1) Clear browser cache and cookies 2) Try a different browser 3) Disable browser extensions 4) Check internet connection 5) Restart your device")
        ]
        
        for filename, content in sample_docs:
            file_path = os.path.join(self.kb_directory, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                log_event("MCPFileSystemTool", {"event": "created_sample_doc", "filename": filename})
            except Exception as e:
                log_event("MCPFileSystemTool", {"event": "sample_doc_error", "filename": filename, "error": str(e)})

# Global instance for easy access
mcp_filesystem = MCPFileSystemTool()

def search_kb_documents(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Convenience function for searching knowledge base documents
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of matching documents
    """
    return mcp_filesystem.search_documents(query, max_results)

def read_kb_document(filename: str, max_chars: int = 5000) -> Dict[str, Any]:
    """
    Convenience function for reading a knowledge base document
    
    Args:
        filename: Document filename
        max_chars: Maximum characters to read
        
    Returns:
        Document content and metadata
    """
    return mcp_filesystem.read_document(filename, max_chars)

def list_kb_documents(pattern: str = "*.txt") -> List[Dict[str, Any]]:
    """
    Convenience function for listing knowledge base documents
    
    Args:
        pattern: File pattern to match
        
    Returns:
        List of document metadata
    """
    return mcp_filesystem.list_documents(pattern)