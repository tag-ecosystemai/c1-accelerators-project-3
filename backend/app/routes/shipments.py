from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.report import RiskReport
from app.services import storage
from app.services.briefing import generate_briefing
from app.services.investigator import investigate

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.post("/{shipment_id}/investigate", response_model=RiskReport)
def run_investigation(shipment_id: str):
    try:
        report = investigate(shipment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown shipment")
    report.briefing = generate_briefing(report)
    storage.save_report(report)
    return report


@router.get("/at-risk", response_model=List[RiskReport])
def at_risk():
    return storage.list_flagged()


@router.get("/{shipment_id}/report", response_model=RiskReport)
def read_report(shipment_id: str):
    report = storage.get_report(shipment_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No report yet. Run the investigation first.")
    return report