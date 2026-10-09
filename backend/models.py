from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    shipments: Mapped[list["Shipment"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    shipment_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    tracking_number: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    carrier: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    origin: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    destination: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    origin_coordinates: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    destination_coordinates: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    estimated_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    current_status: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    shipping_mode: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    company: Mapped["Company"] = relationship(
        back_populates="shipments",
    )

    reports: Mapped[list["Report"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id"),
        nullable=False,
        index=True,
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    flagged: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    shipment: Mapped["Shipment"] = relationship(
        back_populates="reports",
    )