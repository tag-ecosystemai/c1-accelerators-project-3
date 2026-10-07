import re

from app.schemas.report import RiskReport

CITATION = re.compile(r"\[(E\d+)\]")

# Signals the system doesn't call yet. Remove "news" once it is connected.
NOT_YET_CONNECTED = ["news"]


def find_ungrounded(report: RiskReport) -> list:
    """Return citations that point to evidence that doesn't exist, plus
    causes that cite nothing. An empty list means the report is grounded."""
    valid = {e.id for e in report.evidence}
    problems = []

    claims = []
    if report.root_cause:
        claims += report.root_cause.split("; ")
    claims += [a.reason for a in report.alternatives]

    for claim in claims:
        cited = CITATION.findall(claim)
        if not cited and not claim.startswith("No single cause"):
            problems.append(f"no citation: {claim[:60]}")
        for c in cited:
            if c not in valid:
                problems.append(f"unknown evidence {c}")
    return problems


def build_briefing(report: RiskReport) -> str:
    if not report.flagged:
        return (f"Shipment {report.shipment_id} is low risk "
                f"(score {report.risk_score:.2f}). No action needed.")

    lines = [
        f"DISRUPTION BRIEFING: Shipment {report.shipment_id}",
        f"Risk of late delivery: {report.risk_score:.0%}",
        "",
        "Why it is at risk:",
    ]
    for cause in (report.root_cause or "").split("; "):
        lines.append(f"  - {cause}")

    lines += ["", "Options (check the trade-offs before acting):"]
    if report.alternatives:
        for a in report.alternatives:
            lines.append(f"  - {a.name}: {a.reason}")
    else:
        lines.append("  - No better option found in the data.")

    lines += ["", "Data gaps:"]
    if report.signals_unavailable:
        lines.append(f"  - Failed to load: {', '.join(report.signals_unavailable)}")
    if NOT_YET_CONNECTED:
        lines.append(f"  - Not checked: {', '.join(NOT_YET_CONNECTED)}")
    if not report.signals_unavailable and not NOT_YET_CONNECTED:
        lines.append("  - None. All signals were available.")

    lines += ["", "Evidence:"]
    for e in report.evidence:
        lines.append(f"  [{e.id}] {e.source} / {e.signal}: {e.detail[:150]}")

    return "\n".join(lines)


def generate_briefing(report: RiskReport) -> str:
    problems = find_ungrounded(report)
    if problems:
        raise ValueError(f"Briefing is not grounded: {problems}")
    return build_briefing(report)