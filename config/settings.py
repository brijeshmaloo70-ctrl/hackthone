"""
config/settings.py
All configuration, thresholds, language settings for the Chronic Care AI system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# Patient Profile
# ─────────────────────────────────────────────────────────────────────────────
PATIENT_PROFILE = {
    "id": "patient_001",
    "name": "Ramesh Kumar",
    "age": 78,
    "gender": "Male",
    "languages": ["Hindi", "English"],
    "primary_language": "Hindi",
    "phone": "+91-9876543210",
    "emergency_contact": "+91-9876543211",
    "address": "C-14, Sector 22, Noida, Uttar Pradesh",
    "conditions": ["Hypertension", "Type 2 Diabetes"],
    "allergies": ["Penicillin", "Sulfa drugs"],
    "doctor_name": "Dr. Anjali Sharma",
    "doctor_phone": "+91-9876543212",
    "hospital": "Apollo Hospital, Noida",
    "next_appointment": "Day 30",
}

CAREGIVER_PROFILE = {
    "name": "Suresh Kumar",
    "relation": "Son",
    "phone": "+91-9876543211",
    "email": "suresh.kumar@gmail.com",
    "location": "Delhi",
    "preferred_language": "English",
}

CLINICIAN_PROFILE = {
    "name": "Dr. Anjali Sharma",
    "specialty": "General Medicine & Geriatrics",
    "phone": "+91-9876543212",
    "email": "dr.anjali@apollo.com",
    "preferred_language": "English",
}


# ─────────────────────────────────────────────────────────────────────────────
# Vital Thresholds
# ─────────────────────────────────────────────────────────────────────────────
VITAL_THRESHOLDS = {
    "bp_systolic": {
        "danger_high": 160,
        "warning_high": 150,
        "normal_high": 140,
        "normal_low": 100,
        "warning_low": 95,
        "danger_low": 90,
    },
    "bp_diastolic": {
        "danger_high": 100,
        "warning_high": 95,
        "normal_high": 90,
        "normal_low": 60,
        "danger_low": 50,
    },
    "heart_rate": {
        "danger_high": 120,
        "warning_high": 100,
        "normal_high": 90,
        "normal_low": 60,
        "warning_low": 55,
        "danger_low": 50,
    },
    "blood_glucose": {
        "danger_high": 300,
        "warning_high": 250,
        "normal_high": 180,
        "normal_low": 80,
        "warning_low": 70,
        "danger_low": 60,
    },
    "weight_change_kg": {
        "alert_gain": 2.0,  # 2kg gain in a week
        "alert_loss": 2.0,  # 2kg loss in a week
    },
    "sleep_hours": {
        "min_healthy": 6,
        "max_healthy": 9,
    },
    "activity_minutes": {
        "min_daily": 20,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Medication Schedule
# ─────────────────────────────────────────────────────────────────────────────
MEDICATION_SCHEDULE = {
    "morning": [
        {
            "name": "Amlodipine",
            "dose": "5mg",
            "purpose": "Blood pressure control",
            "time": "08:00",
        },
        {
            "name": "Metformin",
            "dose": "500mg",
            "purpose": "Blood sugar control",
            "time": "08:30",
        },
        {
            "name": "Aspirin",
            "dose": "75mg",
            "purpose": "Blood thinner / cardiac protection",
            "time": "08:30",
        },
    ],
    "afternoon": [
        {
            "name": "Metformin",
            "dose": "500mg",
            "purpose": "Blood sugar control",
            "time": "13:30",
        },
    ],
    "evening": [
        {
            "name": "Losartan",
            "dose": "50mg",
            "purpose": "Blood pressure control",
            "time": "20:00",
        },
        {
            "name": "Glimepiride",
            "dose": "2mg",
            "purpose": "Blood sugar control",
            "time": "20:00",
        },
        {
            "name": "Atorvastatin",
            "dose": "20mg",
            "purpose": "Cholesterol control",
            "time": "21:00",
        },
    ],
}

ALL_MEDICATIONS = [
    med
    for slot in MEDICATION_SCHEDULE.values()
    for med in slot
]


# ─────────────────────────────────────────────────────────────────────────────
# Agent Configuration
# ─────────────────────────────────────────────────────────────────────────────
AGENT_CONFIG = {
    "patient_agent": {
        "name": "Asha",
        "persona": "Warm, caring, elderly-friendly AI health companion",
        "check_in_times": ["09:00", "14:00", "21:00"],
        "checkin_frequency_days": 1,
        "isolation_threshold_days": 3,  # No social interaction for 3 days = isolation
    },
    "caregiver_agent": {
        "name": "ConnectAgent",
        "weekly_summary_day": "Sunday",
        "urgent_notification_delay_minutes": 5,
    },
    "clinician_agent": {
        "name": "MedInsightAgent",
        "trend_window_days": 7,
        "visit_preparation_days_before": 3,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Care Goals
# ─────────────────────────────────────────────────────────────────────────────
CARE_GOALS = {
    "vitals": {
        "bp_systolic_target": "120-140 mmHg",
        "bp_diastolic_target": "70-90 mmHg",
        "heart_rate_target": "60-90 bpm",
        "blood_glucose_target": "100-180 mg/dL",
        "weight_target": "72 kg",
    },
    "lifestyle": {
        "activity_minutes_daily": 30,
        "sleep_hours_nightly": 7,
        "social_interactions_weekly": 5,
    },
    "medication": {
        "adherence_target_percent": 95,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Escalation Levels
# ─────────────────────────────────────────────────────────────────────────────
ESCALATION_LEVELS = {
    0: "Normal — All vitals stable",
    1: "Watch — One vital slightly out of range",
    2: "Warning — Multiple vitals concerning, trend worsening",
    3: "CRITICAL — Immediate medical attention required",
}

ESCALATION_COLORS = {
    0: "green",
    1: "yellow",
    2: "orange",
    3: "red",
}


# ─────────────────────────────────────────────────────────────────────────────
# LLM Settings
# ─────────────────────────────────────────────────────────────────────────────
LLM_CONFIG = {
    # Informational only — the real model list lives in core/llm.py / GEMINI_MODEL env var.
    "model": "gemini-flash-lite-latest",
    "temperature": 0.7,
    "max_output_tokens": 1024,
    "timeout_seconds": 30,
}


# ─────────────────────────────────────────────────────────────────────────────
# Database Settings
# ─────────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "path": "data/patient_memory.db",
    "backup_path": "data/backups/",
}


# ─────────────────────────────────────────────────────────────────────────────
# Demo / Simulation Settings
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CONFIG = {
    "total_days": 30,
    "start_date": "2024-11-01",
    "escalation_day": 22,
    "intervention_day": 28,
    "doctor_visit_day": 30,
    "print_delay_seconds": 0.05,  # Small delay between output lines for effect
}
