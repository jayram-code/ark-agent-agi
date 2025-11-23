"""
OpenAPI Tool Wrapper for Shipping Tracker API
Provides a standardized interface for calling shipping tracking APIs
"""

import json
import os
from typing import Any, Dict, Optional

import requests

from utils.observability.logging_utils import log_event


class OpenAPITool:
    """
    Generic OpenAPI tool wrapper that can be configured with OpenAPI specs
    Currently configured for shipping tracker API
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url or os.getenv("SHIPPING_API_URL", "http://localhost:8082")
        self.timeout = timeout
        self.session = requests.Session()

        # Default headers for API calls
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "ARK-Agent-AGI/1.0"}
        )

    def track_order(self, order_id: str) -> Dict[str, Any]:
        """
        Track shipping status for a specific order

        Args:
            order_id: The order ID to track

        Returns:
            Dictionary containing tracking information
        """
        log_event("OpenAPITool", {"event": "tracking_order", "order_id": order_id})

        try:
            # Construct the API endpoint
            endpoint = f"{self.base_url}/track"
            params = {"order_id": order_id}

            # Make the API call
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()

            tracking_data = response.json()

            log_event(
                "OpenAPITool",
                {
                    "event": "tracking_success",
                    "order_id": order_id,
                    "status": tracking_data.get("status", "unknown"),
                },
            )

            return {"success": True, "data": tracking_data, "order_id": order_id}

        except requests.exceptions.RequestException as e:
            error_msg = f"Shipping API error: {str(e)}"
            log_event(
                "OpenAPITool",
                {"event": "tracking_failed", "order_id": order_id, "error": error_msg},
            )

            return {
                "success": False,
                "error": error_msg,
                "order_id": order_id,
                "fallback_data": self._generate_mock_tracking_data(order_id),
            }

    def get_shipping_info(self, order_id: str) -> Dict[str, Any]:
        """
        Get comprehensive shipping information for an order

        Args:
            order_id: The order ID to query

        Returns:
            Dictionary containing shipping details
        """
        log_event("OpenAPITool", {"event": "getting_shipping_info", "order_id": order_id})

        # First try to get tracking info
        tracking_result = self.track_order(order_id)

        if tracking_result["success"]:
            return {
                "success": True,
                "shipping_info": {
                    "order_id": order_id,
                    "tracking_number": tracking_result["data"].get("tracking_number"),
                    "carrier": tracking_result["data"].get("carrier", "Unknown"),
                    "status": tracking_result["data"].get("status", "unknown"),
                    "estimated_delivery": tracking_result["data"].get("estimated_delivery"),
                    "current_location": tracking_result["data"].get("current_location"),
                    "last_update": tracking_result["data"].get("last_update"),
                },
            }
        else:
            # Return fallback data if API fails
            return {
                "success": False,
                "error": tracking_result["error"],
                "shipping_info": tracking_result.get("fallback_data", {}),
            }

    def _generate_mock_tracking_data(self, order_id: str) -> Dict[str, Any]:
        """
        Generate mock tracking data for testing when API is unavailable
        """
        import datetime
        import hashlib

        # Generate consistent mock data based on order_id
        order_hash = hashlib.md5(order_id.encode()).hexdigest()

        # Determine status based on hash
        status_index = int(order_hash[0], 16) % 4
        statuses = ["preparing", "shipped", "in_transit", "delivered"]
        status = statuses[status_index]

        # Generate tracking number
        tracking_number = f"TRK{order_hash[:8].upper()}"

        # Generate estimated delivery (1-7 days from now)
        days_offset = int(order_hash[1], 16) % 7 + 1
        estimated_delivery = (
            datetime.datetime.now() + datetime.timedelta(days=days_offset)
        ).strftime("%Y-%m-%d")

        # Generate current location
        locations = ["Warehouse", "Distribution Center", "In Transit", "Local Facility"]
        location_index = int(order_hash[2], 16) % len(locations)
        current_location = locations[location_index]

        return {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "carrier": "MockCarrier",
            "status": status,
            "estimated_delivery": estimated_delivery,
            "current_location": current_location,
            "last_update": datetime.datetime.now().isoformat(),
            "mock_data": True,  # Flag to indicate this is mock data
        }

    def validate_api_health(self) -> Dict[str, Any]:
        """
        Validate that the shipping API is accessible and healthy

        Returns:
            Health check result
        """
        try:
            # Try to hit a health endpoint or make a test call
            health_endpoint = f"{self.base_url}/health"
            response = self.session.get(health_endpoint, timeout=5)

            if response.status_code == 200:
                return {
                    "healthy": True,
                    "status_code": response.status_code,
                    "message": "Shipping API is accessible",
                }
            else:
                return {
                    "healthy": False,
                    "status_code": response.status_code,
                    "message": f"Shipping API returned status {response.status_code}",
                }

        except requests.exceptions.RequestException as e:
            return {
                "healthy": False,
                "error": str(e),
                "message": "Shipping API is not accessible - using mock data",
            }


# Global instance for easy access
shipping_api = OpenAPITool()


def track_shipping_order(order_id: str) -> Dict[str, Any]:
    """
    Convenience function for tracking shipping orders

    Args:
        order_id: The order ID to track

    Returns:
        Tracking result
    """
    return shipping_api.track_order(order_id)


def get_shipping_information(order_id: str) -> Dict[str, Any]:
    """
    Convenience function for getting comprehensive shipping information

    Args:
        order_id: The order ID to query

    Returns:
        Shipping information result
    """
    return shipping_api.get_shipping_info(order_id)


def check_shipping_api_health() -> Dict[str, Any]:
    """
    Check if the shipping API is healthy and accessible

    Returns:
        Health check result
    """
    return shipping_api.validate_api_health()
