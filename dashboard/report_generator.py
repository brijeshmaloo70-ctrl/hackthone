"""
dashboard/report_generator.py
Doctor-facing report generator.
Produces a rich text/markdown pre-visit clinical summary
with 30-day vitals table, adherence stats, key events, and recommendations.
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from core.care_plan import CarePlan
from core.memory import PatientMemory
from config.settings import PATIENT_PROFILE, CLINICIAN_PROFILE, VITAL_THRESHOLDS

console = Console()


class ReportGenerator:
    """
    Generates the doctor-facing pre-visit report.
    Output is both printed to terminal (with rich) and saved as a markdown file.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_doctor_report(
        self,
        patient_data: List[Dict[str, Any]],
        care_plan: CarePlan,
        memory: PatientMemory,
    ) -> str:
        """
        Generate the complete 30-day doctor report.
        Returns the full report as a string and saves it to disk.
        """
        patient_id = PATIENT_PROFILE["id"]
        patient_name = PATIENT_PROFILE["name"]
        doctor_name = CLINICIAN_PROFILE["name"]
        report_date = datetime.now().strftime("%B %d, %Y at %H:%M")

        # Gather statistics
        adherence = memory.get_medication_adherence(patient_id, days=30)
        social = memory.get_social_summary(patient_id, days=30)
        all_vitals = memory.get_all_vitals(patient_id)
        all_events = memory.get_all_events(patient_id)
        critical_events = memory.get_all_events(patient_id, severity="critical")
        warning_events = memory.get_all_events(patient_id, severity="warning")
        caregiver_alerts = care_plan.caregiver_alerts

        # Compute vitals stats
        bp_values = [v["bp_systolic"] for v in all_vitals if v.get("bp_systolic")]
        glucose_values = [v["blood_glucose"] for v in all_vitals if v.get("blood_glucose")]
        hr_values = [v["heart_rate"] for v in all_vitals if v.get("heart_rate")]
        weight_values = [v["weight"] for v in all_vitals if v.get("weight")]

        bp_avg = round(sum(bp_values) / len(bp_values), 1) if bp_values else 0
        bp_max = max(bp_values) if bp_values else 0
        bp_min = min(bp_values) if bp_values else 0
        glucose_avg = round(sum(glucose_values) / len(glucose_values), 1) if glucose_values else 0
        glucose_max = max(glucose_values) if glucose_values else 0
        hr_avg = round(sum(hr_values) / len(hr_values), 1) if hr_values else 0
        weight_start = weight_values[0] if weight_values else 72
        weight_end = weight_values[-1] if weight_values else 72
        weight_change = round(weight_end - weight_start, 1)

        # Social wellbeing score
        social_score = care_plan.social_wellbeing_score
        isolation_days = social["isolation_days"]

        # ── Print rich terminal report ───────────────────────────────────
        self._print_terminal_report(
            patient_name=patient_name,
            doctor_name=doctor_name,
            report_date=report_date,
            all_vitals=all_vitals,
            patient_data=patient_data,
            adherence=adherence,
            social=social,
            social_score=social_score,
            isolation_days=isolation_days,
            bp_avg=bp_avg, bp_max=bp_max, bp_min=bp_min,
            glucose_avg=glucose_avg, glucose_max=glucose_max,
            hr_avg=hr_avg,
            weight_start=weight_start, weight_end=weight_end, weight_change=weight_change,
            critical_events=critical_events,
            warning_events=warning_events,
            caregiver_alerts=caregiver_alerts,
            care_plan=care_plan,
        )

        # ── Generate markdown string ─────────────────────────────────────
        markdown = self._build_markdown_report(
            patient_name=patient_name,
            doctor_name=doctor_name,
            report_date=report_date,
            patient_data=patient_data,
            adherence=adherence,
            social=social,
            social_score=social_score,
            isolation_days=isolation_days,
            bp_avg=bp_avg, bp_max=bp_max, bp_min=bp_min,
            glucose_avg=glucose_avg, glucose_max=glucose_max,
            hr_avg=hr_avg,
            weight_start=weight_start, weight_end=weight_end, weight_change=weight_change,
            critical_events=critical_events,
            warning_events=warning_events,
            caregiver_alerts=caregiver_alerts,
            care_plan=care_plan,
        )

        # ── Save to disk ─────────────────────────────────────────────────
        filename = f"doctor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        console.print(f"\n[green]✅ Doctor report saved to: {filepath}[/green]")
        return markdown

    # ─── Terminal Report ───────────────────────────────────────────────────

    def _print_terminal_report(self, **kwargs) -> None:
        """Print the full rich terminal report."""
        patient_name = kwargs["patient_name"]
        doctor_name = kwargs["doctor_name"]
        report_date = kwargs["report_date"]
        all_vitals = kwargs["all_vitals"]
        patient_data = kwargs["patient_data"]
        adherence = kwargs["adherence"]
        social = kwargs["social"]
        social_score = kwargs["social_score"]
        isolation_days = kwargs["isolation_days"]
        bp_avg = kwargs["bp_avg"]
        bp_max = kwargs["bp_max"]
        bp_min = kwargs["bp_min"]
        glucose_avg = kwargs["glucose_avg"]
        glucose_max = kwargs["glucose_max"]
        hr_avg = kwargs["hr_avg"]
        weight_start = kwargs["weight_start"]
        weight_end = kwargs["weight_end"]
        weight_change = kwargs["weight_change"]
        critical_events = kwargs["critical_events"]
        warning_events = kwargs["warning_events"]
        caregiver_alerts = kwargs["caregiver_alerts"]
        care_plan = kwargs["care_plan"]

        console.print()
        console.rule("[bold blue]DOCTOR PRE-VISIT REPORT[/bold blue]", characters="═")

        # Header
        console.print(
            Panel(
                f"[bold]Patient:[/bold]   {patient_name}, {PATIENT_PROFILE['age']}M\n"
                f"[bold]Conditions:[/bold] {', '.join(PATIENT_PROFILE['conditions'])}\n"
                f"[bold]Allergies:[/bold]  {', '.join(PATIENT_PROFILE['allergies'])}\n"
                f"[bold]Doctor:[/bold]     {doctor_name}\n"
                f"[bold]Report Date:[/bold] {report_date}\n"
                f"[bold]Period:[/bold]     30-day monitoring (Nov 1–30, 2024)",
                title="[bold cyan]📋 PRE-VISIT CLINICAL SUMMARY[/bold cyan]",
                border_style="cyan",
            )
        )

        # Vitals trend table
        console.print("\n[bold cyan]📊 30-DAY VITALS TREND[/bold cyan]")
        vtable = Table(show_header=True, header_style="bold white", border_style="dim")
        vtable.add_column("Day", justify="center", style="dim")
        vtable.add_column("Date", style="dim")
        vtable.add_column("BP (sys/dia)", justify="center")
        vtable.add_column("Heart Rate", justify="center")
        vtable.add_column("Glucose", justify="center")
        vtable.add_column("Weight", justify="center")
        vtable.add_column("Meds", justify="center")
        vtable.add_column("Social", justify="center")
        vtable.add_column("Mood", justify="center")

        for vitals_row in all_vitals:
            day_num = vitals_row.get("day", 0)
            # Get patient data for this day
            pd_row = next((pd for pd in patient_data if pd["day"] == day_num), {})
            bp_sys = vitals_row.get("bp_systolic", 0)
            bp_dia = vitals_row.get("bp_diastolic", 0)
            hr = vitals_row.get("heart_rate", 0)
            glucose = vitals_row.get("blood_glucose", 0)
            weight = vitals_row.get("weight", 0)
            med_taken = pd_row.get("medication_taken", True)
            social_int = pd_row.get("social_interaction", True)
            mood = pd_row.get("mood", 3)
            date_str = pd_row.get("date", "")

            # Colour BP
            bp_color = "green"
            if bp_sys >= VITAL_THRESHOLDS["bp_systolic"]["danger_high"]:
                bp_color = "bold red"
            elif bp_sys >= VITAL_THRESHOLDS["bp_systolic"]["warning_high"]:
                bp_color = "yellow"

            # Colour glucose
            g_color = "green"
            if glucose >= VITAL_THRESHOLDS["blood_glucose"]["danger_high"]:
                g_color = "bold red"
            elif glucose >= VITAL_THRESHOLDS["blood_glucose"]["warning_high"]:
                g_color = "yellow"

            vtable.add_row(
                str(day_num),
                date_str[5:] if date_str else "",  # Show MM-DD
                f"[{bp_color}]{bp_sys}/{bp_dia}[/{bp_color}]",
                str(hr),
                f"[{g_color}]{glucose}[/{g_color}]",
                str(weight),
                "✅" if med_taken else "[red]❌[/red]",
                "✅" if social_int else "[yellow]—[/yellow]",
                "⭐" * mood,
            )

        console.print(vtable)

        # Summary stats
        adh_pct = adherence["adherence_pct"]
        adh_color = "green" if adh_pct >= 90 else ("yellow" if adh_pct >= 75 else "red")

        console.print(
            Panel(
                f"[bold]Average BP:[/bold]         {bp_avg} mmHg  "
                f"(Max: [bold red]{bp_max}[/bold red], Min: {bp_min})\n"
                f"[bold]Average Glucose:[/bold]    {glucose_avg} mg/dL  "
                f"(Max: [bold red]{glucose_max}[/bold red])\n"
                f"[bold]Average Heart Rate:[/bold] {hr_avg} bpm\n"
                f"[bold]Weight Change:[/bold]      {weight_start} → {weight_end} kg  "
                f"({'[red]+' if weight_change > 0 else '[green]'}{weight_change} kg)\n\n"
                f"[bold]Medication Adherence:[/bold]  [{adh_color}]{adh_pct}%[/{adh_color}]  "
                f"(Taken: {adherence['taken']}, Missed: [red]{adherence['missed']}[/red])\n\n"
                f"[bold]Social Wellbeing:[/bold]   {social['interaction_days']}/30 interaction days  "
                f"(Isolated: [yellow]{isolation_days}[/yellow] days)  "
                f"Score: {social_score}/5\n\n"
                f"[bold]Peak Escalation Level:[/bold] "
                f"[{'red' if care_plan.escalation_level >= 3 else 'yellow'}]"
                f"{care_plan.escalation_level}/3[/]\n"
                f"[bold]Critical Events:[/bold]    {len(critical_events)}\n"
                f"[bold]Warning Events:[/bold]     {len(warning_events)}\n"
                f"[bold]Caregiver Alerts:[/bold]   {len(caregiver_alerts)}",
                title="[bold cyan]📈 30-DAY SUMMARY STATISTICS[/bold cyan]",
                border_style="cyan",
            )
        )

        # Key events
        if critical_events or warning_events:
            console.print("\n[bold red]🚨 KEY CLINICAL EVENTS[/bold red]")
            etable = Table(show_header=True, header_style="bold white", border_style="dim")
            etable.add_column("Day", justify="center", style="dim", width=5)
            etable.add_column("Severity", width=10)
            etable.add_column("Event", width=50)
            etable.add_column("Agent", width=20)

            shown = 0
            for event in sorted(critical_events + warning_events, key=lambda e: e.get("day", 0)):
                if shown >= 12:
                    break
                sev = event.get("severity", "info")
                sev_str = f"[bold red]{sev.upper()}[/bold red]" if sev == "critical" else f"[yellow]{sev.upper()}[/yellow]"
                etable.add_row(
                    str(event.get("day", "?")),
                    sev_str,
                    str(event.get("description", ""))[:80],
                    str(event.get("agent_name", "system")),
                )
                shown += 1
            console.print(etable)

        # Recommendations
        console.print(
            Panel(
                f"1. [bold]Antihypertensive Review:[/bold] BP consistently elevated (avg {bp_avg} mmHg). "
                f"Consider intensifying regimen.\n"
                f"2. [bold]Glycaemic Control:[/bold] Mean glucose {glucose_avg} mg/dL; request HbA1c. "
                f"Consider endocrinology referral.\n"
                f"3. [bold]Medication Adherence:[/bold] Adherence {adh_pct}% — "
                f"{'CRITICAL: Pill organiser / daily alerts needed' if adh_pct < 80 else 'counsel on importance'}\n"
                f"4. [bold]Social Prescription:[/bold] {isolation_days} days of isolation detected — "
                f"screen for depression; community programme referral.\n"
                f"5. [bold]Weight Management:[/bold] +{weight_change} kg in 30 days — dietary review.\n"
                f"6. [bold]Physical Activity:[/bold] Activity declining — physiotherapy referral.\n"
                f"7. [bold]Family Involvement:[/bold] {len(caregiver_alerts)} alerts sent to family — "
                f"invite caregiver to next appointment.",
                title="[bold green]📋 CLINICAL RECOMMENDATIONS[/bold green]",
                border_style="green",
            )
        )

    # ─── Markdown Report ───────────────────────────────────────────────────

    def _build_markdown_report(self, **kwargs) -> str:
        """Build a clean markdown version of the report."""
        patient_name = kwargs["patient_name"]
        doctor_name = kwargs["doctor_name"]
        report_date = kwargs["report_date"]
        patient_data = kwargs["patient_data"]
        adherence = kwargs["adherence"]
        social = kwargs["social"]
        social_score = kwargs["social_score"]
        isolation_days = kwargs["isolation_days"]
        bp_avg = kwargs["bp_avg"]
        bp_max = kwargs["bp_max"]
        bp_min = kwargs["bp_min"]
        glucose_avg = kwargs["glucose_avg"]
        glucose_max = kwargs["glucose_max"]
        hr_avg = kwargs["hr_avg"]
        weight_start = kwargs["weight_start"]
        weight_end = kwargs["weight_end"]
        weight_change = kwargs["weight_change"]
        critical_events = kwargs["critical_events"]
        warning_events = kwargs["warning_events"]
        caregiver_alerts = kwargs["caregiver_alerts"]
        care_plan = kwargs["care_plan"]

        adh_pct = adherence["adherence_pct"]

        lines = [
            f"# Pre-Visit Clinical Summary",
            f"",
            f"**Patient:** {patient_name}, {PATIENT_PROFILE['age']}M  ",
            f"**Conditions:** {', '.join(PATIENT_PROFILE['conditions'])}  ",
            f"**Allergies:** {', '.join(PATIENT_PROFILE['allergies'])}  ",
            f"**Doctor:** {doctor_name}  ",
            f"**Report Date:** {report_date}  ",
            f"**Period:** 30-day monitoring (Nov 1–30, 2024)  ",
            f"",
            f"---",
            f"",
            f"## 30-Day Vitals Trend",
            f"",
            f"| Day | Date | BP (sys/dia) | HR | Glucose | Weight | Meds | Social | Mood |",
            f"|-----|------|-------------|-----|---------|--------|------|--------|------|",
        ]

        for pd_row in patient_data:
            day_num = pd_row["day"]
            bp_sys = pd_row.get("bp_systolic", 0)
            bp_dia = pd_row.get("bp_diastolic", 0)
            hr = pd_row.get("heart_rate", 0)
            glucose = pd_row.get("blood_glucose", 0)
            weight = pd_row.get("weight", 0)
            med_taken = pd_row.get("medication_taken", True)
            social_int = pd_row.get("social_interaction", True)
            mood = pd_row.get("mood", 3)
            date_str = pd_row.get("date", "")

            bp_flag = " ⚠️" if bp_sys >= 160 else (" 📈" if bp_sys >= 150 else "")
            g_flag = " 🆘" if glucose >= 300 else (" ⚠️" if glucose >= 250 else "")
            lines.append(
                f"| {day_num:2d} | {date_str[5:]} | {bp_sys}/{bp_dia}{bp_flag} | "
                f"{hr} | {glucose}{g_flag} | {weight} | "
                f"{'✅' if med_taken else '❌'} | {'✅' if social_int else '—'} | "
                f"{'⭐' * mood} |"
            )

        lines += [
            f"",
            f"## Summary Statistics",
            f"",
            f"### Vitals",
            f"- **Average BP:** {bp_avg} mmHg (Max: {bp_max}, Min: {bp_min})",
            f"- **Average Blood Glucose:** {glucose_avg} mg/dL (Max: {glucose_max})",
            f"- **Average Heart Rate:** {hr_avg} bpm",
            f"- **Weight Change:** {weight_start} → {weight_end} kg ({'+' if weight_change > 0 else ''}{weight_change} kg)",
            f"",
            f"### Medication",
            f"- **30-Day Adherence:** {adh_pct}% {'✅' if adh_pct >= 90 else '⚠️' if adh_pct >= 75 else '🆘'}",
            f"- **Doses Taken:** {adherence['taken']}",
            f"- **Doses Missed:** {adherence['missed']}",
            f"",
            f"### Social Wellbeing",
            f"- **Social Interaction Days:** {social['interaction_days']}/30",
            f"- **Isolation Days:** {isolation_days}",
            f"- **Wellbeing Score:** {social_score}/5",
            f"",
            f"### Clinical Events",
            f"- **Peak Escalation Level:** {care_plan.escalation_level}/3",
            f"- **Critical Events:** {len(critical_events)}",
            f"- **Warning Events:** {len(warning_events)}",
            f"- **Caregiver Alerts Sent:** {len(caregiver_alerts)}",
            f"",
            f"---",
            f"",
            f"## Key Clinical Events",
            f"",
        ]

        for event in sorted(
            critical_events + warning_events, key=lambda e: e.get("day", 0)
        )[:15]:
            sev = event.get("severity", "info").upper()
            desc = event.get("description", "")[:120]
            lines.append(f"- **[Day {event.get('day', '?')}] {sev}:** {desc}")

        lines += [
            f"",
            f"---",
            f"",
            f"## Clinical Recommendations",
            f"",
            f"1. **Antihypertensive Review:** BP consistently elevated (avg {bp_avg} mmHg). Intensify regimen.",
            f"2. **Glycaemic Control:** Mean glucose {glucose_avg} mg/dL. Request HbA1c. Consider endocrinology.",
            f"3. **Medication Adherence:** {adh_pct}% — {'Critical: implement pill organiser' if adh_pct < 80 else 'counsel on importance'}.",
            f"4. **Social Prescription:** {isolation_days} days isolation. Screen for depression; community referral.",
            f"5. **Weight Management:** +{weight_change} kg in 30 days. Dietary review.",
            f"6. **Physical Activity:** Physiotherapy referral recommended.",
            f"7. **Family Involvement:** Invite caregiver to next appointment.",
            f"",
            f"---",
            f"*Generated by MedInsightAgent AI Clinical Support System*  ",
            f"*{report_date}*",
        ]

        return "\n".join(lines)
