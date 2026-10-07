from datetime import datetime, timezone
from typing import Optional

from app.ingestion.dataco import get_shipment
from app.schemas.report import Alternative, RiskReport
from app.services import tools
from app.services.predictor import is_flagged, score_shipment

# Placeholder thresholds for "severe" weather. Agree real values with your team.
SEVERE_PRECIP_MM_H = 5.0
SEVERE_WIND_KMH = 60.0
MIN_REROUTE_HOURS = 48       # PRD: warn at least 48 hours ahead


def investigate(shipment_id: str, as_of: Optional[datetime] = None) -> RiskReport:
    shipment = get_shipment(shipment_id)
    if shipment is None:
        raise ValueError(f"Unknown shipment: {shipment_id}")

    score = score_shipment(shipment)
    report = RiskReport(
        shipment_id=shipment.id,
        risk_score=score,
        flagged=is_flagged(score),
        created_at=datetime.now(timezone.utc),
    )
    if not report.flagged:
        return report                      # nothing to investigate

    # 1. Gather evidence: every tool result is saved with an ID
    status = tools.get_shipment_status(shipment.id, as_of)
    e_status = tools.record_evidence(report, "shipment", "get_shipment_status", status)

    weather = tools.get_weather(shipment.lat, shipment.lon)
    e_weather = tools.record_evidence(report, "weather", "get_weather", weather)
    if not weather["available"]:
        tools.mark_unavailable(report, "weather")

    alts = tools.find_alternative_shipping(shipment.id)
    e_alts = tools.record_evidence(report, "supplier", "find_alternative_shipping", alts)

    # 2. Work out the causes. Each one cites the evidence it rests on.
    causes = []

    rate = alts.get("current_late_rate")
    if rate is not None and rate >= 0.5:
        causes.append(
            f"{shipment.shipping_mode} shipments are late {rate:.0%} of the time "
            f"historically [{e_alts.id}]"
        )

    hours_left = status["hours_until_scheduled_arrival"]
    if hours_left < MIN_REROUTE_HOURS:
        causes.append(
            f"only {hours_left:.0f} hours remain until scheduled arrival, "
            f"which leaves little time to reroute [{e_status.id}]"
        )

    if weather["available"] and (
        weather["max_precip_mm_h"] >= SEVERE_PRECIP_MM_H
        or weather["max_wind_kmh"] >= SEVERE_WIND_KMH
    ):
        causes.append(
            f"severe weather is forecast near the destination [{e_weather.id}]"
        )

    report.root_cause = "; ".join(causes) or "No single cause stands out; see evidence."

    # 3. Turn candidate shipping modes into Alternatives
    for c in alts.get("candidates", []):
        tradeoff = "slower than scheduled" if c["slower_than_current"] else "not slower"
        report.alternatives.append(Alternative(
            supplier_id=c["mode"],          # holds the shipping mode for now
            name=f"{c['mode']} shipping",
            reason=f"historical late rate {c['late_rate']:.0%}; {tradeoff} "
                   f"({c['scheduled_days']} scheduled days) [{e_alts.id}]",
            constraints_checked=alts["constraints_checked"],
        ))

    return report