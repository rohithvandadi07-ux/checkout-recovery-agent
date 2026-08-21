"""
Explainable checkout abandonment diagnosis engine.

The diagnoser uses only observable checkout features.

It NEVER reads the hidden `true_cause` field.

Each possible cause receives an evidence score.
The strongest supported cause is selected only when
the evidence is sufficiently strong.
"""

from __future__ import annotations

from typing import Any


CONFIDENCE_THRESHOLD = 0.50


CAUSES = [
    "otp_timeout",
    "price_shock",
    "network_drop",
    "bank_page_timeout",
    "insufficient_funds",
    "distraction_exit",
    "fraud_suspected",
    "unknown",
]


def _score_causes(
    session: dict[str, Any],
) -> dict[str, float]:
    """
    Calculate explainable evidence scores for every cause.

    Scores are based only on observable session features.
    """

    payment_method = session["payment_method"]
    device = session["device"]
    duration = session["checkout_duration_minutes"]
    cart_value = session["cart_value"]

    scores = {
        cause: 0.0
        for cause in CAUSES
    }

    # ---------------------------------------------------------------
    # OTP timeout
    # ---------------------------------------------------------------

    if payment_method == "UPI":
        scores["otp_timeout"] += 0.35

    if duration <= 1.2:
        scores["otp_timeout"] += 0.45

    if payment_method == "UPI" and duration <= 1.2:
        scores["otp_timeout"] += 0.15

    # ---------------------------------------------------------------
    # Bank page timeout
    # ---------------------------------------------------------------

    if payment_method == "netbanking":
        scores["bank_page_timeout"] += 0.40

    if (
        payment_method == "netbanking"
        and 3.5 <= duration <= 9.0
    ):
        scores["bank_page_timeout"] += 0.40

    if (
        payment_method == "netbanking"
        and 3.5 <= duration <= 9.0
    ):
        scores["bank_page_timeout"] += 0.15

    # ---------------------------------------------------------------
    # Price shock
    # ---------------------------------------------------------------

    if cart_value > 5000:
        scores["price_shock"] += 0.40

    if 1.2 <= duration <= 4.0:
        scores["price_shock"] += 0.30

    if cart_value > 5000 and 1.2 <= duration <= 4.0:
        scores["price_shock"] += 0.15

    # ---------------------------------------------------------------
    # Network drop
    # ---------------------------------------------------------------

    if device == "mobile":
        scores["network_drop"] += 0.20

    if duration <= 0.8:
        scores["network_drop"] += 0.35

    if device == "mobile" and duration <= 0.8:
        scores["network_drop"] += 0.20

    # ---------------------------------------------------------------
    # Distraction exit
    # ---------------------------------------------------------------

    if duration > 10.0:
        scores["distraction_exit"] += 0.70

    if device == "mobile":
        scores["distraction_exit"] += 0.10

    # ---------------------------------------------------------------
    # Fraud suspected
    #
    # This deliberately requires BOTH strong signals:
    # very high cart value AND extremely short checkout.
    # ---------------------------------------------------------------

    if cart_value > 15000:
        scores["fraud_suspected"] += 0.45

    if duration < 0.5:
        scores["fraud_suspected"] += 0.40

    if cart_value > 15000 and duration < 0.5:
        scores["fraud_suspected"] += 0.15

    # ---------------------------------------------------------------
    # Insufficient funds
    #
    # No reliable observable signal is available in our dataset.
    # Therefore this intentionally receives no evidence.
    # ---------------------------------------------------------------

    scores["insufficient_funds"] = 0.0

    return scores


def _build_reasoning(
    cause: str,
    session: dict[str, Any],
) -> str:
    """Create human-readable reasoning for the diagnosis."""

    payment_method = session["payment_method"]
    device = session["device"]
    duration = session["checkout_duration_minutes"]
    cart_value = session["cart_value"]

    if cause == "otp_timeout":
        return (
            f"UPI was used and checkout ended after "
            f"{duration:.2f} minutes, providing evidence "
            "consistent with OTP timeout."
        )

    if cause == "bank_page_timeout":
        return (
            f"Netbanking was used and checkout lasted "
            f"{duration:.2f} minutes, consistent with "
            "a bank-page timeout."
        )

    if cause == "price_shock":
        return (
            f"The cart value was ₹{cart_value:,.2f} and "
            f"checkout lasted {duration:.2f} minutes, "
            "providing evidence consistent with "
            "price-related drop-off."
        )

    if cause == "network_drop":
        return (
            f"The session used {device} and ended after "
            f"{duration:.2f} minutes, providing evidence "
            "consistent with a possible network interruption."
        )

    if cause == "distraction_exit":
        return (
            f"Checkout remained active for {duration:.2f} "
            "minutes before abandonment, consistent with "
            "a delayed or distraction-driven exit."
        )

    if cause == "fraud_suspected":
        return (
            f"The cart value was ₹{cart_value:,.2f} and "
            f"checkout ended after only {duration:.2f} minutes, "
            "creating a high-value, rapid-abandonment pattern "
            "that warrants fraud review."
        )

    return (
        "Available checkout telemetry does not provide "
        "enough evidence for a reliable diagnosis."
    )


def diagnose_session(
    session: dict[str, Any],
) -> dict[str, Any]:
    """
    Diagnose one abandoned checkout session.

    Returns:
        cause
        confidence
        reasoning
    """

    if session.get("status") != "abandoned":
        raise ValueError(
            "Diagnosis is only applicable to abandoned sessions."
        )

    scores = _score_causes(session)

    # Ignore "unknown" while selecting the strongest
    # evidence-supported cause.
    candidate_scores = {
        cause: score
        for cause, score in scores.items()
        if cause != "unknown"
    }

    best_cause = max(
        candidate_scores,
        key=candidate_scores.get,
    )

    best_score = candidate_scores[best_cause]

    # If evidence is too weak, explicitly return unknown.
    if best_score < CONFIDENCE_THRESHOLD:
        return {
            "cause": "unknown",
            "confidence": round(
                max(0.20, best_score),
                2,
            ),
            "reasoning": _build_reasoning(
                "unknown",
                session,
            ),
        }

    # Convert evidence score into a bounded confidence value.
    confidence = round(
        min(best_score, 0.95),
        2,
    )

    return {
        "cause": best_cause,
        "confidence": confidence,
        "reasoning": _build_reasoning(
            best_cause,
            session,
        ),
    }


def is_actionable(
    diagnosis: dict[str, Any],
) -> bool:
    """
    Determine whether diagnosis confidence is high enough
    for the policy layer to consider automated action.

    This does NOT authorize an action.
    """

    return (
        diagnosis["confidence"]
        >= CONFIDENCE_THRESHOLD
    )