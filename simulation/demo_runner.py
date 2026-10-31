"""
simulation/demo_runner.py
DemoRunner — orchestrates the complete 30-day simulation.
Shows all four demo requirements:
  1. Agent-initiated check-ins (voice/WhatsApp)
  2. Deteriorating trend detection + escalation
  3. Doctor-facing summary
  4. Social isolation detection + family nudge
"""

from __future__ import annotations
import time
import logging
from datetime import datetime
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.progress import track
from rich import print as rprint

from agents.patient_agent import PatientAgent
from agents.caregiver_agent import CaregiverAgent
from agents.clinician_agent import ClinicianAgent
from core.care_plan import CarePlan
from core.event_bus import EventBus, EventType
from core.memory import PatientMemory
from api.mock_integrations import MockWhatsApp, MockVoiceCall
from config.settings import (
    DEMO_CONFIG,
    PATIENT_PROFILE,
    ESCALATION_LEVELS,
    VITAL_THRESHOLDS,
)

logger = logging.getLogger(__name__)
console = Console()


class DemoRunner:
    """
    Orchestrates the 30-day chronic care simulation.
    Each day:
      - Patient agent conducts check-in
      - Clinician agent monitors trends
      - Caregiver agent handles notifications
    """

    def __init__(
        self,
        patient_agent: PatientAgent,
        caregiver_agent: CaregiverAgent,
        clinician_agent: ClinicianAgent,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
        timeline: List[Dict[str, Any]],
    ):
        self.patient_agent = patient_agent
        self.caregiver_agent = caregiver_agent
        self.clinician_agent = clinician_agent
        self.care_plan = care_plan
        self.memory = memory
        self.event_bus = event_bus
        self.timeline = timeline
        self.day_logs: List[Dict[str, Any]] = []
        self.print_delay = DEMO_CONFIG.get("print_delay_seconds", 0.02)

    # ─── Main Entry ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Run the full 30-day simulation."""
        self._print_intro()

        for day_data in self.timeline:
            self._run_day(day_data)
            time.sleep(self.print_delay)

        self._print_finale()

    # ─── Per-Day Logic ─────────────────────────────────────────────────────

    def _run_day(self, day_data: Dict[str, Any]) -> None:
        day = day_data["day"]
        phase = day_data.get("phase", "stable")
        current_date = day_data.get("date", "2024-11-01")

        self._print_day_header(day, current_date, phase)

        # ── 1. Patient Agent Check-in ──────────────────────────────────────
        console.print(f"  [bold cyan]🤖 {self.patient_agent.name} (Patient Agent)[/bold cyan]")
        patient_summary = self.patient_agent.run_check_in(day_data)
        console.print(f"     {patient_summary}")

        # ── 2. Clinician Agent Monitoring ──────────────────────────────────
        console.print(f"  [bold blue]🩺 {self.clinician_agent.name} (Clinician Agent)[/bold blue]")
        clinician_summary = self.clinician_agent.run_check_in(day_data)
        console.print(f"     {clinician_summary}")

        # ── 3. Caregiver Agent ─────────────────────────────────────────────
        console.print(f"  [bold green]👨‍👩‍👦 {self.caregiver_agent.name} (Caregiver Agent)[/bold green]")
        caregiver_summary = self.caregiver_agent.run_check_in(day_data)
        console.print(f"     {caregiver_summary}")

        # ── 4. Special Events ──────────────────────────────────────────────
        self._handle_special_events(day, day_data)

        # ── Print escalation status ────────────────────────────────────────
        self._print_escalation_banner(day)

        # ── Log the day ───────────────────────────────────────────────────
        self.day_logs.append({
            "day": day,
            "phase": phase,
            "patient_summary": patient_summary,
            "clinician_summary": clinician_summary,
            "escalation_level": self.care_plan.escalation_level,
        })

    def _handle_special_events(self, day: int, day_data: Dict[str, Any]) -> None:
        """Inject special narrative events at key simulation days."""

        # ── Day 7: First weekly summary ────────────────────────────────────
        if day == 7:
            self._announce("📅 Week 1 Complete — Weekly summary being sent to family", style="green")

        # ── Day 14: Trend starting to show ─────────────────────────────────
        if day == 14:
            self._announce(
                "📈 Clinician Agent detects gradual BP uptrend over last 7 days",
                style="yellow",
            )
            self.care_plan.add_event(
                "TREND_DETECTED",
                "BP systolic showing upward trend over past 7 days. Monitoring closely.",
                severity="warning",
                day=day,
            )

        # ── Day 19: Medication adherence drop alert ────────────────────────
        if day == 19:
            adherence = self.memory.get_medication_adherence(PATIENT_PROFILE["id"], days=7)
            if adherence["adherence_pct"] < 80:
                self._announce(
                    f"💊 MEDICATION ALERT: Adherence dropped to {adherence['adherence_pct']}% this week!",
                    style="yellow",
                )
                self.event_bus.publish(
                    event_type=EventType.FAMILY_NOTIFICATION,
                    data={
                        "message": (
                            f"⚠️ Ramesh ji's medication adherence has dropped to "
                            f"{adherence['adherence_pct']}% this week. "
                            f"Please ensure he is taking his medicines regularly. "
                            f"Missing BP medication is dangerous."
                        ),
                        "urgency": "moderate",
                    },
                    source="DemoRunner",
                    day=day,
                )

        # ── Day 22: ESCALATION TRIGGERED ──────────────────────────────────
        if day == 22:
            self._print_escalation_event(day, day_data)

        # ── Day 24: Social isolation detected ─────────────────────────────
        if day == 24:
            social = self.memory.get_social_summary(PATIENT_PROFILE["id"], days=5)
            if social["isolation_days"] >= 3:
                self._announce_isolation(day, social)

        # ── Day 27: Preparing for doctor visit ────────────────────────────
        if day == 27:
            self._announce(
                "📋 Doctor visit in 3 days — Clinician Agent preparing comprehensive briefing",
                style="blue",
            )
            self.event_bus.publish(
                event_type=EventType.DOCTOR_VISIT_APPROACHING,
                data={
                    "days_remaining": 3,
                    "patient_name": PATIENT_PROFILE["name"],
                    "message": "Doctor visit approaching. Preparing 30-day summary.",
                },
                source="DemoRunner",
                day=day,
            )

        # ── Day 28: Emergency escalation ──────────────────────────────────
        if day == 28:
            self._print_emergency_escalation(day, day_data)

        # ── Day 30: Doctor visit ───────────────────────────────────────────
        if day == 30:
            self._announce(
                "🏥 Doctor Visit Day! Clinician Agent generating full pre-visit summary...",
                style="bold blue",
            )

    # ─── Special Event Handlers ────────────────────────────────────────────

    def _print_escalation_event(self, day: int, day_data: Dict) -> None:
        """Dramatic escalation trigger on day 22."""
        bp = day_data.get("bp_systolic", 170)
        glucose = day_data.get("blood_glucose", 290)

        console.print()
        console.print(
            Panel(
                f"[bold red]⚠️  DETERIORATING TREND DETECTED — DAY {day}[/bold red]\n\n"
                f"[red]Blood Pressure: {bp}/{day_data.get('bp_diastolic', 98)} mmHg[/red] "
                f"[yellow](Threshold: ≥160)[/yellow]\n"
                f"[red]Blood Glucose: {glucose} mg/dL[/red] "
                f"[yellow](Threshold: ≥250 warning)[/yellow]\n\n"
                f"[yellow]📈 7-day BP trend: INCREASING (+{round((bp - 140) / 140 * 100, 1)}% above baseline)[/yellow]\n"
                f"[yellow]📈 Glucose trend: INCREASING significantly[/yellow]\n\n"
                f"[bold cyan]🤖 Clinician Agent → escalating to Level 2 (WARNING)[/bold cyan]\n"
                f"[bold cyan]📱 Alerting Dr. Anjali Sharma via WhatsApp[/bold cyan]\n"
                f"[bold green]👨‍👩‍👦 Caregiver Agent → notifying Suresh Kumar[/bold green]",
                title="[bold red]🚨 SYSTEM ESCALATION EVENT[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )

        # Force escalation
        self.care_plan.escalate(
            2,
            f"BP={bp} (7-day rising trend), Glucose={glucose} (warning zone), "
            f"Adherence declining",
        )
        self.event_bus.publish(
            event_type=EventType.ESCALATION_NEEDED,
            data={
                "level": 2,
                "vitals": day_data,
                "message": (
                    f"🚨 ESCALATION LEVEL 2: Ramesh Kumar's BP has been rising for 7 days "
                    f"(now {bp}/{day_data.get('bp_diastolic')} mmHg). "
                    f"Blood glucose {glucose} mg/dL. Medication adherence declining. "
                    f"Immediate clinical review recommended."
                ),
            },
            source="DemoRunner",
            day=day,
        )

    def _announce_isolation(self, day: int, social: Dict) -> None:
        """Print isolation detection announcement."""
        console.print()
        console.print(
            Panel(
                f"[yellow]👴 SOCIAL ISOLATION DETECTED — DAY {day}[/yellow]\n\n"
                f"Ramesh Kumar has had NO social interaction for "
                f"[bold]{social['isolation_days']} consecutive days[/bold].\n\n"
                f"[cyan]🤖 Patient Agent (Asha) → sending gentle nudge to patient[/cyan]\n"
                f"[green]👨‍👩‍👦 Caregiver Agent → alerting Suresh Kumar[/green]\n\n"
                f"[italic]Research shows social isolation worsens chronic conditions "
                f"in elderly patients by 30-40%.[/italic]",
                title="[yellow]⚠️  SOCIAL WELLBEING ALERT[/yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    def _print_emergency_escalation(self, day: int, day_data: Dict) -> None:
        """Emergency escalation on day 28."""
        bp = day_data.get("bp_systolic", 178)
        glucose = day_data.get("blood_glucose", 318)

        console.print()
        console.print(
            Panel(
                f"[bold red blink]🆘  CRITICAL ESCALATION — LEVEL 3 — DAY {day}[/bold red blink]\n\n"
                f"[red]BP: {bp}/{day_data.get('bp_diastolic', 105)} mmHg — DANGER ZONE[/red]\n"
                f"[red]Blood Glucose: {glucose} mg/dL — DANGER ZONE (≥300)[/red]\n\n"
                f"[bold red]IMMEDIATE ACTIONS TRIGGERED:[/bold red]\n"
                f"  📞 Emergency voice call to Ramesh Kumar\n"
                f"  📱 WhatsApp + SMS alert to Suresh Kumar\n"
                f"  🩺 Clinical alert to Dr. Anjali Sharma\n"
                f"  🚑 Caregiver asked to escort patient to hospital\n\n"
                f"[bold cyan]Agent Coordination:[/bold cyan]\n"
                f"  Patient Agent → initiated emergency voice call\n"
                f"  Clinician Agent → sent structured escalation alert to doctor\n"
                f"  Caregiver Agent → called family with emergency instructions",
                title="[bold red]🆘  EMERGENCY ESCALATION[/bold red]",
                border_style="bold red",
                padding=(1, 2),
            )
        )

        self.care_plan.escalate(
            3,
            f"CRITICAL: BP={bp} (danger ≥160), Glucose={glucose} (danger ≥300)",
        )
        self.event_bus.publish(
            event_type=EventType.ESCALATION_NEEDED,
            data={
                "level": 3,
                "vitals": day_data,
                "message": (
                    f"🆘 CRITICAL ALERT: Ramesh Kumar (Day {day})\n"
                    f"BP: {bp}/{day_data.get('bp_diastolic')} mmHg (DANGER)\n"
                    f"Blood Glucose: {glucose} mg/dL (DANGER)\n"
                    f"Patient needs IMMEDIATE medical attention.\n"
                    f"Please call patient and dispatch medical assistance."
                ),
            },
            source="DemoRunner",
            day=day,
        )

    # ─── Finale ────────────────────────────────────────────────────────────

    def _print_finale(self) -> None:
        """Print final event bus summary and hand off to report generator."""
        console.print()
        console.rule("[bold blue]30-DAY SIMULATION COMPLETE[/bold blue]")
        console.print()

        # Event bus summary
        event_counts = self.event_bus.summary()
        table = Table(title="📊 Agent Event Bus Summary", show_header=True, header_style="bold cyan")
        table.add_column("Event Type", style="cyan")
        table.add_column("Count", justify="right", style="bold white")

        for event_type, count in sorted(event_counts.items(), key=lambda x: -x[1]):
            table.add_row(event_type, str(count))

        console.print(table)
        console.print()

        # Final care plan state
        console.print(
            Panel(
                self.care_plan.summary_str(),
                title="[bold]Final Care Plan State[/bold]",
                border_style="blue",
            )
        )

    # ─── Printing Helpers ──────────────────────────────────────────────────

    def _print_intro(self) -> None:
        """Print the simulation intro banner."""
        console.print()
        console.print(
            Panel(
                "[bold white]Proactive Agents for Chronic Care & Healthy Ageing[/bold white]\n\n"
                "[cyan]Patient:[/cyan] Ramesh Kumar, 78M | Hypertension + Type 2 Diabetes\n"
                "[cyan]Doctor:[/cyan] Dr. Anjali Sharma | Apollo Hospital, Noida\n"
                "[cyan]Caregiver:[/cyan] Suresh Kumar (Son)\n\n"
                "[green]Agents Active:[/green]\n"
                "  🤖 Asha (Patient Agent) — Multilingual check-ins, vitals, social\n"
                "  🩺 MedInsightAgent (Clinician Agent) — Trend analysis, escalation\n"
                "  👨‍👩‍👦 ConnectAgent (Caregiver Agent) — Family notifications\n\n"
                f"[yellow]Simulation:[/yellow] 30-day monitoring (Nov 1 – Nov 30, 2024)\n"
                f"[yellow]LLM:[/yellow] Google Gemini 1.5 Flash (with template fallback)",
                title="[bold blue]🏥 AI CHRONIC CARE MANAGEMENT SYSTEM[/bold blue]",
                subtitle="[dim]Track 4: Healthcare & Social Impact — HEALTH-01[/dim]",
                border_style="blue",
                padding=(1, 4),
            )
        )
        console.print()
        time.sleep(0.5)

    def _print_day_header(self, day: int, date_str: str, phase: str) -> None:
        """Print a formatted day header."""
        phase_colors = {
            "stable": "green",
            "deteriorating": "yellow",
            "dangerous": "red",
            "intervention": "magenta",
        }
        phase_icons = {
            "stable": "✅",
            "deteriorating": "📈",
            "dangerous": "⚠️",
            "intervention": "🆘",
        }
        color = phase_colors.get(phase, "white")
        icon = phase_icons.get(phase, "•")

        console.print()
        console.rule(
            f"[bold {color}]Day {day:2d} | {date_str} | Phase: {icon} {phase.upper()}[/bold {color}]"
        )

    def _print_escalation_banner(self, day: int) -> None:
        """Print current escalation level if > 0."""
        level = self.care_plan.escalation_level
        if level == 0:
            return
        colors = {1: "yellow", 2: "orange3", 3: "bold red"}
        icons = {1: "👁️", 2: "⚠️", 3: "🆘"}
        color = colors.get(level, "white")
        icon = icons.get(level, "")
        console.print(
            f"  [{color}]{icon} Escalation Level: {level}/3 — {ESCALATION_LEVELS[level]}[/{color}]"
        )

    def _announce(self, message: str, style: str = "white") -> None:
        """Print a highlighted announcement line."""
        console.print(f"\n  [bold {style}]  {message}[/bold {style}]\n")

    # ─── Quick Summary Getter ──────────────────────────────────────────────

    def get_simulation_summary(self) -> Dict[str, Any]:
        """Return a summary dict of the simulation run."""
        return {
            "total_days": len(self.day_logs),
            "event_counts": self.event_bus.summary(),
            "peak_escalation": max(
                (d["escalation_level"] for d in self.day_logs), default=0
            ),
            "final_care_plan": self.care_plan.to_dict(),
            "whatsapp_messages": len(MockWhatsApp.sent_messages),
            "voice_calls": len(MockVoiceCall.call_log),
        }
