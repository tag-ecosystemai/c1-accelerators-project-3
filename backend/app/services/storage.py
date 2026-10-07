import sqlite3
from pathlib import Path
from typing import Optional

from app.schemas.report import RiskReport

# backend/app/services/storage.py -> parents[2] is backend/
DB_PATH = Path(__file__).resolve().parents[2] / "sentinel.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS reports (
               shipment_id TEXT PRIMARY KEY,
               flagged INTEGER,
               risk_score REAL,
               body TEXT,
               created_at TEXT
           )"""
    )
    return conn


def save_report(report: RiskReport) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?)",
            (report.shipment_id, int(report.flagged), report.risk_score,
             report.json(), report.created_at.isoformat()),
        )
    conn.close()


def get_report(shipment_id: str) -> Optional[RiskReport]:
    conn = _connect()
    row = conn.execute(
        "SELECT body FROM reports WHERE shipment_id = ?", (shipment_id,)
    ).fetchone()
    conn.close()
    return RiskReport.parse_raw(row[0]) if row else None


def list_flagged() -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT body FROM reports WHERE flagged = 1 ORDER BY risk_score DESC"
    ).fetchall()
    conn.close()
    return [RiskReport.parse_raw(r[0]) for r in rows]