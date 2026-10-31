"""
core/event_bus.py
Simple synchronous pub/sub event bus for agent-to-agent coordination.
Maintains an in-memory chronological event stream with filtering for audit.
"""

from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Canonical event type constants
# ─────────────────────────────────────────────────────────────────────────────
class EventType:
    VITALS_ALERT                  = "VITALS_ALERT"
    MEDICATION_MISSED             = "MEDICATION_MISSED"
    SOCIAL_ISOLATION_DETECTED     = "SOCIAL_ISOLATION_DETECTED"
    ESCALATION_NEEDED             = "ESCALATION_NEEDED"
    DOCTOR_VISIT_APPROACHING      = "DOCTOR_VISIT_APPROACHING"
    FAMILY_NOTIFICATION           = "FAMILY_NOTIFICATION"
    CHECKIN_COMPLETED             = "CHECKIN_COMPLETED"
    TREND_ALERT                   = "TREND_ALERT"
    INTERVENTION_REQUESTED        = "INTERVENTION_REQUESTED"
    ESCALATION_RESOLVED           = "ESCALATION_RESOLVED"
    # New HEALTH-01 canonical events
    RISK_EVALUATION_TRIGGERED     = "RISK_EVALUATION_TRIGGERED"
    RISK_ALERT_ISSUED             = "RISK_ALERT_ISSUED"
    CARE_PLAN_PROPOSAL_CREATED    = "CARE_PLAN_PROPOSAL_CREATED"
    CARE_PLAN_APPROVED            = "CARE_PLAN_APPROVED"
    CAREGIVER_ACTION_RECORDED     = "CAREGIVER_ACTION_RECORDED"
    SOCIAL_INTERVENTION_TRIGGERED = "SOCIAL_INTERVENTION_TRIGGERED"
    SCHEDULE_TRIGGERED            = "SCHEDULE_TRIGGERED"
    EMERGENCY_TRIGGERED           = "EMERGENCY_TRIGGERED"


# ─────────────────────────────────────────────────────────────────────────────
# Event record
# ─────────────────────────────────────────────────────────────────────────────
class Event:
    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "system",
        day: int = 0,
    ):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.day = day
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "day": self.day,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, source={self.source}, day={self.day})"


# ─────────────────────────────────────────────────────────────────────────────
# EventBus
# ─────────────────────────────────────────────────────────────────────────────
class EventBus:
    """
    Synchronous publish/subscribe event bus.
    Handlers are called immediately upon publishing.
    Maintains an audit history of all dispatched events.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)
        self._history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register a handler function for a given event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f"[EventBus] Subscribed handler {handler.__qualname__!r} to {event_type!r}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Remove a handler from a given event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "system",
        day: int = 0,
    ) -> Event:
        """
        Publish an event synchronously to all registered listeners.
        """
        event = Event(event_type=event_type, data=data, source=source, day=day)
        self._history.append(event)
        handlers = self._subscribers.get(event_type, [])
        logger.debug(
            f"[EventBus] Publishing {event_type!r} from {source!r} "
            f"(day={day}) -> {len(handlers)} handler(s)"
        )
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error(
                    f"[EventBus] Handler {handler.__qualname__!r} raised an error for "
                    f"event {event_type!r}: {exc}",
                    exc_info=True,
                )
        return event

    def get_history(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        day: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical events with optional filtering."""
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if day is not None:
            events = [e for e in events if e.day == day]
        return [e.to_dict() for e in events[-limit:]]

    def clear_history(self) -> None:
        self._history.clear()
