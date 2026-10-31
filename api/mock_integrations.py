"""
api/mock_integrations.py
Mock WhatsApp, Voice Call, and SMS Gateway integrations.
Simulates real API calls with realistic logging and terminal output.
"""

from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import rich for pretty output; fall back to plain print
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
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
    """Print a formatted message to the terminal."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    header = f"[{timestamp}] 📨 {channel} {direction}"
    body = f"From: {sender} → To: {recipient}\n{message}"

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
            print(f"\n{'─' * 60}\n{header}\n{body}\n{'─' * 60}")
    else:
        print(f"\n{'─' * 60}\n{header}\n{body}\n{'─' * 60}")


# ─────────────────────────────────────────────────────────────────────────────
# Mock WhatsApp
# ─────────────────────────────────────────────────────────────────────────────
class MockWhatsApp:
    """
    Simulates a WhatsApp Business API integration.
    All messages are logged and printed to the terminal.
    """

    CHANNEL = "WhatsApp"
    sent_messages: list = []

    def send_message(
        self,
        to: str,
        message: str,
        sender: str = "HealthAI System",
        message_type: str = "text",
    ) -> dict:
        """
        Simulate sending a WhatsApp message.
        Returns a mock API response dict.
        """
        timestamp = datetime.now().isoformat()
        record = {
            "channel": self.CHANNEL,
            "to": to,
            "from": sender,
            "message": message,
            "message_type": message_type,
            "timestamp": timestamp,
            "status": "delivered",
            "message_id": f"WA-{int(time.time())}-{len(self.sent_messages) + 1}",
        }
        MockWhatsApp.sent_messages.append(record)

        # Style based on message type
        style_map = {
            "alert_critical": "bold red",
            "clinical_escalation": "bold red",
            "alert_moderate": "yellow",
            "weekly_summary": "green",
            "text": "cyan",
        }
        style = style_map.get(message_type, "cyan")

        _print_message(
            channel="📱 WhatsApp",
            direction="→ SENT",
            sender=sender,
            recipient=to,
            message=message,
            style=style,
        )
        logger.info(
            f"[WhatsApp] Sent to {to} | type={message_type} | id={record['message_id']}"
        )
        return record


# ─────────────────────────────────────────────────────────────────────────────
# Mock Voice Call
# ─────────────────────────────────────────────────────────────────────────────
class MockVoiceCall:
    """
    Simulates a Twilio-style voice call API.
    Prints the call script and simulates call duration.
    """

    CHANNEL = "Voice"
    call_log: list = []

    def initiate_call(
        self,
        to: str,
        script: str,
        caller_id: str = "Asha HealthBot",
        language: str = "Hindi",
    ) -> dict:
        """
        Simulate initiating a voice call and reading the script.
        Returns a mock call record.
        """
        timestamp = datetime.now().isoformat()
        duration_seconds = max(30, len(script) // 5)  # ~5 chars per second

        call_record = {
            "channel": self.CHANNEL,
            "to": to,
            "caller_id": caller_id,
            "language": language,
            "script": script,
            "duration_seconds": duration_seconds,
            "timestamp": timestamp,
            "status": "completed",
            "call_id": f"CALL-{int(time.time())}-{len(self.call_log) + 1}",
        }
        MockVoiceCall.call_log.append(call_record)

        display = (
            f"📞 VOICE CALL | Duration: ~{duration_seconds}s | Language: {language}\n"
            f"Script:\n{script}"
        )
        _print_message(
            channel="📞 Voice Call",
            direction="→ DIALLING",
            sender=caller_id,
            recipient=to,
            message=display,
            style="magenta",
        )
        logger.info(
            f"[VoiceCall] Called {to} | lang={language} | id={call_record['call_id']}"
        )
        return call_record


# ─────────────────────────────────────────────────────────────────────────────
# Mock SMS Gateway
# ─────────────────────────────────────────────────────────────────────────────
class MockSMSGateway:
    """
    Simulates an SMS gateway (e.g. AWS SNS, MSG91).
    Used for critical one-line alerts when WhatsApp may not be read.
    """

    CHANNEL = "SMS"
    sms_log: list = []

    def send_sms(
        self,
        to: str,
        message: str,
        sender: str = "HealthAI",
    ) -> dict:
        """
        Simulate sending an SMS.
        Message is trimmed to 160 characters for realism.
        """
        if len(message) > 160:
            message = message[:157] + "..."
        timestamp = datetime.now().isoformat()
        record = {
            "channel": self.CHANNEL,
            "to": to,
            "sender": sender,
            "message": message,
            "timestamp": timestamp,
            "status": "sent",
            "sms_id": f"SMS-{int(time.time())}-{len(self.sms_log) + 1}",
        }
        MockSMSGateway.sms_log.append(record)

        _print_message(
            channel="📲 SMS",
            direction="→ SENT",
            sender=sender,
            recipient=to,
            message=message,
            style="yellow",
        )
        logger.info(f"[SMS] Sent to {to} | id={record['sms_id']}")
        return record
