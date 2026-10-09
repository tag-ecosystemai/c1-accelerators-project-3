from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal


RiskState = Literal["on_track", "monitoring", "at_risk"]


def _normalize_status(status: str | None) -> str:
    if not status:
        return ""

    return status.strip().lower()


def _is_eta_overdue(
    estimated_arrival: datetime | None,
    now: datetime | None = None,
) -> bool:
    if estimated_arrival is None:
        return False

    current_time = now or datetime.now(timezone.utc)

    if estimated_arrival.tzinfo is None:
        estimated_arrival = estimated_arrival.replace(
            tzinfo=timezone.utc,
        )

    return estimated_arrival < current_time


def determine_risk_state(
    current_status: str | None,
    estimated_arrival: datetime | None,
    now: datetime | None = None,
) -> RiskState:
    """
    Determine a generic operational shipment state.

    This is intentionally separate from the DataCo-specific CatBoost
    prediction model. It uses only canonical shipment fields that a
    SaaS customer can reasonably provide.
    """

    status = _normalize_status(current_status)

    if status in {
        "delayed",
        "late",
        "delivery delayed",
        "exception",
        "failed delivery",
        "cancelled",
        "canceled",
    }:
        return "at_risk"

    if _is_eta_overdue(
        estimated_arrival,
        now=now,
    ):
        return "at_risk"

    if status in {
        "processing",
        "pending",
        "unknown",
        "exception",
        "awaiting pickup",
        "label created",
        "booked",
    }:
        return "monitoring"

    if status in {
        "in transit",
        "in_transit",
        "shipped",
        "out for delivery",
        "dispatched",
        "on the way",
    }:
        return "on_track"

    if not status:
        return "monitoring"

    return "monitoring"