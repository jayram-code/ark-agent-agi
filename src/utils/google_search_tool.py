"""
Google Search Tool for ARK Agent AGI
Provides web search capabilities using Google Custom Search API
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from utils.logging_utils import log_event

class GoogleSearchTool:
    """
    Google Custom Search API integration
    Enables agents to search the web for real-time information
    """
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """
        Initialize Google Search Tool
        
        Args:
            api_key: Google API key (defaults to GOOGLE_SEARCH_API_KEY env var)
            search_engine_id: Custom Search Engine ID (defaults to GOOGLE_CSE_ID env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        log_event("GoogleSearchTool", {
            "event": "initialized",
            "has_api_key": bool(self.api_key),
            "has_cse_id": bool(self.search_engine_id)
        })
    
    def search(self, query: str, num_results: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Search Google and return results
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-10, default 5)
            **kwargs: Additional search parameters (e.g., dateRestrict, siteSearch)
            
        Returns:
            Dictionary with search results and metadata
        """
        if not self.api_key or not self.search_engine_id:
            log_event("GoogleSearchTool", {
                "event": "search_failed",
                "error": "missing_credentials",
                "query": query
            })
            return {
                "success": False,
                "error": "Google Search API credentials not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID environment variables.",
                "query": query,
                "results": self._get_fallback_results(query)
            }
        
        try:
            # Limit results to 1-10 as per API constraints
            num_results = max(1, min(10, num_results))
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": num_results,
                **kwargs
            }
            
            log_event("GoogleSearchTool", {
                "event": "search_started",
                "query": query,
                "num_results": num_results
            })
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse and structure the results
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                })
            
            search_info = data.get("searchInformation", {})
            
            log_event("GoogleSearchTool", {
                "event": "search_completed",
                "query": query,
                "results_count": len(results),
                "search_time": search_info.get("searchTime", 0)
            })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": search_info.get("totalResults", "0"),
                "search_time_seconds": search_info.get("searchTime", 0)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Google Search API error: {str(e)}"
            log_event("GoogleSearchTool", {
                "event": "search_error",
                "query": query,
                "error": error_msg
            })
            
            return {
                "success": False,
                "error": error_msg,
                "query": query,
                "results": self._get_fallback_results(query)
            }
        
        except Exception as e:
            error_msg = f"Unexpected error during search: {str(e)}"
            log_event("GoogleSearchTool", {
                "event": "search_unexpected_error",
                "query": query,
                "error": error_msg
            })
            
            return {
                "success": False,
                "error": error_msg,
                "query": query,
                "results": []
            }
    
    def _get_fallback_results(self, query: str) -> List[Dict[str, str]]:
        """
        Provide fallback results when API is unavailable
        
        Args:
            query: Original search query
            
        Returns:
            List of fallback search results
        """
        return [
            {
                "title": f"Google Search: {query}",
                "link": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                "snippet": "Google Search API is not configured. Click to search manually.",
                "displayLink": "www.google.com"
            }
        ]

# Global instance for easy access
google_search = GoogleSearchTool()

def search_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function for web search
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Search results dictionary
    """
    return google_search.search(query, num_results)
