"""
simulation/patient_data.py
Generates a realistic 30-day simulated patient timeline.

Phase 1 (Days 1-10):  Stable — BP ~140/90, glucose ~180
Phase 2 (Days 11-20): Gradual deterioration — BP rising, some missed meds
Phase 3 (Days 21-27): Dangerous trend — BP 165-175, glucose 280-310, isolation
Phase 4 (Days 28-30): Escalation, intervention, beginning stabilisation
"""

from __future__ import annotations
import random
from datetime import date, timedelta
from typing import Any, Dict, List


def generate_30_day_timeline(
    start_date_str: str = "2024-11-01",
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generate a 30-day patient health timeline for Ramesh Kumar.
    Returns a list of 30 daily records.
    """
    random.seed(seed)
    start = date.fromisoformat(start_date_str)
    timeline: List[Dict[str, Any]] = []

    for day in range(1, 31):
        current_date = start + timedelta(days=day - 1)
        record = _generate_day(day, current_date)
        timeline.append(record)

    return timeline


def _generate_day(day: int, current_date: date) -> Dict[str, Any]:
    """Generate health data for a single day based on the simulation phase."""

    # ─── Phase 1: Stable (Days 1–10) ───────────────────────────────────────
    if 1 <= day <= 10:
        bp_systolic = int(random.gauss(140, 4))      # Mean 140, small variance
        bp_diastolic = int(random.gauss(88, 3))
        heart_rate = int(random.gauss(74, 4))
        blood_glucose = round(random.gauss(175, 15), 1)
        weight = round(72.0 + random.gauss(0, 0.2), 1)
        mood = random.choices([3, 4, 5], weights=[20, 50, 30])[0]
        medication_taken = random.random() > 0.05   # 95% adherence
        social_interaction = random.random() > 0.2   # 80% social days
        sleep_hours = round(random.gauss(7.0, 0.5), 1)
        activity_minutes = int(random.gauss(35, 8))
        symptoms = _pick_symptoms(severity="none")

    # ─── Phase 2: Gradual Deterioration (Days 11–20) ───────────────────────
    elif 11 <= day <= 20:
        drift = (day - 10) * 1.2   # Progressive worsening
        bp_systolic = int(random.gauss(143 + drift, 5))
        bp_diastolic = int(random.gauss(90 + drift * 0.3, 3))
        heart_rate = int(random.gauss(76 + drift * 0.2, 5))
        blood_glucose = round(random.gauss(190 + drift * 3, 20), 1)
        weight = round(72.0 + (day - 10) * 0.15 + random.gauss(0, 0.2), 1)
        mood = random.choices([2, 3, 4], weights=[25, 55, 20])[0]
        medication_taken = random.random() > (0.10 + (day - 10) * 0.02)  # Adherence drops
        social_interaction = random.random() > (0.25 + (day - 10) * 0.03)
        sleep_hours = round(random.gauss(6.5, 0.7), 1)
        activity_minutes = max(0, int(random.gauss(25 - drift, 8)))
        symptoms = _pick_symptoms(severity="mild", day=day)

    # ─── Phase 3: Dangerous Trend (Days 21–27) ─────────────────────────────
    elif 21 <= day <= 27:
        danger_drift = (day - 20) * 2.5
        bp_systolic = int(random.gauss(162 + danger_drift * 0.5, 4))
        bp_diastolic = int(random.gauss(96 + danger_drift * 0.3, 3))
        heart_rate = int(random.gauss(82 + danger_drift * 0.3, 5))
        blood_glucose = round(random.gauss(285 + danger_drift, 20), 1)
        weight = round(73.5 + random.gauss(0, 0.3), 1)
        mood = random.choices([1, 2, 3], weights=[35, 45, 20])[0]
        medication_taken = random.random() > 0.55   # ~45% miss rate
        social_interaction = random.random() > 0.75  # Mostly isolated
        sleep_hours = round(random.gauss(5.5, 0.8), 1)
        activity_minutes = max(0, int(random.gauss(10, 5)))
        symptoms = _pick_symptoms(severity="serious", day=day)

    # ─── Phase 4: Intervention & Stabilisation (Days 28–30) ────────────────
    else:
        recovery_drift = (day - 27) * 3
        bp_systolic = int(random.gauss(175 - recovery_drift, 5))
        bp_diastolic = int(random.gauss(102 - recovery_drift * 0.4, 3))
        heart_rate = int(random.gauss(85 - recovery_drift * 0.2, 4))
        blood_glucose = round(random.gauss(310 - recovery_drift * 5, 20), 1)
        weight = round(73.2 + random.gauss(0, 0.2), 1)
        mood = 2 if day == 28 else 3
        medication_taken = random.random() > 0.15 if day >= 29 else random.random() > 0.6
        social_interaction = True if day >= 29 else False  # Family intervenes
        sleep_hours = round(random.gauss(6.0, 0.5), 1)
        activity_minutes = max(0, int(random.gauss(8, 4)))
        symptoms = _pick_symptoms(severity="critical" if day == 28 else "serious")

    # Clamp values to physiologically plausible ranges
    bp_systolic = max(90, min(200, bp_systolic))
    bp_diastolic = max(50, min(120, bp_diastolic))
    heart_rate = max(45, min(130, heart_rate))
    blood_glucose = max(60, min(400, blood_glucose))
    sleep_hours = max(3, min(12, sleep_hours))
    activity_minutes = max(0, min(120, activity_minutes))
    mood = max(1, min(5, mood))

    return {
        "day": day,
        "date": current_date.isoformat(),
        "phase": _get_phase_name(day),
        # Vitals
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "heart_rate": heart_rate,
        "blood_glucose": blood_glucose,
        "weight": weight,
        # Lifestyle
        "sleep_hours": sleep_hours,
        "activity_minutes": activity_minutes,
        "mood": mood,
        "social_interaction": social_interaction,
        "symptoms": symptoms,
        # Medication
        "medication_taken": medication_taken,
    }


def _get_phase_name(day: int) -> str:
    if day <= 10:
        return "stable"
    elif day <= 20:
        return "deteriorating"
    elif day <= 27:
        return "dangerous"
    else:
        return "intervention"


def _pick_symptoms(
    severity: str = "none", day: int = 0
) -> List[str]:
    """Return a list of symptoms based on severity."""
    none_symptoms: List[str] = []
    mild_symptoms = ["mild fatigue", "occasional headache", "slight dizziness"]
    serious_symptoms = [
        "persistent headache",
        "dizziness",
        "fatigue",
        "blurred vision",
        "frequent urination",
        "excessive thirst",
    ]
    critical_symptoms = [
        "severe headache",
        "chest tightness",
        "breathlessness",
        "dizziness",
        "nausea",
        "blurred vision",
    ]

    if severity == "none":
        return random.choices([[], none_symptoms], weights=[85, 15])[0]

    elif severity == "mild":
        pool = mild_symptoms
        count = random.choices([0, 1, 2], weights=[60, 30, 10])[0]
        return random.sample(pool, min(count, len(pool)))

    elif severity == "serious":
        pool = serious_symptoms
        count = random.choices([1, 2, 3], weights=[30, 50, 20])[0]
        return random.sample(pool, min(count, len(pool)))

    elif severity == "critical":
        pool = critical_symptoms
        count = random.choices([2, 3, 4], weights=[30, 50, 20])[0]
        return random.sample(pool, min(count, len(pool)))

    return []


def get_day_data(timeline: List[Dict[str, Any]], day: int) -> Dict[str, Any]:
    """Retrieve data for a specific day (1-indexed)."""
    for record in timeline:
        if record["day"] == day:
            return record
    raise ValueError(f"Day {day} not found in timeline.")


def compute_adherence(timeline: List[Dict[str, Any]], up_to_day: int) -> float:
    """Compute medication adherence % up to a given day."""
    subset = [d for d in timeline if d["day"] <= up_to_day]
    if not subset:
        return 100.0
    taken = sum(1 for d in subset if d.get("medication_taken", True))
    return round((taken / len(subset)) * 100, 1)
