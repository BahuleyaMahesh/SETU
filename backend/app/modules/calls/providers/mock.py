from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..base import TelephonyProvider



class MockProvider(TelephonyProvider):
    """Mock telephony provider for development"""

    name = "mock"

    async def call(
        self,
        to: str,
        from_: str = None,
        ivr_flow_id: str = None,
        call_id: str = None,
    ) -> Dict[str, Any]:
        return {
            "call_id": f"mock_call_{call_id[:8]}",
            "status": "queued",
            "to": to,
            "from": from_,
        }

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        return {
            "success": True,
            "phone": phone,
            "message_id": "mock_sms_id",
        }
