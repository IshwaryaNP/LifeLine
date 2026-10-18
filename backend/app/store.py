import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "lifeline_triage.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        minute INTEGER,
        channel TEXT,
        sender_hash TEXT,
        text TEXT,
        need_type TEXT,
        people_count INTEGER,
        vulnerable_groups TEXT,
        urgency_cues TEXT,
        place_text TEXT,
        extraction_confidences TEXT,
        lat REAL,
        lon REAL,
        radius_m REAL,
        zone_id TEXT,
        location_confidence REAL,
        needs_human_check INTEGER,
        is_fake_detected INTEGER
    )
    """)

    # Incidents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        zone_id TEXT,
        zone_name TEXT,
        report_ids TEXT,
        lat REAL,
        lon REAL,
        radius_m REAL,
        need_type TEXT,
        estimated_people INTEGER,
        vulnerable_groups TEXT,
        independent_sources INTEGER,
        channels TEXT,
        reliability_score REAL,
        priority_score REAL,
        factors TEXT,
        reasons TEXT,
        status TEXT,
        override_reason TEXT,
        override_priority REAL,
        needs_human_check INTEGER
    )
    """)

    # Audit log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        incident_id TEXT,
        action_type TEXT,
        reason TEXT,
        new_priority REAL,
        target_id TEXT,
        user TEXT
    )
    """)

    # Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        cyclone_name TEXT,
        expected_landfall_time TEXT,
        category TEXT,
        zone_id TEXT,
        zone_name TEXT,
        message TEXT,
        reasons TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_audit_action(action: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (timestamp, incident_id, action_type, reason, new_priority, target_id, user)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        action.get("timestamp"),
        action.get("incident_id"),
        action.get("action_type"),
        action.get("reason"),
        action.get("new_priority"),
        action.get("target_id"),
        action.get("user", "Coordinator")
    ))
    conn.commit()
    conn.close()

def get_audit_logs() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM actions ORDER BY id DESC")
    rows = cursor.fetchall()
    logs = [dict(r) for r in rows]
    conn.close()
    return logs

def save_alerts(alerts: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    for alt in alerts:
        cursor.execute("""
            INSERT OR REPLACE INTO alerts (id, cyclone_name, expected_landfall_time, category, zone_id, zone_name, message, reasons, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alt["id"],
            alt["cyclone_name"],
            alt["expected_landfall_time"],
            alt["category"],
            alt["zone_id"],
            alt["zone_name"],
            alt["message"],
            json.dumps(alt.get("reasons", [])),
            alt["status"]
        ))
    conn.commit()
    conn.close()

def update_alert_status(alert_id: str, status: str = "approved"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id))
    conn.commit()
    conn.close()

def get_alerts() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts")
    rows = cursor.fetchall()
    alerts = []
    for r in rows:
        d = dict(r)
        d["reasons"] = json.loads(d["reasons"]) if d["reasons"] else []
        alerts.append(d)
    conn.close()
    return alerts
