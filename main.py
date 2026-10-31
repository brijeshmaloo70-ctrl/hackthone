"""
main.py
Entry point: initialises all components and runs the 30-day chronic care simulation.
"""

import os
import sys
import logging

# -- Fix Windows console encoding --
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from datetime import datetime

# ── Ensure data/ directory exists BEFORE logging setup ────────────────────────
os.makedirs("data", exist_ok=True)

# ── Load environment variables first ──────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; environment vars must be set manually

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
    level=logging.WARNING,   # Suppress verbose debug output during demo
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
                "[bold green]Initialising AI Chronic Care Management System...[/bold green]\n\n"
                "[dim]Components: Memory Store · Care Plan · Event Bus · 3 AI Agents[/dim]",
                border_style="green",
            )
        )
    else:
        print("\n=== AI Chronic Care Management System ===\n")

    # ── 2. Initialise core components ────────────────────────────────────
    print_step("Memory Store", "SQLite patient memory initialised", "green")
    memory = PatientMemory(db_path=DB_CONFIG["path"])

    print_step("Care Plan", "Shared care plan created for Ramesh Kumar", "green")
    care_plan = initialize_care_plan(
        patient_id=PATIENT_PROFILE["id"],
        patient_name=PATIENT_PROFILE["name"],
        goals=CARE_GOALS,
        medications=ALL_MEDICATIONS,
        vitals_targets=CARE_GOALS["vitals"],
    )

    print_step("Event Bus", "Pub/sub event bus initialised", "green")
    event_bus = EventBus()

    # ── 3. Create agents ─────────────────────────────────────────────────
    print_step("Patient Agent", "Asha (Patient Agent) ready", "cyan")
    patient_agent = PatientAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Caregiver Agent", "ConnectAgent (Caregiver Agent) ready", "cyan")
    caregiver_agent = CaregiverAgent(
        care_plan=care_plan,
        memory=memory,
        event_bus=event_bus,
    )

    print_step("Clinician Agent", "MedInsightAgent (Clinician Agent) ready", "cyan")
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
    _print_final_summary(sim_summary, care_plan)

    # ── 9. Clean up ───────────────────────────────────────────────────────
    memory.close()
    if _rich_available:
        console.print("\n[bold green]✅ Demo complete! Thank you.[/bold green]\n")
    else:
        print("\nDemo complete!\n")


def print_step(component: str, message: str, color: str = "white") -> None:
    """Print a startup step."""
    if _rich_available:
        console.print(f"  [bold {color}]▶ {component}:[/bold {color}] {message}")
    else:
        print(f"  [{component}] {message}")


def _print_final_summary(summary: dict, care_plan) -> None:
    """Print the final simulation summary."""
    event_counts = summary.get("event_counts", {})

    if _rich_available:
        console.print()
        console.print(
            Panel(
                f"[bold]Simulation:[/bold]      30 days completed\n"
                f"[bold]Peak Escalation:[/bold]  Level {summary.get('peak_escalation', 0)}/3\n"
                f"[bold]Events fired:[/bold]     {sum(event_counts.values())} total across all types\n"
                f"[bold]WhatsApp messages:[/bold] {summary.get('whatsapp_messages', 0)} sent\n"
                f"[bold]Voice calls:[/bold]      {summary.get('voice_calls', 0)} initiated\n\n"
                f"[dim]Key Events:[/dim]\n"
                + "\n".join(
                    f"  • {k}: {v}"
                    for k, v in sorted(event_counts.items(), key=lambda x: -x[1])
                )
                + f"\n\n[dim]Final Care Plan:[/dim]\n  {care_plan.summary_str()}\n\n"
                f"[green]📁 Report saved to reports/[/green]\n"
                f"[green]🗄️  Database saved to data/patient_memory.db[/green]",
                title="[bold blue]🏁 SIMULATION COMPLETE[/bold blue]",
                border_style="blue",
            )
        )
    else:
        print("\n=== SIMULATION COMPLETE ===")
        print(f"Peak Escalation: {summary.get('peak_escalation', 0)}/3")
        print(f"Events: {sum(event_counts.values())}")
        print(f"Care Plan: {care_plan.summary_str()}")


if __name__ == "__main__":
    main()
