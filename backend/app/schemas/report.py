from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class Evidence(BaseModel):
    id: str                  # "E1", "E2", ... the briefing cites these
    source: Literal["shipment", "weather", "supplier", "news", "rag"]
    signal: str              # what was checked, e.g. "get_weather"
    detail: str              # what it found
    retrieved_at: datetime


class Alternative(BaseModel):
    supplier_id: str
    name: str
    reason: str
    constraints_checked: list[str]   # e.g. ["capacity", "region"]


class RiskReport(BaseModel):
    shipment_id: str
    risk_score: float                # 0.0 to 1.0, chance of being late
    flagged: bool
    root_cause: Optional[str] = None
    evidence: list[Evidence] = []
    alternatives: list[Alternative] = []
    signals_unavailable: list[str] = []
    briefing: Optional[str] = None
    created_at: datetime