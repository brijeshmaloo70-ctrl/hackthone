"""
agents/base_agent.py
Abstract BaseAgent that all specialised agents inherit from.
Provides Gemini LLM integration with graceful fallback.
"""

from __future__ import annotations
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.care_plan import CarePlan
from core.memory import PatientMemory
from core.event_bus import EventBus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all chronic-care AI agents.

    Subclasses must implement `run_check_in(patient_data)`.
    All agents share the same CarePlan, PatientMemory, and EventBus.
    """

    def __init__(
        self,
        name: str,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        self.name = name
        self.care_plan = care_plan
        self.memory = memory
        self.event_bus = event_bus
        self._llm_client = None
        self._llm_available = False
        self._init_llm()

    # ─── LLM Initialisation ────────────────────────────────────────────────

    def _init_llm(self) -> None:
        """Use the shared REST Gemini client (core/llm.py). Falls back to templates if no key."""
        from core.llm import get_llm

        client = get_llm()
        if not client.configured:
            logger.info(f"[{self.name}] GEMINI_API_KEY not set — using template-based responses.")
            self._llm_available = False
            return
        self._llm_client = client
        self._llm_available = True
        logger.info(f"[{self.name}] Gemini client ready (models: {', '.join(client.models)}).")

    # ─── LLM Call ──────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str, fallback: Optional[str] = None) -> str:
        """
        Call Gemini with `prompt`.
        If the API is unavailable or the call fails, return `fallback` (or a generic message).
        """
        if not self._llm_available or self._llm_client is None:
            return fallback or self._generic_fallback(prompt)

        try:
            response = self._llm_client.generate_content(prompt)
            text = response.text.strip()
            return text
        except Exception as exc:
            logger.warning(f"[{self.name}] LLM call failed: {exc}")
            return fallback or self._generic_fallback(prompt)

    def _generic_fallback(self, prompt: str) -> str:
        """Very simple keyword-based fallback when Gemini is unavailable."""
        prompt_lower = prompt.lower()
        if "check" in prompt_lower and "medicine" in prompt_lower:
            return (
                "Namaste Ramesh ji! Aaj ki dawai le li? "
                "Please apni BP aur sugar check karein aur mujhe batayein. "
                "(Hello Ramesh ji! Did you take today's medicine? "
                "Please check your BP and sugar and let me know.)"
            )
        if "escalat" in prompt_lower or "urgent" in prompt_lower or "critical" in prompt_lower:
            return (
                "⚠️ URGENT MEDICAL ALERT: Patient vitals are critically abnormal. "
                "Immediate clinical review required. "
                "BP and glucose readings exceed danger thresholds. "
                "Please contact patient or send emergency assistance."
            )
        if "family" in prompt_lower or "caregiver" in prompt_lower:
            return (
                "Dear Suresh ji, this is an update about your father Ramesh Kumar. "
                "His health metrics have shown concerning trends this week. "
                "Please call him today and ensure he is taking his medications. "
                "The care team has been notified."
            )
        if "doctor" in prompt_lower or "summary" in prompt_lower or "visit" in prompt_lower:
            return (
                "PATIENT VISIT SUMMARY — Ramesh Kumar (78M)\n"
                "Chief concerns: Rising BP trend, suboptimal glycaemic control.\n"
                "Medication adherence has declined over the past 2 weeks.\n"
                "Social isolation noted for 5+ consecutive days.\n"
                "Recommend: Medication review, dietary counselling, caregiver involvement.\n"
            )
        return (
            "I am monitoring your health closely. "
            "Please ensure you take your medicines on time and check your vitals daily."
        )

    # ─── Prompt Builder ────────────────────────────────────────────────────

    def _build_gemini_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a detailed, context-rich prompt for Gemini.
        Subclasses can override or extend this.
        """
        care_plan_summary = self.care_plan.summary_str()
        patient_name = self.care_plan.patient_name
        escalation = self.care_plan.escalation_level
        adherence = self.care_plan.medication_adherence_pct
        social_score = self.care_plan.social_wellbeing_score

        prompt = f"""
You are {self.name}, an AI health agent in a proactive chronic-care system for elderly patients.

PATIENT: {patient_name}, 78 years old
CONDITIONS: Hypertension, Type 2 Diabetes
CURRENT STATUS: {care_plan_summary}
ESCALATION LEVEL: {escalation} (0=normal, 1=watch, 2=warning, 3=critical)
MEDICATION ADHERENCE: {adherence}%
SOCIAL WELLBEING SCORE: {social_score}/5

CONTEXT PROVIDED:
{self._dict_to_text(context)}

INSTRUCTIONS:
- Be warm, empathetic, and clear.
- If the situation is critical, be direct and urgent.
- Use simple language appropriate for a 78-year-old patient or their family.
- Keep your response concise (under 150 words).
""".strip()
        return prompt

    @staticmethod
    def _dict_to_text(d: Dict[str, Any]) -> str:
        lines = []
        for k, v in d.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    # ─── Abstract methods ──────────────────────────────────────────────────

    @abstractmethod
    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """
        Perform the agent's primary check-in / action for a given day.
        Returns a string summary of what was done.
        """
        ...
