"""
main.py
Entry point: initialises all components and runs the 30-day chronic care simulation.
Demonstrates coordination across all 5 AI Agents and shared CarePlan.
"""

import os
import sys
import logging
from datetime import datetime

# ── Fix Windows console encoding ──────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Ensure data/ directory exists BEFORE logging setup ────────────────────────
os.makedirs("data", exist_ok=True)

# ── Load environment variables first ──────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Rich imports ──────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.traceback import install as install_rich_tb
    install_rich_tb(show_locals=False)
    console = Console()
    _rich_available = True
except ImportError:
    console = None
    _rich_available = False

# ── Configure logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/app.log", mode="w", encoding="utf-8"),
    ],
)

# ── Project imports ───────────────────────────────────────────────────────────
from config.settings import (
    PATIENT_PROFILE,
    CARE_GOALS,
    MEDICATION_SCHEDULE,
    ALL_MEDICATIONS,
    DB_CONFIG,
    DEMO_CONFIG,
)
from core.care_plan import initialize_care_plan
from core.memory import PatientMemory
from core.event_bus import EventBus
from agents.patient_agent import PatientAgent
from agents.caregiver_agent import CaregiverAgent
from agents.clinician_agent import ClinicianAgent
from agents.risk_agent import RiskAnalysisAgent
from agents.social_agent import SocialWellbeingAgent
from simulation.patient_data import generate_30_day_timeline
from simulation.demo_runner import DemoRunner
from dashboard.report_generator import ReportGenerator


def main():
    """Bootstrap and run the complete 30-day simulation demo."""

    # ── 1. Print startup banner ───────────────────────────────────────────
    if _rich_available:
        console.print()
        console.print(
            Panel(
                "[bold green]Initialising CareSync AI — 5-Agent Chronic Care Ecosystem...[/bold green]\n\n"
                "[dim]Architecture: Longitudinal SQLite Memory · Singleton Care Plan · Event Bus · 5 AI Agents[/dim]",
                border_style="green",
            )
        )
    else:
        print("\n=== AI Chronic Care Management System (5 Agents) ===\n")

    # ── 2. Initialise core components ────────────────────────────────────
    print_step("Memory Store", "SQLite longitudinal patient memory initialised", "green")
    memory = PatientMemory(db_path=DB_CONFIG["path"])

    print_step("Care Plan", "Shared evolving care plan created for Ramesh Kumar", "green")
    care_plan = initialize_care_plan(
        patient_id=PATIENT_PROFILE["id"],
        patient_name=PATIENT_PROFILE["name"],
        goals=CARE_GOALS,
        medications=ALL_MEDICATIONS,
        vitals_targets=CARE_GOALS["vitals"],
    )

    print_step("Event Bus", "Pub/sub event bus initialised", "green")
    event_bus = EventBus()

    # ── 3. Create all 5 specialized agents ────────────────────────────────
    print_step("Patient Agent", "Asha (Patient Agent) ready [Hindi, Marathi, English]", "cyan")
    patient_agent = PatientAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Risk Analysis Agent", "RiskAnalysisAgent ready [Clinical triage & deterministic rules]", "yellow")
    risk_agent = RiskAnalysisAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Social Wellbeing Agent", "SocialWellbeingAgent ready [Loneliness & routine monitoring]", "magenta")
    social_agent = SocialWellbeingAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Caregiver Agent", "ConnectAgent (Caregiver Agent) ready [Family alerts & actions]", "cyan")
    caregiver_agent = CaregiverAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Clinician Agent", "MedInsightAgent (Clinician Agent) ready [10-pt clinical briefing]", "cyan")
    clinician_agent = ClinicianAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    # ── 4. LLM status ────────────────────────────────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if _rich_available:
        if api_key:
            console.print("  [bold green]✅ Gemini API Key detected — using LLM responses[/bold green]")
        else:
            console.print(
                "  [yellow]⚠️  No GEMINI_API_KEY found — using template-based responses "
                "(set GEMINI_API_KEY in .env for LLM)[/yellow]"
            )
    else:
        status = "Gemini API active" if api_key else "Template mode (no API key)"
        print(f"  LLM Status: {status}")

    # ── 5. Generate 30-day simulation data ───────────────────────────────
    print_step("Simulation Data", "30-day patient timeline generated", "blue")
    timeline = generate_30_day_timeline(
        start_date_str=DEMO_CONFIG["start_date"],
        seed=42,
    )

    # ── 6. Create and run the demo ────────────────────────────────────────
    runner = DemoRunner(
        patient_agent=patient_agent,
        risk_agent=risk_agent,
        social_agent=social_agent,
        caregiver_agent=caregiver_agent,
        clinician_agent=clinician_agent,
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
        timeline=timeline,
    )

    runner.run()

    # ── 7. Generate doctor report ─────────────────────────────────────────
    if _rich_available:
        console.rule("[bold blue]GENERATING DOCTOR PRE-VISIT REPORT[/bold blue]")
    else:
        print("\n=== GENERATING DOCTOR REPORT ===\n")

    report_gen = ReportGenerator(output_dir="reports")
    report = report_gen.generate_doctor_report(
        patient_data=timeline,
        care_plan=care_plan,
        memory=memory,
    )

    # ── 8. Final summary ──────────────────────────────────────────────────
    sim_summary = runner.get_simulation_summary()
    _print_final_summary(sim_summary, care_plan, event_bus)

    # ── 9. Clean up ───────────────────────────────────────────────────────
    memory.close()
    if _rich_available:
        console.print("\n[bold green]✅ Demo complete! Thank you.[/bold green]\n")
    else:
        print("\nDemo complete!\n")


def print_step(component: str, message: str, color: str = "white") -> None:
    if _rich_available:
        console.print(f"  [bold {color}]▶ {component}:[/bold {color}] {message}")
    else:
        print(f"  [{component}] {message}")


def _print_final_summary(summary: dict, care_plan, event_bus) -> None:
    events = event_bus.get_history()
    event_counts = {}
    for e in events:
        t = e.get("event_type", "UNKNOWN")
        event_counts[t] = event_counts.get(t, 0) + 1

    if _rich_available:
        console.print()
        console.print(
            Panel(
                f"[bold]Simulation:[/bold]      30 days completed (All 5 Agents active)\n"
                f"[bold]Peak Escalation:[/bold]  Level {care_plan.escalation_level}/3 ({care_plan.escalation_reason})\n"
                f"[bold]Events fired:[/bold]     {len(events)} total on Event Bus\n"
                f"[bold]Care Plan Proposals:[/bold] {len(care_plan.proposals)} proposed\n\n"
                f"[dim]Key Dispatched Events:[/dim]\n"
                + "\n".join(
                    f"  • {k}: {v}"
                    for k, v in sorted(event_counts.items(), key=lambda x: -x[1])[:8]
                )
                + f"\n\n[dim]Final Care Plan Status:[/dim]\n  {care_plan.summary_str()}\n\n"
                f"[green]📁 Pre-consultation report saved to reports/[/green]\n"
                f"[green]🗄️  Persistent database saved to data/patient_memory.db[/green]",
                title="[bold blue]🏁 5-AGENT SIMULATION COMPLETE[/bold blue]",
                border_style="blue",
            )
        )
    else:
        print("\n=== SIMULATION COMPLETE ===")
        print(f"Peak Escalation: Level {care_plan.escalation_level}/3")
        print(f"Events: {len(events)}")
        print(f"Care Plan: {care_plan.summary_str()}")


if __name__ == "__main__":
    main()
