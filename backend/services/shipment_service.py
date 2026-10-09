from __future__ import annotations

from sqlalchemy.orm import Session

from backend.repositories import get_shipment
from backend.services.risk_state import determine_risk_state


def get_shipment_for_company(
    db: Session,
    company_id: int,
    shipment_id: str,
):
    shipment = get_shipment(
        db,
        company_id,
        shipment_id,
    )

    if shipment is None:
        return None

    return shipment


def build_shipment_context(
    shipment,
) -> dict:
    """
    Convert a persisted canonical shipment into the neutral context
    expected by downstream SentinelAI intelligence services.

    This deliberately contains no ML prediction. The current CatBoost
    model is DataCo-specific and must not be applied to arbitrary
    customer shipments.
    """

    return {
        "shipment_id": shipment.shipment_id,
        "tracking_number": shipment.tracking_number,
        "carrier": shipment.carrier,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "origin_coordinates": shipment.origin_coordinates,
        "destination_coordinates": shipment.destination_coordinates,
        "estimated_arrival": (
            shipment.estimated_arrival.isoformat()
            if shipment.estimated_arrival
            else None
        ),
        "current_status": shipment.current_status,
        "shipping_mode": shipment.shipping_mode,
        "risk_state": determine_risk_state(
            current_status=shipment.current_status,
            estimated_arrival=shipment.estimated_arrival,
        ),
    }