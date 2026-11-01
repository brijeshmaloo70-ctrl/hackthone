"""
core/memory.py
Long-term patient memory store backed by SQLite.
Persists check-in history, vitals, medication adherence, mood, social logs,
caregiver actions, care plan proposals, and contextual retrieval for agents.
"""

from __future__ import annotations
import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class PatientMemory:
    """
    SQLite-backed persistent longitudinal memory for patient health data.
    Provides structured relational storage, chronological event timelines,
    and contextual retrieval layers for multi-agent coordination.
    """

    def __init__(self, db_path: str = "data/patient_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ─── Schema ────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Create all tables and indices if they do not exist."""
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id     TEXT    NOT NULL,
                day            INTEGER NOT NULL,
                timestamp      TEXT    NOT NULL,
                language       TEXT    DEFAULT 'Hindi',
                mood           INTEGER,          -- 1-5
                energy         INTEGER,          -- 1-5
                pain_level     INTEGER,          -- 0-10
                symptoms       TEXT,             -- JSON list
                notes          TEXT,
                agent_response TEXT
            );

            CREATE TABLE IF NOT EXISTS vitals (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id       TEXT    NOT NULL,
                day              INTEGER NOT NULL,
                timestamp        TEXT    NOT NULL,
                bp_systolic      INTEGER,
                bp_diastolic     INTEGER,
                heart_rate       INTEGER,
                blood_glucose    REAL,
                weight           REAL,
                sleep_hours      REAL,
                activity_minutes INTEGER,
                notes            TEXT
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

            CREATE TABLE IF NOT EXISTS caregiver_actions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      TEXT    NOT NULL,
                day             INTEGER NOT NULL,
                timestamp       TEXT    NOT NULL,
                caregiver_name  TEXT    NOT NULL,
                alert_id        TEXT,
                action_taken    TEXT    NOT NULL,
                notes           TEXT
            );

            CREATE TABLE IF NOT EXISTS caregiver_alerts (
                alert_id        TEXT    PRIMARY KEY,
                patient_id      TEXT    NOT NULL,
                day             INTEGER NOT NULL,
                timestamp       TEXT    NOT NULL,
                urgency         TEXT    NOT NULL,
                source          TEXT,
                message         TEXT    NOT NULL,
                acknowledged    INTEGER DEFAULT 0,
                action_taken    TEXT,
                notes           TEXT,
                acknowledged_at TEXT
            );

            CREATE TABLE IF NOT EXISTS care_plan_proposals (
                id                         TEXT    PRIMARY KEY,
                patient_id                 TEXT    NOT NULL,
                day                        INTEGER NOT NULL,
                created_at                 TEXT    NOT NULL,
                agent_name                 TEXT    NOT NULL,
                category                   TEXT    NOT NULL,
                old_value                  TEXT,
                proposed_value             TEXT,
                reason                     TEXT,
                status                     TEXT    DEFAULT 'pending_review',
                requires_clinical_approval INTEGER DEFAULT 1,
                reviewer                   TEXT,
                reviewed_at                TEXT
            );

            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id     TEXT    NOT NULL,
                task_type      TEXT    NOT NULL,
                scheduled_time TEXT    NOT NULL,
                executed_at    TEXT,
                status         TEXT    DEFAULT 'pending',
                payload        TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_vitals_patient_day        ON vitals(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_checkins_patient_day      ON checkins(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_medications_patient_day    ON medications(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_social_patient_day        ON social_logs(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_events_patient_day        ON events(patient_id, day);
            CREATE INDEX IF NOT EXISTS idx_cg_actions_patient        ON caregiver_actions(patient_id, day);
            """
        )
        self._conn.commit()

    # ─── Logging Methods ───────────────────────────────────────────────────

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

    def log_caregiver_action(
        self,
        patient_id: str,
        caregiver_name: str,
        action_taken: str,
        notes: str = "",
        day: int = 0,
        alert_id: Optional[str] = None,
    ) -> int:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO caregiver_actions
                (patient_id, day, timestamp, caregiver_name, alert_id, action_taken, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                day,
                datetime.now().isoformat(),
                caregiver_name,
                alert_id,
                action_taken,
                notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Caregiver alerts (persistent, so they survive server restarts) ────

    def add_caregiver_alert(
        self,
        patient_id: str,
        day: int,
        urgency: str,
        message: str,
        source: str = "ConnectAgent",
    ) -> Dict[str, Any]:
        alert = {
            "alert_id": f"alert_{uuid.uuid4().hex[:10]}",
            "patient_id": patient_id,
            "day": day,
            "timestamp": datetime.now().isoformat(),
            "urgency": urgency,
            "source": source,
            "message": message,
            "acknowledged": False,
            "action_taken": None,
            "notes": None,
            "acknowledged_at": None,
        }
        self._conn.execute(
            """INSERT INTO caregiver_alerts
               (alert_id, patient_id, day, timestamp, urgency, source, message)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (alert["alert_id"], patient_id, day, alert["timestamp"], urgency, source, message),
        )
        self._conn.commit()
        return alert

    def get_caregiver_alerts(self, patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Newest first. Unacknowledged critical alerts are what the UI surfaces first."""
        rows = self._fetch_rows(
            "SELECT * FROM caregiver_alerts WHERE patient_id=? ORDER BY timestamp DESC LIMIT ?",
            (patient_id, limit),
        )
        for r in rows:
            r["acknowledged"] = bool(r["acknowledged"])
        return rows

    def get_caregiver_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        rows = self._fetch_rows("SELECT * FROM caregiver_alerts WHERE alert_id=?", (alert_id,))
        if not rows:
            return None
        rows[0]["acknowledged"] = bool(rows[0]["acknowledged"])
        return rows[0]

    def acknowledge_caregiver_alert(self, alert_id: str, action_taken: str, notes: str = "") -> bool:
        cur = self._conn.execute(
            """UPDATE caregiver_alerts
               SET acknowledged=1, action_taken=?, notes=?, acknowledged_at=?
               WHERE alert_id=?""",
            (action_taken, notes, datetime.now().isoformat(), alert_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_caregiver_actions(self, patient_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._fetch_rows(
            "SELECT * FROM caregiver_actions WHERE patient_id=? ORDER BY day DESC, id DESC LIMIT ?",
            (patient_id, limit),
        )

    # ─── Contextual & Semantic Retrieval Layer ─────────────────────────────

    def search_similar_symptoms(self, patient_id: str, target_symptoms: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves previous check-ins where any of the target symptoms were reported,
        along with the day's vitals and notes for clinical pattern comparison.
        """
        rows = self._fetch_rows(
            "SELECT c.day, c.timestamp, c.mood, c.symptoms, c.notes, v.bp_systolic, v.bp_diastolic, v.blood_glucose "
            "FROM checkins c LEFT JOIN vitals v ON c.patient_id=v.patient_id AND c.day=v.day "
            "WHERE c.patient_id=? ORDER BY c.day DESC",
            (patient_id,),
        )
        matches = []
        target_set = {s.lower().strip() for s in target_symptoms}
        for r in rows:
            try:
                symptoms_logged = json.loads(r["symptoms"] or "[]")
            except Exception:
                symptoms_logged = []
            symptoms_set = {s.lower().strip() for s in symptoms_logged}
            common = target_set.intersection(symptoms_set)
            if common:
                r_dict = dict(r)
                r_dict["matched_symptoms"] = list(common)
                matches.append(r_dict)
        return matches

    def get_context_for_agent(self, patient_id: str, agent_role: str = "general") -> Dict[str, Any]:
        """
        Compiles an all-in-one contextual snapshot of the patient across the last 7 to 30 days.
        Used by agents before reasoning or interacting.
        """
        max_day = self._get_max_day(patient_id)
        vitals_7d = self.get_trend(patient_id, "bp_systolic", days=7)
        gluc_7d = self.get_trend(patient_id, "blood_glucose", days=7)
        adherence_7d = self.get_medication_adherence(patient_id, days=7)
        social_7d = self.get_social_summary(patient_id, days=7)
        recent_events = self.get_all_events(patient_id)

        # Recent symptoms across last 5 check-ins
        recent_checkins = self._fetch_rows(
            "SELECT day, mood, symptoms, notes FROM checkins WHERE patient_id=? ORDER BY day DESC LIMIT 5",
            (patient_id,),
        )
        recent_symptoms = []
        for c in recent_checkins:
            try:
                s_list = json.loads(c["symptoms"] or "[]")
                recent_symptoms.extend(s_list)
            except Exception:
                pass
        recent_symptoms = list(set(recent_symptoms))

        return {
            "patient_id": patient_id,
            "current_day": max_day,
            "bp_systolic_7d_avg": vitals_7d.get("average"),
            "bp_trend_direction": vitals_7d.get("trend_direction"),
            "blood_glucose_7d_avg": gluc_7d.get("average"),
            "glucose_trend_direction": gluc_7d.get("trend_direction"),
            "adherence_7d_pct": adherence_7d.get("adherence_pct"),
            "isolation_days_7d": social_7d.get("isolation_days"),
            "recent_symptoms": recent_symptoms,
            "active_events_count": len(recent_events),
            "recent_events": recent_events[-5:],
        }

    # ─── Retrieval Methods ─────────────────────────────────────────────────

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
            "caregiver_actions": self._fetch_rows(
                "SELECT * FROM caregiver_actions WHERE patient_id=? AND day BETWEEN ? AND ? ORDER BY day",
                (patient_id, min_day, max_day),
            ),
        }

    def get_trend(self, patient_id: str, metric: str, days: int = 7) -> Dict[str, Any]:
        """Compute rolling trend statistics for a metric over the last N days."""
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
            return {
                "metric": metric, "values": [], "average": None,
                "min": None, "max": None, "trend_direction": "unknown", "trend_pct_change": 0
            }

        avg = sum(values) / len(values)
        mn = min(values)
        mx = max(values)

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
        """Calculate medication adherence percentage over past N days."""
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
        """Summarise social interaction and isolation over the past N days."""
        max_day = self._get_max_day(patient_id)
        min_day = max(1, max_day - days + 1)
        rows = self._fetch_rows(
            "SELECT had_interaction, interaction_type, duration_minutes FROM social_logs "
            "WHERE patient_id=? AND day BETWEEN ? AND ?",
            (patient_id, min_day, max_day),
        )
        total_days = max(1, max_day - min_day + 1)
        interaction_days = sum(1 for r in rows if r["had_interaction"] == 1)
        isolation_days = max(0, total_days - interaction_days)
        return {
            "total_days": total_days,
            "interaction_days": interaction_days,
            "isolation_days": isolation_days,
            "isolation_pct": round((isolation_days / total_days) * 100, 1),
        }

    def get_all_vitals(self, patient_id: str) -> List[Dict]:
        return self._fetch_rows(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY day",
            (patient_id,),
        )

    def get_all_events(self, patient_id: str, severity: Optional[str] = None) -> List[Dict]:
        if severity:
            return self._fetch_rows(
                "SELECT * FROM events WHERE patient_id=? AND severity=? ORDER BY day",
                (patient_id, severity),
            )
        return self._fetch_rows(
            "SELECT * FROM events WHERE patient_id=? ORDER BY day",
            (patient_id,),
        )

    def get_patient_ids(self) -> List[str]:
        rows = self._fetch_rows("SELECT DISTINCT patient_id FROM vitals", ())
        ids = [r["patient_id"] for r in rows]
        if "patient_001" not in ids:
            ids.insert(0, "patient_001")
        return ids

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

    def reset(self) -> None:
        """Wipe all patient data. Called at the start of each simulation run —
        without this, every `python main.py` appended another 30 days of rows
        and skewed every average/adherence stat."""
        cur = self._conn.cursor()
        tables = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )]
        for t in tables:
            cur.execute(f'DELETE FROM "{t}"')
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
