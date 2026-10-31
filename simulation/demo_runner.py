"""
simulation/demo_runner.py
DemoRunner — orchestrates the complete 30-day simulation.
Coordinates all 5 AI Agents:
  1. Patient Agent (Asha) — daily multilingual check-ins
  2. Health Monitoring & Risk Analysis Agent — clinical triage & risk scoring
  3. Social Wellbeing Agent — loneliness & healthy ageing tracking
  4. Caregiver Agent (ConnectAgent) — family alerts & weekly summaries
  5. Clinician Agent (MedInsightAgent) — doctor briefings & care plan oversight
"""

from __future__ import annotations
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

from agents.patient_agent import PatientAgent
from agents.caregiver_agent import CaregiverAgent
from agents.clinician_agent import ClinicianAgent
from agents.risk_agent import RiskAnalysisAgent, RiskLevel
from agents.social_agent import SocialWellbeingAgent
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
    Each simulated day coordinates all 5 agents through the shared CarePlan and EventBus.
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
        risk_agent: Optional[RiskAnalysisAgent] = None,
        social_agent: Optional[SocialWellbeingAgent] = None,
    ):
        self.patient_agent = patient_agent
        self.caregiver_agent = caregiver_agent
        self.clinician_agent = clinician_agent
        self.care_plan = care_plan
        self.memory = memory
        self.event_bus = event_bus
        self.timeline = timeline

        # Initialize dedicated risk & social agents if not injected
        self.risk_agent = risk_agent or RiskAnalysisAgent(
            care_plan=self.care_plan, memory=self.memory, event_bus=self.event_bus
        )
        self.social_agent = social_agent or SocialWellbeingAgent(
            care_plan=self.care_plan, memory=self.memory, event_bus=self.event_bus
        )

        self.day_logs: List[Dict[str, Any]] = []
        self.print_delay = DEMO_CONFIG.get("print_delay_seconds", 0.01)

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

        # ── 2. Health Monitoring & Risk Analysis Agent ─────────────────────
        console.print(f"  [bold yellow]🛡️  {self.risk_agent.name} (Risk Analysis Agent)[/bold yellow]")
        risk_eval = self.risk_agent.evaluate_health_record(day_data, day=day)
        console.print(
            f"     Risk Level: [bold]{risk_eval['risk_level']}[/bold] | "
            f"Reason: {risk_eval['reasons'][0]}"
        )

        # ── 3. Social Wellbeing Agent ──────────────────────────────────────
        console.print(f"  [bold magenta]🌸 {self.social_agent.name} (Social Wellbeing Agent)[/bold magenta]")
        social_eval = self.social_agent.evaluate_social_health(day, day_data)
        console.print(
            f"     Social Score: {social_eval['social_score']}/5 | "
            f"Isolation (7d): {social_eval['isolation_days_7d']} days"
        )

        # ── 4. Clinician Agent Monitoring ──────────────────────────────────
        console.print(f"  [bold blue]🩺 {self.clinician_agent.name} (Clinician Agent)[/bold blue]")
        clinician_summary = self.clinician_agent.run_check_in(day_data)
        console.print(f"     {clinician_summary}")

        # ── 5. Caregiver Agent ─────────────────────────────────────────────
        console.print(f"  [bold green]👨‍👩‍👦 {self.caregiver_agent.name} (Caregiver Agent)[/bold green]")
        caregiver_summary = self.caregiver_agent.run_check_in(day_data)
        console.print(f"     {caregiver_summary}")

        # ── 6. Special Events ──────────────────────────────────────────────
        self._handle_special_events(day, day_data)

        # ── Print escalation status ────────────────────────────────────────
        self._print_escalation_banner(day)

        # ── Log the day ───────────────────────────────────────────────────
        self.day_logs.append({
            "day": day,
            "phase": phase,
            "patient_summary": patient_summary,
            "risk_level": risk_eval["risk_level"],
            "social_score": social_eval["social_score"],
            "clinician_summary": clinician_summary,
            "escalation_level": self.care_plan.escalation_level,
        })

    def _handle_special_events(self, day: int, day_data: Dict[str, Any]) -> None:
        """Inject narrative events at key simulation milestones."""
        if day == 7:
            self._announce("📅 Week 1 Complete — Weekly summary sent to caregiver Suresh", style="green")

        if day == 14:
            self._announce(
                "📈 Clinician & Risk Agents detect gradual systolic BP uptrend over last 7 days",
                style="yellow",
            )
            self.care_plan.add_event(
                "TREND_DETECTED",
                "BP systolic upward slope over past 7 days. Monitoring escalated to Level 1.",
                severity="warning",
                day=day,
            )

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
                            f"{adherence['adherence_pct']}% this week. Please check in with him."
                        ),
                        "urgency": "moderate",
                    },
                    source="DemoRunner",
                    day=day,
                )

        if day == 22:
            self._print_escalation_event(day, day_data)

        if day == 24:
            social = self.memory.get_social_summary(PATIENT_PROFILE["id"], days=5)
            if social["isolation_days"] >= 3:
                self._announce_isolation(day, social)

        if day == 27:
            self._announce(
                "📋 Doctor visit in 3 days — Clinician Agent synthesizing 10-point briefing",
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

        if day == 28:
            self._print_emergency_escalation(day, day_data)

        if day == 30:
            self._announce(
                "🏥 Doctor Visit Day! Full 30-day pre-consultation summary generated.",
                style="bold blue",
            )

    # ─── Special Event Handlers ────────────────────────────────────────────

    def _print_escalation_event(self, day: int, day_data: Dict) -> None:
        bp = day_data.get("bp_systolic", 170)
        glucose = day_data.get("blood_glucose", 290)

        console.print()
        console.print(
            Panel(
                f"[bold red]⚠️  DETERIORATING TREND DETECTED — DAY {day}[/bold red]\n\n"
                f"[red]Blood Pressure: {bp}/{day_data.get('bp_diastolic', 98)} mmHg[/red] (Threshold: ≥160)\n"
                f"[red]Blood Glucose: {glucose} mg/dL[/red] (Threshold: ≥250 warning)\n\n"
                f"[bold cyan]🤖 Risk Analysis Agent → Risk classification: High Concern[/bold cyan]\n"
                f"[bold cyan]📱 Alerting Dr. Anjali Sharma via WhatsApp[/bold cyan]\n"
                f"[bold green]👨‍👩‍👦 Caregiver Agent → Notifying Suresh Kumar[/bold green]",
                title="[bold red]🚨 SYSTEM ESCALATION EVENT (LEVEL 2)[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )

        self.care_plan.escalate(
            2,
            f"BP={bp} (rising trend), Glucose={glucose} (warning threshold), Adherence dropping",
        )
        self.event_bus.publish(
            event_type=EventType.ESCALATION_NEEDED,
            data={"level": 2, "vitals": day_data},
            source="DemoRunner",
            day=day,
        )

    def _announce_isolation(self, day: int, social: Dict) -> None:
        console.print()
        console.print(
            Panel(
                f"[yellow]👴 SOCIAL ISOLATION DETECTED — DAY {day}[/yellow]\n\n"
                f"Ramesh Kumar has had no social contact for [bold]{social['isolation_days']} consecutive days[/bold].\n\n"
                f"[cyan]🌸 Social Wellbeing Agent → Triggered gentle walking & companion nudge[/cyan]\n"
                f"[green]👨‍👩‍👦 Caregiver Agent → Encouraged Suresh to schedule phone call[/green]",
                title="[yellow]⚠️  SOCIAL WELLBEING INTERVENTION[/yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    def _print_emergency_escalation(self, day: int, day_data: Dict) -> None:
        bp = day_data.get("bp_systolic", 178)
        glucose = day_data.get("blood_glucose", 318)

        console.print()
        console.print(
            Panel(
                f"[bold red]🆘  CRITICAL ESCALATION — LEVEL 3 (EMERGENCY) — DAY {day}[/bold red]\n\n"
                f"[red]BP: {bp}/{day_data.get('bp_diastolic', 105)} mmHg — CRISIS ZONE[/red]\n"
                f"[red]Blood Glucose: {glucose} mg/dL — DANGER ZONE (≥300)[/red]\n\n"
                f"[bold red]IMMEDIATE ACTIONS DISPATCHED:[/bold red]\n"
                f"  📞 Emergency voice call to patient (instructed to sit down calmly)\n"
                f"  📱 Urgent WhatsApp + SMS alert to caregiver Suresh\n"
                f"  🩺 Clinical escalation alert to Dr. Anjali Sharma\n"
                f"  🚑 Emergency 108 protocol standby advisory",
                title="[bold red]🆘  FAIL-SAFE EMERGENCY PROTOCOL[/bold red]",
                border_style="bold red",
                padding=(1, 2),
            )
        )

        self.care_plan.escalate(3, f"CRITICAL: BP={bp}, Glucose={glucose}")
        self.event_bus.publish(
            event_type=EventType.ESCALATION_NEEDED,
            data={"level": 3, "vitals": day_data},
            source="DemoRunner",
            day=day,
        )

    def _announce(self, message: str, style: str = "white") -> None:
        console.print()
        console.print(f"  [{style}]▶ {message}[/{style}]")

    def _print_intro(self) -> None:
        console.print()
        console.print(
            Panel(
                f"[bold white]   Proactive Multi-Agent Healthcare Platform (5 AI Agents)[/bold white]\n\n"
                f"   Patient: {PATIENT_PROFILE['name']}, {PATIENT_PROFILE['age']}M | {', '.join(PATIENT_PROFILE['conditions'])}\n"
                f"   Doctor: {PATIENT_PROFILE['doctor_name']} | {PATIENT_PROFILE['hospital']}\n"
                f"   Caregiver: Suresh Kumar (Son)\n\n"
                f"   Active Agent Ecosystem:\n"
                f"     🤖 Asha (Patient Agent) — Proactive multilingual check-ins\n"
                f"     🛡️  RiskAnalysisAgent — Deterministic clinical rules + AI triage\n"
                f"     🌸 SocialWellbeingAgent — Emotional wellbeing & routine tracking\n"
                f"     🩺 MedInsightAgent (Clinician Agent) — Trend synthesis & care plan\n"
                f"     👨‍👩‍👦 ConnectAgent (Caregiver Agent) — Family alerts & action logging",
                title="[bold blue]🏥 CARESYNC AI — HEALTH-01 TRACK[/bold blue]",
                border_style="blue",
            )
        )

    def _print_day_header(self, day: int, date_str: str, phase: str) -> None:
        phase_labels = {
            "stable": "[green]✅ STABLE[/green]",
            "deteriorating": "[yellow]📈 DETERIORATING[/yellow]",
            "dangerous": "[red]⚠️ DANGEROUS[/red]",
            "intervention": "[bold red]🆘 INTERVENTION[/bold red]",
        }
        phase_str = phase_labels.get(phase, phase)
        console.print(Rule(f"Day {day:2d} | {date_str} | Phase: {phase_str}", style="dim"))

    def _print_escalation_banner(self, day: int) -> None:
        lvl = self.care_plan.escalation_level
        colors = {0: "green", 1: "yellow", 2: "red", 3: "bold red"}
        color = colors.get(lvl, "white")
        console.print(f"     [dim]Active Escalation:[/dim] [{color}]Level {lvl}/3[/{color}]")

    def _print_finale(self) -> None:
        console.print(Rule("Simulation Complete", style="bold green"))

    def get_simulation_summary(self) -> Dict[str, Any]:
        return {
            "total_days": len(self.timeline),
            "peak_escalation": self.care_plan.escalation_level,
            "events_count": len(self.event_bus.get_history()),
            "day_logs": self.day_logs,
        }
