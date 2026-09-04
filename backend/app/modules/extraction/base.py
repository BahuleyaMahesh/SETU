from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class ExtractionProvider(ABC):
    """Base class for extraction providers"""

    name: str = "base"

    @abstractmethod
    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract structured data from text"""
        pass
