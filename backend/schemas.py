from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CompanyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ShipmentResponse(BaseModel):
    id: int
    shipment_id: str
    tracking_number: str | None = None
    carrier: str | None = None
    origin: str | None = None
    destination: str | None = None
    origin_coordinates: dict[str, Any] | None = None
    destination_coordinates: dict[str, Any] | None = None
    estimated_arrival: datetime | None = None
    current_status: str | None = None
    shipping_mode: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShipmentImportRow(BaseModel):
    shipment_id: str = Field(..., min_length=1)
    tracking_number: str | None = None
    carrier: str | None = None
    origin: str | None = None
    destination: str | None = None
    estimated_arrival: datetime | None = None
    current_status: str | None = None
    shipping_mode: str | None = None


class ShipmentImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    id: int
    shipment_id: int
    risk_score: float
    flagged: bool
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestigationEvidence(BaseModel):
    type: str
    source: str
    value: Any = None


class InvestigationRisk(BaseModel):
    state: str
    assessed_at: str
    ml_available: bool = False
    ml_probability: float | None = None
    ml_threshold: float | None = None
    ml_is_at_risk: bool | None = None
    ml_missing_features: list[str] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    shipment: dict[str, Any]
    risk: InvestigationRisk
    weather: dict[str, Any] | None = None
    route_options: list[dict[str, Any]] = Field(default_factory=list)
    supplier_options: list[dict[str, Any]] = Field(default_factory=list)
    news_results: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[InvestigationEvidence] = Field(default_factory=list)
    knowledge_results: list[dict[str, Any]] = Field(default_factory=list)


class SaaSAnalysisResponse(BaseModel):
    shipment: dict[str, Any]
    risk: InvestigationRisk
    weather: dict[str, Any] | None = None
    route_options: list[dict[str, Any]] = Field(default_factory=list)
    supplier_options: list[dict[str, Any]] = Field(default_factory=list)
    news_results: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[InvestigationEvidence] = Field(default_factory=list)
    knowledge_results: list[dict[str, Any]] = Field(default_factory=list)
    briefing: str
    report_id: int | None = None