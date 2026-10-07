from app.schemas.shipment import Shipment

# Placeholder scoring: late rate for each shipping mode, measured from DataCo
# (see scripts/check_dataco_orders.py). The ML lead replaces score_shipment().
SHIPPING_MODE_LATE_RATE = {
    "First Class": 0.953,
    "Second Class": 0.766,
    "Same Day": 0.457,
    "Standard Class": 0.381,
}
DEFAULT_RATE = 0.55          # overall late rate, used for unknown modes

RISK_THRESHOLD = 0.7         # at or above this, a shipment is flagged


def score_shipment(shipment: Shipment) -> float:
    """Return the estimated probability (0 to 1) that the shipment arrives late."""
    return SHIPPING_MODE_LATE_RATE.get(shipment.shipping_mode, DEFAULT_RATE)


def is_flagged(score: float) -> bool:
    return score >= RISK_THRESHOLD