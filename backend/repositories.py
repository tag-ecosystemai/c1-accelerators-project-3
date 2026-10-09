from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Company, Report, Shipment


def get_or_create_company(
    db: Session,
    name: str,
) -> Company:
    company = db.scalar(
        select(Company).where(Company.name == name)
    )

    if company is not None:
        return company

    company = Company(name=name)
    db.add(company)
    db.commit()
    db.refresh(company)

    return company


def create_shipment(
    db: Session,
    company_id: int,
    shipment_id: str,
    tracking_number: str | None = None,
    carrier: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    origin_coordinates: dict[str, Any] | None = None,
    destination_coordinates: dict[str, Any] | None = None,
    estimated_arrival: datetime | None = None,
    current_status: str | None = None,
    shipping_mode: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> Shipment:
    shipment = Shipment(
        company_id=company_id,
        shipment_id=shipment_id,
        tracking_number=tracking_number,
        carrier=carrier,
        origin=origin,
        destination=destination,
        origin_coordinates=origin_coordinates,
        destination_coordinates=destination_coordinates,
        estimated_arrival=estimated_arrival,
        current_status=current_status,
        shipping_mode=shipping_mode,
        metadata_json=metadata_json,
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return shipment


def get_shipment(
    db: Session,
    company_id: int,
    shipment_id: str,
) -> Shipment | None:
    return db.scalar(
        select(Shipment).where(
            Shipment.company_id == company_id,
            Shipment.shipment_id == shipment_id,
        )
    )


def list_shipments(
    db: Session,
    company_id: int,
) -> list[Shipment]:
    return list(
        db.scalars(
            select(Shipment)
            .where(Shipment.company_id == company_id)
            .order_by(Shipment.created_at.desc())
        )
    )


def save_report(
    db: Session,
    shipment: Shipment,
    risk_score: float,
    flagged: bool,
    body: str,
) -> Report:
    report = Report(
        shipment_id=shipment.id,
        risk_score=risk_score,
        flagged=flagged,
        body=body,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


def get_latest_report(
    db: Session,
    shipment: Shipment,
) -> Report | None:
    return db.scalar(
        select(Report)
        .where(Report.shipment_id == shipment.id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )


def list_flagged_shipments(
    db: Session,
    company_id: int,
) -> list[tuple[Shipment, Report]]:
    statement = (
        select(Shipment, Report)
        .join(Report, Report.shipment_id == Shipment.id)
        .where(
            Shipment.company_id == company_id,
            Report.flagged.is_(True),
        )
        .order_by(Report.risk_score.desc())
    )

    return list(db.execute(statement).all())