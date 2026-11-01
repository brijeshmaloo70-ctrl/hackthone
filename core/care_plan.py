"""
core/care_plan.py
Shared evolving care plan — the single source of truth shared across all agents.
Supports structured proposals, clinical approvals, audit logging, and role-based changes.
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CarePlan:
    """
    The shared, evolving care plan for a patient.
    All agents read this object, and propose or approve updates with audit tracking.
    """

    patient_id: str
    patient_name: str

    # Goals and Targets
    goals: Dict[str, Any] = field(default_factory=dict)
    medications: List[Dict[str, Any]] = field(default_factory=list)
    vitals_targets: Dict[str, str] = field(default_factory=dict)

    # Schedules & Recommendations
    monitoring_schedule: Dict[str, str] = field(default_factory=lambda: {
        "blood_pressure": "Twice daily (Morning 8:00 AM & Evening 7:00 PM)",
        "blood_glucose": "Daily fasting + 2 hrs post-lunch on alternate days",
        "weight": "Weekly on Sunday morning",
    })
    activity_goals: Dict[str, Any] = field(default_factory=lambda: {
        "daily_walk_minutes": 25,
        "daily_water_glasses": 8,
        "social_interaction_target_days": 5,
    })
    dietary_recommendations: List[str] = field(default_factory=lambda: [
        "Sodium restriction < 2.0g per day (DASH diet principles)",
        "Low glycaemic index carbohydrates; eliminate refined sugars",
        "Increase soluble dietary fibre (methi seeds, oats, leafy vegetables)",
    ])
    appointment_schedule: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "doctor": "Dr. Anjali Sharma",
            "specialty": "Geriatrics & Chronic Care",
            "hospital": "Apollo Hospital, Noida",
            "day": 30,
            "status": "scheduled",
        }
    ])
    current_concerns: List[str] = field(default_factory=list)

    # Proposals Audit Trail (Evolving Care Plan lifecycle)
    proposals: List[Dict[str, Any]] = field(default_factory=list)

    # Operational status & history
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    last_vitals: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    escalation_level: int = 0
    escalation_reason: str = ""
    current_day: int = 0
    doctor_notes: List[Dict[str, Any]] = field(default_factory=list)
    caregiver_alerts: List[Dict[str, Any]] = field(default_factory=list)
    medication_adherence_pct: float = 100.0
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
        """Append an event to recent_events audit trail."""
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
        """Raise or lower the escalation level with an audit log."""
        old_level = self.escalation_level
        self.escalation_level = max(0, min(3, level))
        self.escalation_reason = reason
        self.last_updated = datetime.now().isoformat()
        self.add_event(
            event_type="ESCALATION_CHANGE",
            description=f"Escalation changed from level {old_level} -> {self.escalation_level}: {reason}",
            severity="critical" if self.escalation_level >= 3 else ("warning" if self.escalation_level >= 1 else "info"),
        )

    def propose_update(
        self,
        agent_name: str,
        category: str,
        proposed_value: Any,
        reason: str,
        requires_clinical_approval: bool = True,
    ) -> Dict[str, Any]:
        """
        Record a proposed care plan change.
        If non-clinical (e.g. social reminder schedule), can be auto-approved or approved by caregiver.
        """
        proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
        old_val = None
        if hasattr(self, category):
            old_val = getattr(self, category)
        elif category in self.goals:
            old_val = self.goals[category]

        proposal = {
            "id": proposal_id,
            "agent_name": agent_name,
            "category": category,
            "old_value": old_val,
            "proposed_value": proposed_value,
            "reason": reason,
            "requires_clinical_approval": requires_clinical_approval,
            "status": "pending_review",
            "created_at": datetime.now().isoformat(),
            "day": self.current_day,
            "reviewer": None,
            "reviewed_at": None,
        }

        # Auto-apply if it doesn't require clinician authorization
        if not requires_clinical_approval:
            proposal["status"] = "approved"
            proposal["reviewer"] = agent_name
            proposal["reviewed_at"] = datetime.now().isoformat()
            self._apply_approved_update(category, proposed_value)

        self.proposals.append(proposal)
        self.add_event(
            event_type="CARE_PLAN_PROPOSAL",
            description=f"[{agent_name}] Proposed change to '{category}': {reason} (Status: {proposal['status']})",
            severity="info",
        )
        self.last_updated = datetime.now().isoformat()
        return proposal

    def approve_proposal(self, proposal_id: str, reviewer_role: str = "clinician") -> bool:
        """Authorize and apply a care plan update proposal."""
        for prop in self.proposals:
            if prop["id"] == proposal_id and prop["status"] == "pending_review":
                # Verify clinical authorization role
                if prop["requires_clinical_approval"] and reviewer_role not in ["clinician", "doctor", "admin"]:
                    raise PermissionError("Clinical approval required for medication or target alterations.")

                prop["status"] = "approved"
                prop["reviewer"] = reviewer_role
                prop["reviewed_at"] = datetime.now().isoformat()
                self._apply_approved_update(prop["category"], prop["proposed_value"])
                self.add_event(
                    event_type="CARE_PLAN_APPROVED",
                    description=f"Care plan proposal '{proposal_id}' ({prop['category']}) approved by {reviewer_role}",
                    severity="info",
                )
                self.last_updated = datetime.now().isoformat()
                return True
        return False

    def reject_proposal(self, proposal_id: str, reviewer_role: str, reason: str = "") -> bool:
        """Reject a proposed care plan change."""
        for prop in self.proposals:
            if prop["id"] == proposal_id and prop["status"] == "pending_review":
                prop["status"] = "rejected"
                prop["reviewer"] = reviewer_role
                prop["rejection_reason"] = reason
                prop["reviewed_at"] = datetime.now().isoformat()
                self.add_event(
                    event_type="CARE_PLAN_REJECTED",
                    description=f"Proposal '{proposal_id}' rejected by {reviewer_role}: {reason}",
                    severity="info",
                )
                self.last_updated = datetime.now().isoformat()
                return True
        return False

    def _apply_approved_update(self, category: str, new_value: Any) -> None:
        """Apply an approved change.
        A free-text change to a structured field (e.g. "Increase Amlodipine to 10mg" for the
        medications list) is recorded as an amendment instead of replacing the whole list/dict —
        previously approving it wiped the medication list with a string."""
        if hasattr(self, category):
            current = getattr(self, category)
            stamp = datetime.now().isoformat()
            if isinstance(current, list) and not isinstance(new_value, list):
                current.append({"name": "Amendment", "change": new_value, "approved_at": stamp})
            elif isinstance(current, dict) and not isinstance(new_value, dict):
                current.setdefault("approved_changes", []).append({"change": new_value, "approved_at": stamp})
            else:
                setattr(self, category, new_value)
        elif category in self.goals:
            self.goals[category] = new_value

    def add_doctor_note(self, note: str, author: str = "Dr. Anjali Sharma") -> None:
        self.doctor_notes.append({
            "note": note,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "day": self.current_day,
        })
        self.last_updated = datetime.now().isoformat()

    def add_caregiver_alert(self, message: str, urgency: str) -> None:
        self.caregiver_alerts.append({
            "message": message,
            "urgency": urgency,
            "timestamp": datetime.now().isoformat(),
            "day": self.current_day,
        })

    def update_adherence(self, adherence_pct: float) -> None:
        self.medication_adherence_pct = round(adherence_pct, 1)
        self.last_updated = datetime.now().isoformat()

    def update_social_score(self, score: float) -> None:
        self.social_wellbeing_score = round(max(1.0, min(5.0, score)), 1)
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "goals": self.goals,
            "medications": self.medications,
            "vitals_targets": self.vitals_targets,
            "monitoring_schedule": self.monitoring_schedule,
            "activity_goals": self.activity_goals,
            "dietary_recommendations": self.dietary_recommendations,
            "appointment_schedule": self.appointment_schedule,
            "current_concerns": self.current_concerns,
            "proposals": self.proposals,
            "recent_events": self.recent_events[-30:],
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

    def summary_str(self) -> str:
        last_bp = f"{self.last_vitals.get('bp_systolic', '?')}/{self.last_vitals.get('bp_diastolic', '?')}"
        last_gluc = str(self.last_vitals.get("blood_glucose", "?"))
        pending = len([p for p in self.proposals if p["status"] == "pending_review"])
        return (
            f"[Day {self.current_day}] Escalation={self.escalation_level} | "
            f"BP={last_bp} | Glucose={last_gluc} | "
            f"Adherence={self.medication_adherence_pct}% | "
            f"Social={self.social_wellbeing_score}/5 | "
            f"Pending Proposals={pending}"
        )


_shared_care_plan: Optional[CarePlan] = None


def get_care_plan() -> CarePlan:
    global _shared_care_plan
    if _shared_care_plan is None:
        _shared_care_plan = initialize_care_plan("patient_001", "Ramesh Kumar")
    return _shared_care_plan


def initialize_care_plan(
    patient_id: str,
    patient_name: str,
    goals: Optional[Dict[str, Any]] = None,
    medications: Optional[List[Dict[str, Any]]] = None,
    vitals_targets: Optional[Dict[str, str]] = None,
) -> CarePlan:
    global _shared_care_plan
    _shared_care_plan = CarePlan(
        patient_id=patient_id,
        patient_name=patient_name,
        goals=goals or {},
        medications=medications or [],
        vitals_targets=vitals_targets or {},
    )
    return _shared_care_plan
