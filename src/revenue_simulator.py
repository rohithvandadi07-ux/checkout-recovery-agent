"""
Deterministic revenue recovery simulator.

This module estimates potential revenue recovered by the
checkout recovery agent.

IMPORTANT:
    This is a simulation only.
    It does not represent actual Razorpay revenue or
    real customer behavior.
"""

from __future__ import annotations

import hashlib
from typing import Any


# -------------------------------------------------------------------
# Simulation assumptions
# -------------------------------------------------------------------
#
# These are experimental assumptions, not measured business results.
# They represent the probability that an eligible recovery action
# successfully brings the customer back to checkout.
# -------------------------------------------------------------------

RECOVERY_PROBABILITIES = {
    "otp_timeout": 0.65,
    "bank_page_timeout": 0.55,
    "network_drop": 0.45,
    "distraction_exit": 0.40,
    "price_shock": 0.25,
}


def deterministic_score(session_id: str) -> float:
    """
    Convert a session ID into a deterministic value in [0, 1).

    Using SHA-256 means the same session always produces
    the same simulation result across different runs.
    """

    digest = hashlib.sha256(
        session_id.encode("utf-8")
    ).hexdigest()

    integer_value = int(digest[:16], 16)

    return integer_value / float(16**16)


def simulate_recovery(
    session: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Simulate whether an agent intervention recovers revenue
    for one session.

    Only sessions approved by the policy engine for recovery
    are eligible.

    Returns a structured simulation result.
    """

    session_id = session["session_id"]
    cart_value = float(
        session.get("cart_value", 0.0)
    )
    status = session.get("status")

    diagnosis = result.get("diagnosis")
    policy = result.get("policy", {})

    cause = (
        diagnosis.get("cause")
        if diagnosis
        else None
    )

    decision = policy.get("decision")

    probability = RECOVERY_PROBABILITIES.get(
        cause,
        0.0,
    )

    # ---------------------------------------------------------------
    # Only abandoned sessions are candidates for revenue recovery.
    # Completed sessions must never be treated as revenue at risk.
    # ---------------------------------------------------------------

    if status != "abandoned":
        return {
            "session_id": session_id,
            "status": status,
            "cause": cause,
            "cart_value": cart_value,
            "eligible": False,
            "recovery_probability": 0.0,
            "recovered": False,
            "recovered_revenue": 0.0,
            "reason": (
                "Session was not abandoned and is therefore "
                "not eligible for recovery."
            ),
        }

    # ---------------------------------------------------------------
    # No recovery action means no simulated recovery.
    # ---------------------------------------------------------------

    if decision != "recover":
        return {
            "session_id": session_id,
            "status": status,
            "cause": cause,
            "cart_value": cart_value,
            "eligible": False,
            "recovery_probability": probability,
            "recovered": False,
            "recovered_revenue": 0.0,
            "reason": (
                "Session was not approved for automatic "
                "recovery."
            ),
        }

    # ---------------------------------------------------------------
    # A recovery action is only eligible if the cause has a
    # defined recovery probability.
    # ---------------------------------------------------------------

    if probability <= 0.0:
        return {
            "session_id": session_id,
            "status": status,
            "cause": cause,
            "cart_value": cart_value,
            "eligible": False,
            "recovery_probability": 0.0,
            "recovered": False,
            "recovered_revenue": 0.0,
            "reason": (
                "No recovery probability is defined for "
                f"cause '{cause}'."
            ),
        }

    # ---------------------------------------------------------------
    # Deterministic simulation.
    # ---------------------------------------------------------------

    score = deterministic_score(session_id)

    recovered = score < probability

    recovered_revenue = (
        cart_value
        if recovered
        else 0.0
    )

    return {
        "session_id": session_id,
        "status": status,
        "cause": cause,
        "cart_value": cart_value,
        "eligible": True,
        "recovery_probability": probability,
        "simulation_score": score,
        "recovered": recovered,
        "recovered_revenue": recovered_revenue,
        "reason": (
            "Simulated recovery succeeded."
            if recovered
            else "Simulated recovery did not succeed."
        ),
    }


def simulate_results(
    sessions: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Simulate revenue recovery for multiple sessions.

    The sessions and agent results must correspond by position.
    """

    if len(sessions) != len(results):
        raise ValueError(
            "Sessions and results must have the same length."
        )

    return [
        simulate_recovery(
            session,
            result,
        )
        for session, result in zip(
            sessions,
            results,
        )
    ]


def summarize_revenue(
    simulations: list[dict[str, Any]],
) -> dict[str, float | int]:
    """
    Calculate aggregate revenue recovery metrics.

    Value at risk is calculated only from abandoned sessions.
    Completed sessions are excluded because their checkout
    value is not at risk.
    """

    value_at_risk = sum(
        float(item["cart_value"])
        for item in simulations
        if item.get("status") == "abandoned"
    )

    eligible_value = sum(
        float(item["cart_value"])
        for item in simulations
        if item["eligible"]
    )

    recovered_revenue = sum(
        float(item["recovered_revenue"])
        for item in simulations
    )

    eligible_sessions = sum(
        1
        for item in simulations
        if item["eligible"]
    )

    successful_recoveries = sum(
        1
        for item in simulations
        if item["recovered"]
    )

    total_sessions = len(simulations)

    return {
        "total_sessions": total_sessions,
        "value_at_risk": value_at_risk,
        "eligible_sessions": eligible_sessions,
        "eligible_value": eligible_value,
        "successful_recoveries": successful_recoveries,
        "recovered_revenue": recovered_revenue,
        "recovery_rate": (
            successful_recoveries / eligible_sessions
            if eligible_sessions
            else 0.0
        ),
        "revenue_recovery_rate": (
            recovered_revenue / eligible_value
            if eligible_value
            else 0.0
        ),
    }