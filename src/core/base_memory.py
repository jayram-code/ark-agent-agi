from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMemory(ABC):
    """
    Abstract base class for memory storage systems.
    Defines the interface for storing and retrieving interactions.
    """

    @abstractmethod
    def store_interaction(self, customer_id: str, kind: str, content: str) -> int:
        """
        Store an interaction in the memory bank.

        Args:
            customer_id: Unique identifier for the customer
            kind: Type of interaction (e.g., 'note', 'email', 'chat')
            content: The content of the interaction

        Returns:
            The ID of the stored interaction
        """
        pass

    @abstractmethod
    def get_recent(self, customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve recent interactions for a customer.

        Args:
            customer_id: Unique identifier for the customer
            limit: Maximum number of interactions to return

        Returns:
            List of interaction dictionaries
        """
        pass

    @abstractmethod
    def recall_relevant(self, customer_id: Optional[str], query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Recall relevant interactions based on a query.

        Args:
            customer_id: Unique identifier for the customer (optional)
            query: The search query
            k: Number of relevant items to return

        Returns:
            List of relevant interaction dictionaries with scores
        """
        pass
