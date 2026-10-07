from __future__ import annotations

import os
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