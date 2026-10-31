"""
core/care_plan.py
Shared evolving care plan — the single source of truth shared across all agents.
Uses a singleton pattern so all agents always read and write the same object.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# CarePlan dataclass
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class CarePlan:
    """
    The shared, evolving care plan for a patient.
    All three agents (Patient, Caregiver, Clinician) read and write this object.
    """

    patient_id: str
    patient_name: str

    # Goals are a dict of category -> target string
    goals: Dict[str, Any] = field(default_factory=dict)

    # Medications list of dicts
    medications: List[Dict[str, Any]] = field(default_factory=list)

    # Vitals targets
    vitals_targets: Dict[str, str] = field(default_factory=dict)

    # Recent events — list of event dicts {timestamp, event_type, description, severity}
    recent_events: List[Dict[str, Any]] = field(default_factory=list)

    # Last recorded vitals
    last_vitals: Dict[str, Any] = field(default_factory=dict)

    # Timestamp of last update
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # Escalation level 0-3
    escalation_level: int = 0

    # Escalation reason
    escalation_reason: str = ""

    # Simulation day
    current_day: int = 0

    # Doctor notes
    doctor_notes: List[str] = field(default_factory=list)

    # Caregiver alerts sent
    caregiver_alerts: List[Dict[str, Any]] = field(default_factory=list)

    # Medication adherence % (rolling)
    medication_adherence_pct: float = 100.0

    # Social wellbeing score 1-5
    social_wellbeing_score: float = 3.0

    # ─── Methods ───────────────────────────────────────────────────────────

    def update_vitals(self, vitals: Dict[str, Any]) -> None:
        """Update the most recently recorded vitals."""
        self.last_vitals = {
            **vitals,
            "recorded_at": datetime.now().isoformat(),
        }
        self.last_updated = datetime.now().isoformat()

    def add_event(
        self,
        event_type: str,
        description: str,
        severity: str = "info",
        day: Optional[int] = None,
    ) -> None:
        """
        Append an event to recent_events.
        severity: 'info' | 'warning' | 'critical'
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "day": day if day is not None else self.current_day,
            "event_type": event_type,
            "description": description,
            "severity": severity,
        }
        self.recent_events.append(event)
        self.last_updated = datetime.now().isoformat()

    def escalate(self, level: int, reason: str) -> None:
        """Raise (or lower) the escalation level with a reason."""
        old_level = self.escalation_level
        self.escalation_level = max(0, min(3, level))
        self.escalation_reason = reason
        self.last_updated = datetime.now().isoformat()
        self.add_event(
            event_type="ESCALATION_CHANGE",
            description=f"Escalation changed from level {old_level} → {self.escalation_level}: {reason}",
            severity="critical" if self.escalation_level >= 3 else "warning",
        )

    def add_doctor_note(self, note: str) -> None:
        self.doctor_notes.append(
            {"note": note, "timestamp": datetime.now().isoformat()}
        )
        self.last_updated = datetime.now().isoformat()

    def add_caregiver_alert(self, message: str, urgency: str) -> None:
        self.caregiver_alerts.append(
            {
                "message": message,
                "urgency": urgency,
                "timestamp": datetime.now().isoformat(),
                "day": self.current_day,
            }
        )

    def update_adherence(self, adherence_pct: float) -> None:
        self.medication_adherence_pct = round(adherence_pct, 1)
        self.last_updated = datetime.now().isoformat()

    def update_social_score(self, score: float) -> None:
        self.social_wellbeing_score = round(max(1.0, min(5.0, score)), 1)
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary (JSON-serialisable)."""
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "goals": self.goals,
            "medications": self.medications,
            "vitals_targets": self.vitals_targets,
            "recent_events": self.recent_events[-20:],  # Last 20 events
            "last_vitals": self.last_vitals,
            "last_updated": self.last_updated,
            "escalation_level": self.escalation_level,
            "escalation_reason": self.escalation_reason,
            "current_day": self.current_day,
            "doctor_notes": self.doctor_notes,
            "caregiver_alerts": self.caregiver_alerts,
            "medication_adherence_pct": self.medication_adherence_pct,
            "social_wellbeing_score": self.social_wellbeing_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CarePlan":
        """Deserialize from a plain dictionary."""
        cp = cls(
            patient_id=data["patient_id"],
            patient_name=data["patient_name"],
        )
        cp.goals = data.get("goals", {})
        cp.medications = data.get("medications", [])
        cp.vitals_targets = data.get("vitals_targets", {})
        cp.recent_events = data.get("recent_events", [])
        cp.last_vitals = data.get("last_vitals", {})
        cp.last_updated = data.get("last_updated", datetime.now().isoformat())
        cp.escalation_level = data.get("escalation_level", 0)
        cp.escalation_reason = data.get("escalation_reason", "")
        cp.current_day = data.get("current_day", 0)
        cp.doctor_notes = data.get("doctor_notes", [])
        cp.caregiver_alerts = data.get("caregiver_alerts", [])
        cp.medication_adherence_pct = data.get("medication_adherence_pct", 100.0)
        cp.social_wellbeing_score = data.get("social_wellbeing_score", 3.0)
        return cp

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def get_critical_events(self) -> List[Dict[str, Any]]:
        """Return only critical/warning events."""
        return [e for e in self.recent_events if e["severity"] in ("warning", "critical")]

    def summary_str(self) -> str:
        """One-line summary for logging."""
        return (
            f"[Day {self.current_day}] Escalation={self.escalation_level} | "
            f"BP={self.last_vitals.get('bp_systolic','?')}/{self.last_vitals.get('bp_diastolic','?')} | "
            f"Glucose={self.last_vitals.get('blood_glucose','?')} | "
            f"Adherence={self.medication_adherence_pct}% | "
            f"Social={self.social_wellbeing_score}/5"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────────────────
_care_plan_instance: Optional[CarePlan] = None


def get_care_plan() -> Optional[CarePlan]:
    """Return the singleton CarePlan instance (None until initialized)."""
    return _care_plan_instance


def initialize_care_plan(
    patient_id: str,
    patient_name: str,
    goals: Dict[str, Any],
    medications: List[Dict[str, Any]],
    vitals_targets: Dict[str, str],
) -> CarePlan:
    """Create and register the singleton CarePlan."""
    global _care_plan_instance
    _care_plan_instance = CarePlan(
        patient_id=patient_id,
        patient_name=patient_name,
        goals=goals,
        medications=medications,
        vitals_targets=vitals_targets,
    )
    return _care_plan_instance
