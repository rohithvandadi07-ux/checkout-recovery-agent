"""
Checkout recovery policy engine.

The policy engine converts a diagnosis into a bounded decision.

Responsibilities:
- Decide whether automated recovery is allowed.
- Prevent action when confidence is too low.
- Prevent recovery actions for suspicious/fraud cases.
- Keep interventions limited and explainable.

The policy engine does NOT diagnose the customer.
"""

from __future__ import annotations

from typing import Any

from src.diagnoser import CONFIDENCE_THRESHOLD


# Maximum cart value for an automatic recovery intervention.
MAX_AUTO_RECOVERY_VALUE = 10000.0


def evaluate_policy(
    session: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    """
    Decide what the recovery system is allowed to do.

    Possible decisions:
        recover
        no_action
        escalate
    """

    if session.get("status") != "abandoned":
        return {
            "decision": "no_action",
            "action": None,
            "reason": "Session was not abandoned.",
        }

    cause = diagnosis.get("cause")
    confidence = diagnosis.get("confidence", 0.0)
    cart_value = session.get("cart_value", 0.0)

    # ---------------------------------------------------------------
    # Safety gate 1: insufficient confidence
    # ---------------------------------------------------------------

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "decision": "no_action",
            "action": None,
            "reason": (
                f"Diagnosis confidence ({confidence:.2f}) is below "
                f"the minimum policy threshold "
                f"({CONFIDENCE_THRESHOLD:.2f})."
            ),
        }

    # ---------------------------------------------------------------
    # Safety gate 2: unknown cause
    # ---------------------------------------------------------------

    if cause == "unknown":
        return {
            "decision": "no_action",
            "action": None,
            "reason": (
                "The abandonment cause is unknown, so an "
                "automated intervention is not justified."
            ),
        }

    # ---------------------------------------------------------------
    # Safety gate 3: suspected fraud
    # ---------------------------------------------------------------

    if cause == "fraud_suspected":
        return {
            "decision": "escalate",
            "action": "manual_review",
            "reason": (
                "Fraud is suspected. Automated recovery or "
                "incentives are prohibited; the session requires "
                "review."
            ),
        }

    # ---------------------------------------------------------------
    # Safety gate 4: insufficient funds
    #
    # Even if this cause is ever supplied by a future detector,
    # don't automatically offer incentives.
    # ---------------------------------------------------------------

    if cause == "insufficient_funds":
        return {
            "decision": "no_action",
            "action": None,
            "reason": (
                "Insufficient funds should not trigger an "
                "automatic recovery intervention."
            ),
        }

    # ---------------------------------------------------------------
    # Safety gate 5: high-value transactions
    # ---------------------------------------------------------------

    if cart_value > MAX_AUTO_RECOVERY_VALUE:
        return {
            "decision": "escalate",
            "action": "manual_review",
            "reason": (
                f"Cart value ₹{cart_value:,.2f} exceeds the "
                f"automatic recovery limit of "
                f"₹{MAX_AUTO_RECOVERY_VALUE:,.2f}."
            ),
        }

    # ---------------------------------------------------------------
    # Bounded recovery actions
    # ---------------------------------------------------------------

    recovery_actions = {
        "otp_timeout": "send_payment_retry_prompt",
        "bank_page_timeout": "send_payment_retry_prompt",
        "network_drop": "send_checkout_resume_prompt",
        "price_shock": "send_cart_reminder",
        "distraction_exit": "send_checkout_resume_prompt",
    }

    action = recovery_actions.get(cause)

    if action is None:
        return {
            "decision": "no_action",
            "action": None,
            "reason": (
                f"No approved automated action exists for "
                f"diagnosis '{cause}'."
            ),
        }

    return {
        "decision": "recover",
        "action": action,
        "reason": (
            f"Diagnosis '{cause}' has sufficient confidence "
            "and is eligible for a bounded recovery intervention."
        ),
    }
