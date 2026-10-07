# Shipment Disruption Response Procedure

## Purpose

This procedure defines the operational response for a shipment identified by SentinelAI as being at elevated risk of late delivery.

SentinelAI provides decision support. It does not automatically reroute shipments, replace suppliers, cancel orders, or make operational decisions without human review.

## Initial Risk Review

When a shipment is flagged as at risk, first confirm the shipment identity and current shipment status.

Review:

- shipment identifier
- destination country and region
- shipping mode
- scheduled shipping window
- product category
- model-estimated late-delivery probability
- current operational signals

The historical risk model is an early-warning signal derived from historical shipment patterns. It should not be treated as proof that a shipment will be late.

## Evidence Review

Review available operational evidence before recommending an intervention.

Relevant evidence may include:

- shipment status
- weather conditions affecting the destination
- route conditions or available route alternatives
- supplier alternatives
- disruption-related news
- applicable operational procedures

Evidence from external services should be treated according to its source and freshness.

A missing signal must not be treated as evidence that no disruption exists.

## Route Assessment

If route-related disruption is identified, review available alternative routes.

For each candidate route, consider:

- shipping mode
- destination compatibility
- route availability
- reliability information
- operational constraints
- potential downstream impact

A route alternative must not be presented as confirmed availability unless the underlying source explicitly confirms availability.

For demo or synthetic route data, clearly identify the information as demonstration data.

## Supplier Assessment

If supplier disruption could affect shipment continuity, review available supplier alternatives.

Consider:

- product category compatibility
- destination compatibility
- supplier reliability information
- known operational constraints
- whether substitution is feasible

Supplier information derived from demonstration datasets must be clearly identified as synthetic or illustrative.

Do not infer supplier identity or reliability from unrelated DataCo customer, product, or order identifiers.

## Weather Assessment

Weather should be considered when it can plausibly affect the shipment or destination.

Relevant signals include:

- precipitation
- wind
- temperature
- weather conditions
- observation or forecast time

Weather information should be reported with its source and observation time where available.

Weather alone should not be used to assert that a shipment will be delayed.

## News Assessment

Disruption-related news may provide secondary contextual evidence.

Potential topics include:

- severe weather
- port disruption
- transportation disruption
- strikes
- infrastructure disruption
- regional supply-chain disruption

News should be treated as contextual evidence rather than definitive proof of an operational event.

If news retrieval fails or is unavailable, the analysis should continue using the remaining evidence sources.

## Escalation

Escalate a shipment for human operational review when:

- the model identifies elevated late-delivery risk and supporting evidence exists;
- multiple independent signals indicate a possible disruption;
- the shipment may create downstream inventory or customer impact;
- available alternatives require an operational decision;
- evidence is conflicting or insufficient for a confident recommendation.

Escalation means presenting the evidence and recommended next steps to an authorized human decision-maker.

## Recommended Response

A SentinelAI operational briefing should distinguish clearly between:

1. What the system knows.
2. What the system estimates.
3. What external evidence indicates.
4. What remains uncertain.
5. What a human operator should review next.

The briefing should never present an estimate as a confirmed operational fact.

## Evidence and Traceability

Every important claim in an operational briefing should be traceable to one of:

- the shipment record;
- the historical risk model;
- a weather observation or forecast;
- a route data source;
- a supplier data source;
- a retrieved procedure;
- a news source.

If evidence is unavailable, the system should explicitly state that the information could not be verified.

## Human Decision Rule

SentinelAI is a decision-support system.

The final operational decision remains with the human operator.

The system may identify risk, investigate possible causes, retrieve relevant procedures, and present alternatives. It must not independently execute rerouting, supplier substitution, shipment cancellation, or other operational actions.