"""
core/scheduler.py
Autonomous Proactive Scheduling Engine.
Executes scheduled healthcare jobs (morning check-in, medication follow-up,
hydration/activity prompts, evening assessments) independently of user initiation.
Supports both real-time wall-clock execution and accelerated simulation mode.
"""

from __future__ import annotations
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from core.event_bus import EventBus, EventType
from core.care_plan import CarePlan
from core.memory import PatientMemory

logger = logging.getLogger(__name__)


class ScheduledJob:
    def __init__(
        self,
        job_id: str,
        name: str,
        time_slot: str,  # e.g. "08:00", "09:00", "13:00", "19:00"
        task_func: Callable[[int, Dict[str, Any]], Any],
        description: str = "",
        frequency: str = "daily",
    ):
        self.job_id = job_id
        self.name = name
        self.time_slot = time_slot
        self.task_func = task_func
        self.description = description
        self.frequency = frequency
        self.last_run_day: Optional[int] = None
        self.run_count = 0


class AutonomousScheduler:
    """
    Autonomous Proactive Scheduler.
    Executes health interventions on schedule without requiring the patient
    to open the application or prompt the agent.
    """

    def __init__(
        self,
        event_bus: EventBus,
        care_plan: CarePlan,
        memory: PatientMemory,
        patient_agent=None,
        risk_agent=None,
        social_agent=None,
        caregiver_agent=None,
    ):
        self.event_bus = event_bus
        self.care_plan = care_plan
        self.memory = memory
        self.patient_agent = patient_agent
        self.risk_agent = risk_agent
        self.social_agent = social_agent
        self.caregiver_agent = caregiver_agent

        self.jobs: Dict[str, ScheduledJob] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self._init_default_schedules()

    def _init_default_schedules(self) -> None:
        """Register the canonical daily chronic care schedule."""
        self.register_job(
            job_id="job_morning_checkin",
            name="Morning Health & Vitals Check-in",
            time_slot="08:00",
            task_func=self._run_morning_checkin,
            description="Proactively contacts patient to record fasting BP, morning glucose, sleep quality, and mood.",
        )
        self.register_job(
            job_id="job_med_adherence",
            name="Morning Medication Verification",
            time_slot="09:00",
            task_func=self._run_med_verification,
            description="Checks if morning antihypertensives (Amlodipine) and Metformin were taken; alerts caregiver if missed.",
        )
        self.register_job(
            job_id="job_hydration_activity",
            name="Afternoon Hydration & Activity Prompt",
            time_slot="13:00",
            task_func=self._run_activity_prompt,
            description="Gentle midday reminder for hydration, light walking, and companion check-in.",
        )
        self.register_job(
            job_id="job_evening_assessment",
            name="Evening Health & Dinner Review",
            time_slot="19:00",
            task_func=self._run_evening_assessment,
            description="Evening vitals review, evening medication reminder, and day wrap-up.",
        )

    def register_job(
        self,
        job_id: str,
        name: str,
        time_slot: str,
        task_func: Callable,
        description: str = "",
    ) -> None:
        self.jobs[job_id] = ScheduledJob(
            job_id=job_id,
            name=name,
            time_slot=time_slot,
            task_func=task_func,
            description=description,
        )

    # ─── Job Handlers ──────────────────────────────────────────────────────

    @staticmethod
    def _normalize(day: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agents expect mood as int 1-5; the API may send words like 'tired'."""
        ctx = dict(context)
        ctx["day"] = day
        mood = ctx.get("mood", 3)
        if isinstance(mood, str):
            ctx["mood"] = {"happy": 5, "calm": 4, "okay": 3, "tired": 2, "sad": 2, "dizzy": 1}.get(mood.lower(), 3)
        ctx.setdefault("symptoms", [])
        return ctx

    def _run_morning_checkin(self, day: int, context: Dict[str, Any]) -> str:
        msg = f"[Scheduler 08:00 AM] Proactive Morning Check-in executed for Day {day}."
        if self.patient_agent:
            # Full pipeline: logs vitals/meds/social to memory and fires VITALS_ALERT /
            # MEDICATION_MISSED / CHECKIN_COMPLETED → Risk, Clinician, Caregiver agents react.
            # (Previously only built a greeting string, so nothing downstream ever ran.)
            msg = "[Scheduler 08:00 AM] " + self.patient_agent.run_check_in(self._normalize(day, context))
        self.event_bus.publish(
            event_type=EventType.SCHEDULE_TRIGGERED,
            data={"job": "morning_checkin", "time": "08:00", "day": day},
            source="AutonomousScheduler",
            day=day,
        )
        return msg

    def _run_med_verification(self, day: int, context: Dict[str, Any]) -> str:
        taken = context.get("medication_taken", True)
        if not taken and self.patient_agent:
            # PatientAgent's check-in already published MEDICATION_MISSED — avoid a duplicate alert
            return f"[Scheduler 09:00 AM] Medication missed on Day {day} — caregiver already alerted by Asha."
        if not taken and self.caregiver_agent:
            self.event_bus.publish(
                event_type=EventType.MEDICATION_MISSED,
                data={"day": day, "med_name": "Amlodipine 5mg / Metformin 500mg"},
                source="AutonomousScheduler",
                day=day,
            )
            return f"[Scheduler 09:00 AM] Medication missed on Day {day}! Dispatched caregiver reminder."
        return f"[Scheduler 09:00 AM] Medication verified taken on Day {day}."

    def _run_activity_prompt(self, day: int, context: Dict[str, Any]) -> str:
        if self.social_agent:
            self.social_agent.evaluate_social_health(day, self._normalize(day, context))
        return f"[Scheduler 01:00 PM] Midday wellbeing and activity prompt dispatched for Day {day}."

    def _run_evening_assessment(self, day: int, context: Dict[str, Any]) -> str:
        if self.risk_agent:
            ev = self.risk_agent.evaluate_health_record(self._normalize(day, context), day=day)
            return (f"[Scheduler 07:00 PM] Evening assessment Day {day}: {ev['risk_level']} — "
                    f"escalation level {self.care_plan.escalation_level}.")
        return f"[Scheduler 07:00 PM] Evening physiological assessment completed for Day {day}."

    # ─── Execution Methods ─────────────────────────────────────────────────

    def execute_scheduled_day(self, day: int, day_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Accelerated demo execution: triggers all scheduled jobs sequentially
        for a single simulated day, ensuring no duplicate triggers.
        """
        day_results = []
        for job_id, job in sorted(self.jobs.items(), key=lambda x: x[1].time_slot):
            # Duplicate prevention check
            if job.last_run_day == day:
                continue

            try:
                res_text = job.task_func(day, day_data)
                job.last_run_day = day
                job.run_count += 1
                record = {
                    "job_id": job.job_id,
                    "job_name": job.name,
                    "time_slot": job.time_slot,
                    "day": day,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "result": res_text,
                }
            except Exception as exc:
                logger.error(f"[Scheduler] Error executing {job.name}: {exc}")
                record = {
                    "job_id": job.job_id,
                    "job_name": job.name,
                    "time_slot": job.time_slot,
                    "day": day,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(exc),
                }

            day_results.append(record)
            self.execution_log.append(record)

        return day_results

    def get_upcoming_schedule(self) -> List[Dict[str, Any]]:
        """List all configured proactive schedules."""
        return [
            {
                "job_id": j.job_id,
                "name": j.name,
                "time_slot": j.time_slot,
                "description": j.description,
                "frequency": j.frequency,
                "last_run_day": j.last_run_day,
                "run_count": j.run_count,
            }
            for j in self.jobs.values()
        ]

    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.execution_log[-limit:]

