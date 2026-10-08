from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories import (
    get_or_create_company,
    get_shipment,
    list_shipments,
    save_report,
)
from backend.schemas import (
    InvestigationResponse,
    SaaSAnalysisResponse,
    ShipmentImportResponse,
    ShipmentResponse,
)
from backend.services.import_service import import_shipments
from backend.services.risk_state import determine_risk_state

router = APIRouter(
    prefix="/api/shipments",
    tags=["shipments"],
)

DEFAULT_COMPANY_NAME = "Demo Company"


def get_current_company(
    db: Session = Depends(get_db),
):
    return get_or_create_company(
        db,
        DEFAULT_COMPANY_NAME,
    )


def _serialize_shipment(shipment) -> dict:
    response = ShipmentResponse.model_validate(shipment)
    data = response.model_dump()

    data["risk_state"] = determine_risk_state(
        current_status=shipment.current_status,
        estimated_arrival=shipment.estimated_arrival,
    )

    return data


@router.get("")
def get_shipments(
    db: Session = Depends(get_db),
):
    company = get_current_company(db)

    shipments = list_shipments(
        db,
        company.id,
    )

    return [
        _serialize_shipment(shipment)
        for shipment in shipments
    ]


@router.post(
    "/import",
    response_model=ShipmentImportResponse,
)
async def upload_shipments(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    filename = file.filename.lower()

    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    company = get_current_company(db)

    try:
        return import_shipments(
            db=db,
            company_id=company.id,
            file_bytes=file_bytes,
            filename=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/at-risk")
def get_at_risk_shipments(
    db: Session = Depends(get_db),
):
    company = get_current_company(db)

    shipments = list_shipments(
        db,
        company.id,
    )

    return [
        _serialize_shipment(shipment)
        for shipment in shipments
        if determine_risk_state(
            current_status=shipment.current_status,
            estimated_arrival=shipment.estimated_arrival,
        )
        == "at_risk"
    ]


@router.get("/{shipment_id}")
def get_shipment_by_id(
    shipment_id: str,
    db: Session = Depends(get_db),
):
    company = get_current_company(db)

    shipment = get_shipment(
        db,
        company.id,
        shipment_id,
    )

    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found.",
        )

    return _serialize_shipment(shipment)


@router.get(
    "/{shipment_id}/investigate",
    response_model=InvestigationResponse,
)
def investigate_shipment(
    shipment_id: str,
    db: Session = Depends(get_db),
):
    company = get_current_company(db)

    shipment = get_shipment(
        db,
        company.id,
        shipment_id,
    )

    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found.",
        )

    from backend.services.investigation_service import (
        SaaSInvestigationService,
    )

    investigation = SaaSInvestigationService().investigate(
        shipment,
        company_id=company.id,
    )

    return investigation


@router.get(
    "/{shipment_id}/analyze",
    response_model=SaaSAnalysisResponse,
)
def analyze_shipment(
    shipment_id: str,
    db: Session = Depends(get_db),
):
    company = get_current_company(db)

    shipment = get_shipment(
        db,
        company.id,
        shipment_id,
    )

    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found.",
        )

    from backend.services.saas_agent_service import (
        SaaSAgentService,
    )

    agent = SaaSAgentService()

    result = agent.run(
        shipment=shipment,
        company_id=company.id,
    )

    investigation = {
        key: value
        for key, value in result.items()
        if key != "briefing"
    }

    briefing = result.get(
        "briefing",
        "",
    )

    risk = investigation["risk"]

    if (
        risk["ml_available"]
        and risk["ml_probability"] is not None
    ):
        risk_score = float(
            risk["ml_probability"]
        )

        flagged = bool(
            risk["ml_is_at_risk"]
        )
    else:
        risk_score = (
            1.0
            if risk["state"] == "at_risk"
            else 0.0
        )

        flagged = (
            risk["state"] == "at_risk"
        )

    report = save_report(
        db=db,
        shipment=shipment,
        risk_score=risk_score,
        flagged=flagged,
        body=briefing,
    )

    return {
        **investigation,
        "briefing": briefing,
        "report_id": report.id,
    }