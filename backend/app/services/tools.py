import json
from datetime import datetime, timezone
from typing import Optional

from app.ingestion.dataco import _orders, get_shipment
from app.ingestion.weather import fetch_weather
from app.schemas.report import Alternative, Evidence, RiskReport
from app.services.predictor import SHIPPING_MODE_LATE_RATE


def get_shipment_status(shipment_id: str, as_of: Optional[datetime] = None) -> dict:
    """Details of a shipment and how long until it is due.

    DataCo is historical, so "now" is simulated: as_of defaults to the order date.
    """
    s = get_shipment(shipment_id)
    if s is None:
        return {"error": "unknown shipment"}
    as_of = as_of or s.order_date
    hours_left = (s.scheduled_arrival - as_of).total_seconds() / 3600
    return {
        "shipment_id": s.id,
        "shipping_mode": s.shipping_mode,
        "category": s.category,
        "destination": f"{s.city}, {s.country}",
        "scheduled_arrival": s.scheduled_arrival.isoformat(),
        "hours_until_scheduled_arrival": round(hours_left, 1),
        "quantity": s.quantity,
    }


def get_weather(lat: float, lon: float) -> dict:
    """Weather summary for the next 72 hours, or {"available": False}."""
    weather = fetch_weather(lat, lon)
    if weather is None:
        return {"available": False}
    return {"available": True, **weather}


def find_alternative_shipping(shipment_id: str) -> dict:
    """Shipping modes with a lower late rate than the current one."""
    s = get_shipment(shipment_id)
    if s is None:
        return {"error": "unknown shipment"}

    # Scheduled days per mode, read from the data rather than typed in
    days = _orders().groupby("shipping_mode")["scheduled_days"].first().to_dict()
    current_rate = SHIPPING_MODE_LATE_RATE.get(s.shipping_mode)
    if current_rate is None:
        return {"candidates": [], "note": "unknown current shipping mode"}

    candidates = []
    for mode, rate in SHIPPING_MODE_LATE_RATE.items():
        if mode != s.shipping_mode and rate < current_rate:
            candidates.append({
                "mode": mode,
                "late_rate": rate,
                "scheduled_days": int(days[mode]),
                "slower_than_current": int(days[mode]) > s.scheduled_days,
            })
    candidates.sort(key=lambda c: c["late_rate"])
    return {
        "current_mode": s.shipping_mode,
        "current_late_rate": current_rate,
        "candidates": candidates,
        "constraints_checked": ["lower_late_rate"],
    }


def record_evidence(report: RiskReport, source: str, signal: str, detail: dict) -> Evidence:
    """Save a tool result on the report as the next numbered piece of evidence."""
    evidence = Evidence(
        id=f"E{len(report.evidence) + 1}",
        source=source,
        signal=signal,
        detail=json.dumps(detail, default=str),
        retrieved_at=datetime.now(timezone.utc),
    )
    report.evidence.append(evidence)
    return evidence


def mark_unavailable(report: RiskReport, signal: str) -> None:
    """Note that a data source could not be reached (PRD: never fail silently)."""
    if signal not in report.signals_unavailable:
        report.signals_unavailable.append(signal)