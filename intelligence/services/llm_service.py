from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests


class LLMService:
    """
    Generates evidence-grounded operational briefings.

    Supported providers:
    - Azure OpenAI
    - Google Gemini

    If no LLM credentials are configured, the service uses a deterministic
    fallback briefing. This keeps local development and automated tests
    functional without requiring secrets.

    Production deployments should configure an actual LLM provider.
    """

    def __init__(self) -> None:
        self.provider = os.getenv(
            "LLM_PROVIDER",
            "azure_openai",
        ).lower()

    def generate_briefing(
        self,
        *,
        shipment: dict[str, Any],
        risk_assessment: dict[str, Any],
        weather: dict[str, Any] | None,
        route_context: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]],
        investigation_findings: list[str],
    ) -> str:
        prompt = self._build_prompt(
            shipment=shipment,
            risk_assessment=risk_assessment,
            weather=weather,
            route_context=route_context,
            route_options=route_options,
            supplier_options=supplier_options,
            news=news,
            knowledge_results=knowledge_results,
            investigation_findings=investigation_findings,
        )

        if self.provider == "azure_openai":
            if self._azure_openai_configured():
                return self._generate_with_azure_openai(prompt)

            return self._generate_fallback_briefing(
                shipment=shipment,
                risk_assessment=risk_assessment,
                weather=weather,
                route_options=route_options,
                supplier_options=supplier_options,
                news=news,
                knowledge_results=knowledge_results,
                investigation_findings=investigation_findings,
            )

        if self.provider == "gemini":
            if os.getenv("GEMINI_API_KEY"):
                return self._generate_with_gemini(prompt)

            return self._generate_fallback_briefing(
                shipment=shipment,
                risk_assessment=risk_assessment,
                weather=weather,
                route_options=route_options,
                supplier_options=supplier_options,
                news=news,
                knowledge_results=knowledge_results,
                investigation_findings=investigation_findings,
            )

        raise ValueError(
            f"Unsupported LLM_PROVIDER '{self.provider}'. "
            "Use 'azure_openai' or 'gemini'."
        )

    def generate_saas_briefing(
        self,
        *,
        shipment: dict[str, Any],
        risk: dict[str, Any],
        weather: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news_results: list[dict[str, Any]] | None = None,
        evidence: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]] | None = None,
    ) -> str:
        """
        Generate an evidence-grounded briefing for a canonical SaaS shipment.

        Unlike the DataCo briefing path, this does not assume a historical
        ML probability or DataCo-specific shipment fields.
        """
        news_results = news_results or []
        knowledge_results = knowledge_results or []

        prompt = self._build_saas_prompt(
            shipment=shipment,
            risk=risk,
            weather=weather,
            route_options=route_options,
            supplier_options=supplier_options,
            news_results=news_results,
            evidence=evidence,
            knowledge_results=knowledge_results,
        )

        if self.provider == "azure_openai":
            if self._azure_openai_configured():
                return self._generate_with_azure_openai(prompt)

            return self._generate_saas_fallback(
                shipment=shipment,
                risk=risk,
                weather=weather,
                route_options=route_options,
                supplier_options=supplier_options,
                news_results=news_results,
                evidence=evidence,
                knowledge_results=knowledge_results,
            )

        if self.provider == "gemini":
            if os.getenv("GEMINI_API_KEY"):
                return self._generate_with_gemini(prompt)

            return self._generate_saas_fallback(
                shipment=shipment,
                risk=risk,
                weather=weather,
                route_options=route_options,
                supplier_options=supplier_options,
                news_results=news_results,
                evidence=evidence,
                knowledge_results=knowledge_results,
            )

        raise ValueError(
            f"Unsupported LLM_PROVIDER '{self.provider}'. "
            "Use 'azure_openai' or 'gemini'."
        )

    def _azure_openai_configured(self) -> bool:
        return all(
            (
                os.getenv("AZURE_OPENAI_ENDPOINT"),
                os.getenv("AZURE_OPENAI_API_KEY"),
                os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            )
        )

    def _build_prompt(
        self,
        *,
        shipment: dict[str, Any],
        risk_assessment: dict[str, Any],
        weather: dict[str, Any] | None,
        route_context: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]],
        investigation_findings: list[str],
    ) -> str:
        evidence = {
            "shipment": shipment,
            "risk_assessment": risk_assessment,
            "weather": weather,
            "route_context": route_context,
            "route_options": route_options,
            "supplier_options": supplier_options,
            "news": news,
            "investigation_findings": investigation_findings,
            "retrieved_procedures": knowledge_results,
        }

        return f"""
You are the operational intelligence assistant inside SentinelAI,
a supply-chain disruption decision-support system.

Your job is to produce a concise operational briefing for a human
logistics operator.

IMPORTANT RULES:

1. Use ONLY the evidence supplied below.
2. Do not invent shipment facts, suppliers, routes, weather events,
   news events, or operational conditions.
3. Clearly distinguish:
   - confirmed information
   - model estimates
   - external evidence
   - uncertainty
4. A high model risk score does NOT mean the shipment will definitely
   be late.
5. Synthetic or demonstration route/supplier data must be described
   as demonstration data when relevant.
6. Do not claim that an alternative route or supplier is available
   unless the supplied evidence explicitly supports that statement.
7. Do not recommend that SentinelAI automatically execute an action.
8. Final decisions belong to a human operator.
9. If evidence is missing, say that it is unavailable.
10. Do not use knowledge outside the supplied evidence.

Return a professional briefing using exactly these sections:

EXECUTIVE SUMMARY
RISK ASSESSMENT
EVIDENCE
LIKELY CONTRIBUTORS
RECOMMENDED HUMAN REVIEW
UNCERTAINTIES

Keep the briefing concise and operationally useful.

SUPPLIED EVIDENCE:

{evidence}
""".strip()

    def _generate_fallback_briefing(
        self,
        *,
        shipment: dict[str, Any],
        risk_assessment: dict[str, Any],
        weather: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]],
        investigation_findings: list[str],
    ) -> str:
        """
        Generate a deterministic briefing when no LLM credentials exist.

        This is intentionally transparent: it never pretends to be an
        LLM-generated conclusion.
        """

        shipment_id = shipment.get("shipment_id", "Unknown")
        destination = (
            f"{shipment.get('destination_city', 'Unknown')}, "
            f"{shipment.get('destination_country', 'Unknown')}"
        )

        probability = risk_assessment.get("probability", 0.0)
        threshold = risk_assessment.get("threshold", 0.0)
        is_at_risk = risk_assessment.get("is_at_risk", False)

        risk_percent = probability * 100
        threshold_percent = threshold * 100

        status = (
            "flagged as at risk"
            if is_at_risk
            else "not flagged as at risk"
        )

        evidence_lines: list[str] = [
            f"- Shipment status: {shipment.get('status', 'Unavailable')}",
            f"- Destination: {destination}",
            f"- Shipping mode: {shipment.get('shipping_mode', 'Unavailable')}",
            f"- Historical model probability: {risk_percent:.1f}%",
            f"- Model decision threshold: {threshold_percent:.1f}%",
        ]

        if weather:
            evidence_lines.append(
                "- Weather evidence: available from the weather service."
            )
        else:
            evidence_lines.append(
                "- Weather evidence: unavailable."
            )

        evidence_lines.append(
            f"- Alternative route records: {len(route_options)}."
        )

        evidence_lines.append(
            f"- Alternative supplier records: {len(supplier_options)}."
        )

        evidence_lines.append(
            f"- News records: {len(news)}."
        )

        findings = investigation_findings or [
            "No additional investigation findings were recorded."
        ]

        knowledge_sources = sorted(
            {
                str(item.get("source", "Unknown"))
                for item in knowledge_results
            }
        )

        knowledge_summary = (
            ", ".join(knowledge_sources)
            if knowledge_sources
            else "No procedure source was retrieved."
        )

        return (
            "EXECUTIVE SUMMARY\n"
            f"Shipment {shipment_id} is {status}. "
            f"The historical risk model estimates a "
            f"{risk_percent:.1f}% probability of late delivery. "
            "This is a model estimate and not confirmation that the "
            "shipment will be late.\n\n"
            "RISK ASSESSMENT\n"
            f"Risk probability: {risk_percent:.1f}%. "
            f"Decision threshold: {threshold_percent:.1f}%. "
            f"At-risk classification: {'Yes' if is_at_risk else 'No'}.\n\n"
            "EVIDENCE\n"
            + "\n".join(evidence_lines)
            + "\n\n"
            "LIKELY CONTRIBUTORS\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\n"
            "RECOMMENDED HUMAN REVIEW\n"
            "Review the shipment status and available operational "
            "evidence before taking action. "
            f"{len(route_options)} route alternative(s) and "
            f"{len(supplier_options)} supplier alternative(s) are "
            "present in the supplied data. These alternatives should "
            "not be treated as confirmed operational availability "
            "without source verification.\n\n"
            "UNCERTAINTIES\n"
            f"Retrieved procedure source: {knowledge_summary}. "
            "External evidence may be incomplete or unavailable. "
            "The final operational decision remains with a human "
            "operator."
        )

    def _generate_with_azure_openai(self, prompt: str) -> str:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv(
            "AZURE_OPENAI_API_VERSION",
            "2024-10-21",
        )
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        missing = [
            name
            for name, value in {
                "AZURE_OPENAI_ENDPOINT": endpoint,
                "AZURE_OPENAI_API_KEY": api_key,
                "AZURE_OPENAI_DEPLOYMENT": deployment,
            }.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Missing Azure OpenAI configuration: "
                + ", ".join(missing)
            )

        url = (
            f"{endpoint.rstrip('/')}/openai/deployments/"
            f"{deployment}/chat/completions"
            f"?api-version={api_version}"
        )

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are SentinelAI's evidence-grounded "
                        "supply-chain operations analyst."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 900,
        }

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "api-key": api_key,
            },
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "Azure OpenAI returned an unexpected response."
            ) from exc

    def _generate_with_gemini(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required when "
                "LLM_PROVIDER='gemini'."
            )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent"
            f"?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 900,
            },
        }

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "Gemini returned an unexpected response."
            ) from exc

    @staticmethod
    def _format_saas_weather(
        weather: dict[str, Any] | None,
    ) -> str:
        if not weather:
            return "Unavailable."

        temperature = weather.get("temperature_c")
        precipitation = weather.get("precipitation_mm")
        wind = weather.get("wind_speed_kmh")

        parts: list[str] = []

        if temperature is not None:
            parts.append(f"{float(temperature):.1f}°C")

        if precipitation is not None:
            parts.append(
                f"{float(precipitation):.1f} mm precipitation"
            )

        if wind is not None:
            parts.append(
                f"{float(wind):.1f} km/h wind"
            )

        return ", ".join(parts) if parts else "Available."

    @staticmethod
    def _format_saas_routes(
        route_options: list[dict[str, Any]],
    ) -> list[str]:
        if not route_options:
            return ["No route alternatives were returned."]

        formatted: list[str] = []

        for route in route_options:
            route_id = route.get("route_id", "Unknown")
            distance = route.get("distance_km")
            duration = route.get("duration_minutes")
            recommendation = route.get(
                "recommendation",
                "Alternative route",
            )

            distance_text = (
                f"{float(distance):.1f} km"
                if distance is not None
                else "distance unavailable"
            )

            duration_text = (
                f"{float(duration) / 60:.1f} hours"
                if duration is not None
                else "duration unavailable"
            )

            formatted.append(
                f"Route {route_id}: {recommendation}; "
                f"{distance_text}; estimated driving time "
                f"{duration_text}."
            )

        return formatted

    @staticmethod
    def _format_saas_suppliers(
        supplier_options: list[dict[str, Any]],
    ) -> list[str]:
        if not supplier_options:
            return ["No supplier alternatives were supplied."]

        formatted: list[str] = []

        for supplier in supplier_options:
            name = supplier.get(
                "name",
                supplier.get("supplier", "Unknown supplier"),
            )
            formatted.append(
                f"Supplier option: {name}."
            )

        return formatted

    @staticmethod
    def _format_saas_news(
        news_results: list[dict[str, Any]],
    ) -> list[str]:
        if not news_results:
            return ["No relevant external news records were returned."]

        formatted: list[str] = []

        for article in news_results:
            title = article.get(
                "title",
                article.get("headline", "Untitled article"),
            )

            source = article.get(
                "source",
                article.get("domain", "Unknown source"),
            )

            formatted.append(
                f"{title} — {source}."
            )

        return formatted

    @staticmethod
    def _format_saas_evidence(
        evidence: list[dict[str, Any]],
    ) -> list[str]:
        if not evidence:
            return ["No additional evidence was recorded."]

        formatted: list[str] = []

        for item in evidence:
            evidence_type = str(
                item.get("type", "evidence")
            ).replace("_", " ").title()

            source = str(
                item.get("source", "unknown source")
            )

            value = item.get("value")

            if evidence_type == "Ml Risk Prediction":
                continue

            if evidence_type == "Weather":
                continue

            if evidence_type == "Route Options":
                continue

            if value is None or value == "":
                value_text = "Unavailable"
            elif isinstance(value, dict):
                value_text = "Available."
            elif isinstance(value, list):
                value_text = (
                    f"{len(value)} record(s) available."
                )
            else:
                value_text = str(value)

            formatted.append(
                f"- {evidence_type}: {value_text} "
                f"(source: {source})."
            )

        return formatted

    @staticmethod
    def _eta_status(
        estimated_arrival: str | None,
    ) -> str | None:
        if not estimated_arrival:
            return None

        try:
            eta = datetime.fromisoformat(
                estimated_arrival.replace("Z", "+00:00")
            )

            if eta.tzinfo is None:
                eta = eta.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            if eta < now:
                return "The estimated arrival time has passed."

            return "The estimated arrival time has not yet passed."

        except (TypeError, ValueError):
            return None

    def _build_saas_prompt(
        self,
        *,
        shipment: dict[str, Any],
        risk: dict[str, Any],
        weather: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news_results: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]],
    ) -> str:
        supplied_evidence = {
            "shipment": shipment,
            "risk": risk,
            "weather": weather,
            "route_options": route_options,
            "supplier_options": supplier_options,
            "external_news": news_results,
            "evidence": evidence,
            "knowledge_results": knowledge_results,
        }

        return f"""
You are the operational intelligence assistant inside SentinelAI,
a supply-chain disruption decision-support system.

Produce a concise operational briefing for a human logistics operator.

IMPORTANT RULES:

1. Use ONLY the supplied evidence.
2. Never invent shipment facts, causes, routes, suppliers, weather,
   news, or operational conditions.
3. The operational risk state is a deterministic assessment based on
   the shipment status and estimated arrival.
4. If an ML prediction is supplied, clearly label it as a model estimate.
5. External news is contextual evidence only. Do not claim that a news
   article caused the shipment disruption unless the supplied evidence
   establishes that relationship.
6. Clearly distinguish confirmed information from uncertainty.
7. Do not claim that a route or supplier is available unless the
   supplied evidence explicitly supports it.
8. If evidence is missing, say that it is unavailable.
9. Do not recommend automatic execution of operational actions.
10. Final decisions belong to a human operator.
11. Knowledge-base content may support a recommendation, but it must
    not be treated as proof of the shipment's actual condition.
12. Do not use knowledge outside the supplied evidence.
13. If the estimated arrival time has passed, explicitly mention that
    as temporal evidence.
14. Do not treat a model classification of "not at risk" as proof that
    a shipment currently marked delayed is safe.

Return exactly these sections:

EXECUTIVE SUMMARY
RISK ASSESSMENT
EVIDENCE
LIKELY CONTRIBUTORS
RECOMMENDED HUMAN REVIEW
UNCERTAINTIES

Keep the briefing concise and operationally useful.

SUPPLIED EVIDENCE:

{supplied_evidence}
""".strip()

    def _generate_saas_fallback(
        self,
        *,
        shipment: dict[str, Any],
        risk: dict[str, Any],
        weather: dict[str, Any] | None,
        route_options: list[dict[str, Any]],
        supplier_options: list[dict[str, Any]],
        news_results: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        knowledge_results: list[dict[str, Any]],
    ) -> str:
        """Generate a transparent deterministic SaaS briefing."""

        shipment_id = shipment.get(
            "shipment_id",
            "Unknown",
        )

        status = shipment.get(
            "current_status",
            "Unavailable",
        ) or "Unavailable"

        destination = shipment.get(
            "destination",
            "Unavailable",
        ) or "Unavailable"

        estimated_arrival = shipment.get(
            "estimated_arrival"
        )

        risk_state = risk.get(
            "state",
            "monitoring",
        )

        ml_available = risk.get(
            "ml_available",
            False,
        )

        ml_probability = risk.get(
            "ml_probability"
        )

        ml_threshold = risk.get(
            "ml_threshold"
        )

        ml_is_at_risk = risk.get(
            "ml_is_at_risk"
        )

        evidence_lines: list[str] = [
            f"- Shipment status: {status}.",
            f"- Destination: {destination}.",
            (
                "- Estimated arrival: "
                f"{estimated_arrival or 'Unavailable'}."
            ),
            f"- Operational risk state: {risk_state}.",
        ]

        eta_status = self._eta_status(
            estimated_arrival
        )

        if eta_status:
            evidence_lines.append(
                f"- ETA assessment: {eta_status}"
            )

        if ml_available and ml_probability is not None:
            probability_percent = (
                float(ml_probability) * 100
            )

            threshold_percent = (
                float(ml_threshold) * 100
                if ml_threshold is not None
                else None
            )

            evidence_lines.append(
                "- CatBoost risk probability: "
                f"{probability_percent:.1f}%."
            )

            if threshold_percent is not None:
                evidence_lines.append(
                    "- CatBoost decision threshold: "
                    f"{threshold_percent:.1f}%."
                )

            evidence_lines.append(
                "- CatBoost classification: "
                f"{'at risk' if ml_is_at_risk else 'not at risk'}."
            )
        else:
            evidence_lines.append(
                "- CatBoost prediction: unavailable."
            )

        evidence_lines.append(
            "- Weather: "
            f"{self._format_saas_weather(weather)}"
        )

        evidence_lines.append(
            f"- Route alternatives: {len(route_options)}."
        )

        for route in self._format_saas_routes(
            route_options
        ):
            evidence_lines.append(
                f"- {route}"
            )

        evidence_lines.append(
            f"- Supplier alternatives: {len(supplier_options)}."
        )

        for supplier in self._format_saas_suppliers(
            supplier_options
        ):
            evidence_lines.append(
                f"- {supplier}"
            )

        evidence_lines.append(
            f"- External news records: {len(news_results)}."
        )

        for article in self._format_saas_news(
            news_results
        ):
            evidence_lines.append(
                f"- External news: {article}"
            )

        evidence_lines.append(
            f"- Knowledge-base results: "
            f"{len(knowledge_results)}."
        )

        formatted_evidence = self._format_saas_evidence(
            evidence
        )

        if formatted_evidence:
            evidence_lines.extend(
                formatted_evidence
            )

        has_weather = bool(weather)
        has_routes = bool(route_options)
        has_suppliers = bool(supplier_options)
        has_news = bool(news_results)

        contributor_lines: list[str] = []

        if status.lower() in {
            "delayed",
            "late",
            "exception",
            "cancelled",
        }:
            contributor_lines.append(
                "The shipment status confirms an operational "
                "exception."
            )

        if eta_status == "The estimated arrival time has passed.":
            contributor_lines.append(
                "The estimated arrival time has passed."
            )

        if has_weather:
            contributor_lines.append(
                "Weather data is available as contextual evidence, "
                "but it does not establish weather as the cause."
            )

        if has_routes:
            contributor_lines.append(
                "Alternative road routes were returned by the "
                "routing service, but route availability does not "
                "establish the cause of the delay."
            )

        if has_news:
            contributor_lines.append(
                "External news was returned as contextual evidence; "
                "no shipment-specific causal relationship is assumed."
            )

        if not contributor_lines:
            contributor_lines.append(
                "No confirmed disruption contributor was established "
                "from the available evidence."
            )

        if (
            risk_state == "at_risk"
            and ml_available
            and ml_is_at_risk is False
        ):
            contributor_lines.append(
                "The operational risk state and CatBoost classification "
                "differ: the shipment is operationally delayed, while "
                "the model probability remains below its decision "
                "threshold."
            )

        if risk_state == "at_risk":
            summary = (
                f"Shipment {shipment_id} is currently classified as "
                "at risk based on its operational status and available "
                "temporal evidence."
            )
        else:
            summary = (
                f"Shipment {shipment_id} is currently classified as "
                f"{risk_state} based on the available shipment data."
            )

        if ml_available and ml_probability is not None:
            summary += (
                " CatBoost provides a separate probabilistic estimate "
                f"of {float(ml_probability) * 100:.1f}%."
            )

        route_review = (
            f"{len(route_options)} route alternative(s)"
            if route_options
            else "no route alternatives"
        )

        supplier_review = (
            f"{len(supplier_options)} supplier alternative(s)"
            if supplier_options
            else "no supplier alternatives"
        )

        return (
            "EXECUTIVE SUMMARY\n"
            f"{summary}\n\n"
            "RISK ASSESSMENT\n"
            f"Operational risk state: {risk_state}.\n"
            + (
                (
                    f"CatBoost estimates a "
                    f"{float(ml_probability) * 100:.1f}% probability "
                    f"of late delivery. "
                    f"The decision threshold is "
                    f"{float(ml_threshold) * 100:.1f}%, so the model "
                    f"classification is "
                    f"{'at risk' if ml_is_at_risk else 'not at risk'}."
                )
                if ml_available
                and ml_probability is not None
                and ml_threshold is not None
                else
                "CatBoost prediction is unavailable because the "
                "required model features were not supplied."
            )
            + "\n\n"
            "EVIDENCE\n"
            + "\n".join(evidence_lines)
            + "\n\n"
            "LIKELY CONTRIBUTORS\n"
            + "\n".join(
                f"- {line}"
                for line in contributor_lines
            )
            + "\n\n"
            "RECOMMENDED HUMAN REVIEW\n"
            f"Review the confirmed shipment status, ETA, model estimate, "
            f"weather context, route options, and applicable operational "
            f"procedures. The investigation returned {route_review} and "
            f"{supplier_review}. These should be verified before any "
            "operational decision is made. SentinelAI does not "
            "automatically execute rerouting, carrier changes, or "
            "supplier changes.\n\n"
            "UNCERTAINTIES\n"
            f"Weather evidence is "
            f"{'available' if has_weather else 'unavailable'}. "
            f"External news returned {len(news_results)} record(s). "
            "External evidence may be incomplete or unrelated to the "
            "specific shipment. The final operational decision remains "
            "with a human operator."
        )