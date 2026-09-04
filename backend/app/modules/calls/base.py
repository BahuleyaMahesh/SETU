from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class TelephonyProvider(ABC):
    """Base class for telephony providers"""

    name: str = "base"

    @abstractmethod
    async def call(
        self,
        to: str,
        from_: str = None,
        ivr_flow_id: str = None,
        call_id: str = None,
    ) -> Dict[str, Any]:
        """Initiate a call"""
        pass

    @abstractmethod
    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send an SMS"""
        pass
