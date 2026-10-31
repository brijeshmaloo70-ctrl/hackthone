"""
core/event_bus.py
Simple synchronous pub/sub event bus for agent-to-agent coordination.
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
    VITALS_ALERT               = "VITALS_ALERT"
    MEDICATION_MISSED          = "MEDICATION_MISSED"
    SOCIAL_ISOLATION_DETECTED  = "SOCIAL_ISOLATION_DETECTED"
    ESCALATION_NEEDED          = "ESCALATION_NEEDED"
    DOCTOR_VISIT_APPROACHING   = "DOCTOR_VISIT_APPROACHING"
    FAMILY_NOTIFICATION        = "FAMILY_NOTIFICATION"
    CHECKIN_COMPLETED          = "CHECKIN_COMPLETED"
    TREND_ALERT                = "TREND_ALERT"
    INTERVENTION_REQUESTED     = "INTERVENTION_REQUESTED"
    ESCALATION_RESOLVED        = "ESCALATION_RESOLVED"


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

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, source={self.source}, day={self.day})"


# ─────────────────────────────────────────────────────────────────────────────
# EventBus
# ─────────────────────────────────────────────────────────────────────────────
class EventBus:
    """
    Simple synchronous publish/subscribe bus.
    Handlers are called immediately (synchronously) on publish.
    All events are logged to an internal history for audit/debugging.
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
    ) -> None:
        """
        Publish an event synchronously.
        All registered handlers for this event_type are called in registration order.
        """
        event = Event(event_type=event_type, data=data, source=source, day=day)
        self._history.append(event)
        handlers = self._subscribers.get(event_type, [])
        logger.debug(
            f"[EventBus] Publishing {event_type!r} from {source!r} "
            f"(day={day}) → {len(handlers)} handler(s)"
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

    def get_history(
        self, event_type: Optional[str] = None
    ) -> List[Event]:
        """Return the full event history, optionally filtered by type."""
        if event_type:
            return [e for e in self._history if e.event_type == event_type]
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    def summary(self) -> Dict[str, int]:
        """Return a count of events by type."""
        counts: Dict[str, int] = defaultdict(int)
        for event in self._history:
            counts[event.event_type] += 1
        return dict(counts)
