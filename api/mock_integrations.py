"""
api/mock_integrations.py
Mock WhatsApp Business API, Voice Call (IVR/STT), and SMS Gateway adapters.
Provides realistic delivery state transitions (sent -> delivered -> read),
inbound webhook simulation, message inspection, and audit history.
"""

from __future__ import annotations
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import rich for pretty console output
try:
    from rich.console import Console
    from rich.panel import Panel
    _console = Console()
    _rich_available = True
except ImportError:
    _console = None
    _rich_available = False


def _print_message(
    channel: str,
    direction: str,
    sender: str,
    recipient: str,
    message: str,
    style: str = "cyan",
) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = f"[{timestamp}] 📨 {channel} {direction}"
    body = f"From: {sender} -> To: {recipient}\n{message}"

    if _rich_available and _console:
        try:
            _console.print(
                Panel(
                    body,
                    title=f"[bold {style}]{header}[/bold {style}]",
                    border_style=style,
                    padding=(0, 2),
                )
            )
        except Exception:
            print(f"\n{'-' * 60}\n{header}\n{body}\n{'-' * 60}")
    else:
        print(f"\n{'-' * 60}\n{header}\n{body}\n{'-' * 60}")


# ─────────────────────────────────────────────────────────────────────────────
# WhatsApp Business API Simulator & Adapter
# ─────────────────────────────────────────────────────────────────────────────
class MockWhatsApp:
    """
    Simulates a production WhatsApp Business Cloud API integration.
    Maintains delivery states (sent -> delivered -> read) and inbound webhook events.
    """

    CHANNEL = "WhatsApp"
    _message_store: List[Dict[str, Any]] = []

    def __init__(self):
        pass

    def send_message(
        self,
        recipient: str = "",
        message: str = "",
        sender_name: str = "CareSync AI",
        message_type: str = "text",
        to: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch simulated WhatsApp message with delivery state metadata."""
        dest = recipient or to or "+91-9876543210"
        src = sender_name or sender or "CareSync AI"
        msg_id = f"wamid_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        record = {
            "id": msg_id,
            "channel": self.CHANNEL,
            "direction": "outbound",
            "from": src,
            "to": dest,
            "message": message,
            "message_type": message_type,
            "status": "delivered",  # sent -> delivered -> read
            "timestamp": now,
        }
        MockWhatsApp._message_store.append(record)

        style = "bold red" if "urgent" in message_type or "critical" in message_type else ("yellow" if "moderate" in message_type else "cyan")
        _print_message(
            channel="📱 WhatsApp",
            direction="-> SENT",
            sender=src,
            recipient=dest,
            message=message,
            style=style,
        )
        return record

    def receive_inbound(self, from_number: str, message: str) -> Dict[str, Any]:
        """Simulate incoming WhatsApp message from patient or family."""
        msg_id = f"wamid_in_{uuid.uuid4().hex[:12]}"
        record = {
            "id": msg_id,
            "channel": self.CHANNEL,
            "direction": "inbound",
            "from": from_number,
            "to": "CareSync AI WhatsApp Gateway",
            "message": message,
            "message_type": "text",
            "status": "received",
            "timestamp": datetime.now().isoformat(),
        }
        MockWhatsApp._message_store.append(record)
        _print_message(
            channel="📱 WhatsApp",
            direction="<- RECEIVED",
            sender=from_number,
            recipient="CareSync AI",
            message=message,
            style="green",
        )
        return record

    @classmethod
    def get_messages(cls, limit: int = 50, recipient: Optional[str] = None) -> List[Dict[str, Any]]:
        msgs = cls._message_store
        if recipient:
            msgs = [m for m in msgs if m.get("to") == recipient or m.get("from") == recipient]
        return msgs[-limit:]

    @classmethod
    def mark_as_read(cls, message_id: str) -> bool:
        for m in cls._message_store:
            if m["id"] == message_id:
                m["status"] = "read"
                return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Voice Call Simulation Adapter
# ─────────────────────────────────────────────────────────────────────────────
class MockVoiceCall:
    """Simulates automated outbound telephone calls with IVR / TTS speech."""

    CHANNEL = "Voice Call"
    _call_logs: List[Dict[str, Any]] = []

    def make_call(
        self,
        to: str,
        message: str,
        caller: str = "Asha (Patient Agent)",
        call_type: str = "checkin",
        language: str = "Hindi",
    ) -> Dict[str, Any]:
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        record = {
            "call_id": call_id,
            "channel": self.CHANNEL,
            "to": to,
            "caller": caller,
            "message": message,
            "language": language,
            "call_type": call_type,
            "status": "completed",
            "duration_seconds": 45,
            "timestamp": datetime.now().isoformat(),
        }
        MockVoiceCall._call_logs.append(record)

        _print_message(
            channel="📞 Voice Call",
            direction="-> INITIATED",
            sender=caller,
            recipient=to,
            message=f"[Language: {language}] {message}",
            style="bold yellow" if "emergency" in call_type else "magenta",
        )
        return record

    @classmethod
    def get_calls(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return cls._call_logs[-limit:]


# ─────────────────────────────────────────────────────────────────────────────
# SMS Gateway Simulator
# ─────────────────────────────────────────────────────────────────────────────
class MockSMSGateway:
    """Simulates telecom SMS gateway for high-priority emergency family alerts."""

    CHANNEL = "SMS"
    _sms_logs: List[Dict[str, Any]] = []

    def send_sms(
        self,
        recipient: str,
        message: str,
        sender: str = "CareSync",
    ) -> Dict[str, Any]:
        sms_id = f"sms_{uuid.uuid4().hex[:8]}"
        record = {
            "sms_id": sms_id,
            "channel": self.CHANNEL,
            "to": recipient,
            "from": sender,
            "message": message,
            "status": "delivered",
            "timestamp": datetime.now().isoformat(),
        }
        MockSMSGateway._sms_logs.append(record)

        _print_message(
            channel="💬 SMS Gateway",
            direction="-> DISPATCHED",
            sender=sender,
            recipient=recipient,
            message=message,
            style="red",
        )
        return record

    @classmethod
    def get_sms(cls, limit: int = 20) -> List[Dict[str, Any]]:
        return cls._sms_logs[-limit:]
