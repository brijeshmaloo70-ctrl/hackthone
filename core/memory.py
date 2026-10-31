"""
core/memory.py
Long-term patient memory store backed by SQLite.
Persists check-in history, vitals, medication adherence, mood, and social logs.
"""

from __future__ import annotations
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class PatientMemory:
    """
    SQLite-backed persistent memory for patient health data.
    All agents share this store for reading and writing.
    """

    def __init__(self, db_path: str = "data/patient_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ─── Schema ────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Create all tables if they don't exist."""
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  TEXT    NOT NULL,
                day         INTEGER NOT NULL,
                timestamp   TEXT    NOT NULL,
                language    TEXT    DEFAULT 'Hindi',
                mood        INTEGER,          -- 1-5
                energy      INTEGER,          -- 1-5
                pain_level  INTEGER,          -- 0-10
                symptoms    TEXT,             -- JSON list
                notes       TEXT,
                agent_response TEXT
            );

            CREATE TABLE IF NOT EXISTS vitals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                day             INTEGER NOT NULL,
                timestamp       TEXT    NOT NULL,
                bp_systolic     INTEGER,
                bp_diastolic    INTEGER,
                heart_rate      INTEGER,
                blood_glucose   REAL,
                weight          REAL,
                sleep_hours     REAL,
                activity_minutes INTEGER,
                notes           TEXT
            );

            CREATE TABLE IF NOT EXISTS medications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                day             INTEGER NOT NULL,
                timestamp       TEXT    NOT NULL,
                med_name        TEXT    NOT NULL,
                dose            TEXT,
                scheduled_time  TEXT,
                taken           INTEGER DEFAULT 1,  -- 1=taken, 0=missed
                notes           TEXT
            );

            CREATE TABLE IF NOT EXISTS social_logs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id          TEXT    NOT NULL,
                day                 INTEGER NOT NULL,
                timestamp           TEXT    NOT NULL,
                had_interaction     INTEGER DEFAULT 0,   -- 1=yes, 0=no
                interaction_type    TEXT,                -- family/friend/community/none
                duration_minutes    INTEGER DEFAULT 0,
                mood_after          INTEGER,             -- 1-5
                notes               TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  TEXT    NOT NULL,
                day         INTEGER NOT NULL,
                timestamp   TEXT    NOT NULL,
                event_type  TEXT    NOT NULL,
                description TEXT,
                severity    TEXT    DEFAULT 'info',
                agent_name  TEXT,
                resolved    INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_vitals_patient_day    ON vitals(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_checkins_patient_day  ON checkins(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_medications_patient_day ON medications(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_social_patient_day    ON social_logs(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_events_patient_day    ON events(patient_id, day);
            """
        )
        self._conn.commit()

    # ─── Check-ins ─────────────────────────────────────────────────────────

    def log_checkin(
        self,
        patient_id: str,
        day: int,
        mood: int,
        energy: int,
        pain_level: int,
        symptoms: List[str],
        notes: str = "",
        agent_response: str = "",
        language: str = "Hindi",
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO checkins
                (patient_id, day, timestamp, language, mood, energy, pain_level, symptoms, notes, agent_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                language,
                mood,
                energy,
                pain_level,
                json.dumps(symptoms, ensure_ascii=False),
                notes,
                agent_response,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Vitals ────────────────────────────────────────────────────────────

    def log_vitals(
        self,
        patient_id: str,
        day: int,
        bp_systolic: int,
        bp_diastolic: int,
        heart_rate: int,
        blood_glucose: float,
        weight: float,
        sleep_hours: float,
        activity_minutes: int,
        notes: str = "",
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO vitals
                (patient_id, day, timestamp, bp_systolic, bp_diastolic, heart_rate,
                 blood_glucose, weight, sleep_hours, activity_minutes, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                bp_systolic,
                bp_diastolic,
                heart_rate,
                blood_glucose,
                weight,
                sleep_hours,
                activity_minutes,
                notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Medications ───────────────────────────────────────────────────────

    def log_medication(
        self,
        patient_id: str,
        day: int,
        med_name: str,
        dose: str,
        scheduled_time: str,
        taken: bool,
        notes: str = "",
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO medications
                (patient_id, day, timestamp, med_name, dose, scheduled_time, taken, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                med_name,
                dose,
                scheduled_time,
                1 if taken else 0,
                notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Social ────────────────────────────────────────────────────────────

    def log_social(
        self,
        patient_id: str,
        day: int,
        had_interaction: bool,
        interaction_type: str = "none",
        duration_minutes: int = 0,
        mood_after: int = 3,
        notes: str = "",
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO social_logs
                (patient_id, day, timestamp, had_interaction, interaction_type,
                 duration_minutes, mood_after, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                1 if had_interaction else 0,
                interaction_type,
                duration_minutes,
                mood_after,
                notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Events ────────────────────────────────────────────────────────────

    def log_event(
        self,
        patient_id: str,
        day: int,
        event_type: str,
        description: str,
        severity: str = "info",
        agent_name: str = "system",
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO events
                (patient_id, day, timestamp, event_type, description, severity, agent_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                event_type,
                description,
                severity,
                agent_name,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Retrieval ─────────────────────────────────────────────────────────

    def get_history(self, patient_id: str, days: int = 30) -> Dict[str, List[Dict]]:
        """Return a full history dict for the last N days."""
        max_day = self._get_max_day(patient_id)
        min_day = max(1, max_day - days + 1)
        return {
            "vitals": self._fetch_rows(
                "SELECT * FROM vitals WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
            "checkins": self._fetch_rows(
                "SELECT * FROM checkins WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
            "medications": self._fetch_rows(
                "SELECT * FROM medications WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
            "social": self._fetch_rows(
                "SELECT * FROM social_logs WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
            "events": self._fetch_rows(
                "SELECT * FROM events WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
        }

    def get_trend(self, patient_id: str, metric: str, days: int = 7) -> Dict[str, Any]:
        """
        Compute basic trend statistics for a vital metric over the last N days.
        Returns: {values, average, min, max, trend_direction, trend_pct_change}
        """
        max_day = self._get_max_day(patient_id)
        min_day = max(1, max_day - days + 1)

        valid_metrics = {
            "bp_systolic", "bp_diastolic", "heart_rate",
            "blood_glucose", "weight", "sleep_hours", "activity_minutes",
        }
        if metric not in valid_metrics:
            return {"error": f"Unknown metric: {metric}"}

        rows = self._fetch_rows(
            f"SELECT day, {metric} FROM vitals WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
            (patient_id, min_day, max_day),
        )
        values = [r[metric] for r in rows if r[metric] is not None]

        if not values:
            return {"values": [], "average": None, "min": None, "max": None,
                    "trend_direction": "unknown", "trend_pct_change": 0}

        avg = sum(values) / len(values)
        mn = min(values)
        mx = max(values)

        # Simple linear trend: compare first-half avg vs second-half avg
        if len(values) >= 4:
            mid = len(values) // 2
            first_half_avg = sum(values[:mid]) / mid
            second_half_avg = sum(values[mid:]) / (len(values) - mid)
            pct_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg else 0
            if pct_change > 3:
                direction = "increasing"
            elif pct_change < -3:
                direction = "decreasing"
            else:
                direction = "stable"
        else:
            direction = "stable"
            pct_change = 0.0

        return {
            "metric": metric,
            "values": values,
            "days": days,
            "average": round(avg, 1),
            "min": round(mn, 1),
            "max": round(mx, 1),
            "trend_direction": direction,
            "trend_pct_change": round(pct_change, 1),
        }

    def get_medication_adherence(self, patient_id: str, days: int = 30) -> Dict[str, Any]:
        """Calculate medication adherence percentage over the past N days."""
        max_day = self._get_max_day(patient_id)
        min_day = max(1, max_day - days + 1)
        rows = self._fetch_rows(
            "SELECT taken FROM medications WHERE patient_id=? AND day BETWEEN ? AND ?",
            (patient_id, min_day, max_day),
        )
        if not rows:
            return {"adherence_pct": 100.0, "taken": 0, "missed": 0, "total": 0}
        total = len(rows)
        taken = sum(1 for r in rows if r["taken"] == 1)
        missed = total - taken
        return {
            "adherence_pct": round((taken / total) * 100, 1) if total else 100.0,
            "taken": taken,
            "missed": missed,
            "total": total,
        }

    def get_social_summary(self, patient_id: str, days: int = 7) -> Dict[str, Any]:
        """Summarise social interaction over the past N days."""
        max_day = self._get_max_day(patient_id)
        min_day = max(1, max_day - days + 1)
        rows = self._fetch_rows(
            "SELECT had_interaction, interaction_type, duration_minutes FROM social_logs "
            "WHERE patient_id=? AND day BETWEEN ? AND ?",
            (patient_id, min_day, max_day),
        )
        total_days = max_day - min_day + 1
        interaction_days = sum(1 for r in rows if r["had_interaction"] == 1)
        isolation_days = total_days - interaction_days
        return {
            "total_days": total_days,
            "interaction_days": interaction_days,
            "isolation_days": isolation_days,
            "isolation_pct": round((isolation_days / total_days) * 100, 1) if total_days else 0,
        }

    def get_all_vitals(self, patient_id: str) -> List[Dict]:
        """Return all vitals rows ordered by day."""
        return self._fetch_rows(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY day",
            (patient_id,),
        )

    def get_all_events(self, patient_id: str, severity: Optional[str] = None) -> List[Dict]:
        """Return all event rows, optionally filtered by severity."""
        if severity:
            return self._fetch_rows(
                "SELECT * FROM events WHERE patient_id=? AND severity=? ORDER BY day",
                (patient_id, severity),
            )
        return self._fetch_rows(
            "SELECT * FROM events WHERE patient_id=? ORDER BY day",
            (patient_id,),
        )

    # ─── Helpers ───────────────────────────────────────────────────────────

    def _fetch_rows(self, query: str, params: Tuple) -> List[Dict]:
        cur = self._conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def _get_max_day(self, patient_id: str) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT MAX(day) FROM vitals WHERE patient_id=?", (patient_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else 1

    def close(self) -> None:
        self._conn.close()
