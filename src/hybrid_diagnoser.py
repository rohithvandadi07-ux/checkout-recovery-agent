"""
Hybrid checkout abandonment diagnosis.

Combines:
1. Explainable rule-based diagnosis.
2. Machine-learning diagnosis.

The hybrid layer does NOT decide whether an action is safe.
That responsibility remains with policy_engine.py.

Design:
    Rule diagnosis + ML diagnosis
              ↓
       Agreement / disagreement
              ↓
       Conservative final diagnosis
              ↓
          Policy engine
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.diagnoser import (
    CONFIDENCE_THRESHOLD,
    diagnose_session,
)

from src.ml_diagnoser import (
    DEFAULT_MODEL_PATH,
    predict_session,
)


# Minimum ML confidence required for the ML result
# to participate in the hybrid decision.
ML_CONFIDENCE_THRESHOLD = 0.50


def _build_reasoning(
    final_cause: str,
    rule_result: dict[str, Any],
    ml_result: dict[str, Any],
    agreement: bool,
) -> str:
    """Build human-readable hybrid diagnosis reasoning."""

    rule_cause = rule_result["cause"]
    rule_confidence = rule_result["confidence"]

    ml_cause = ml_result["cause"]
    ml_confidence = ml_result["confidence"]

    if agreement:
        return (
            f"Rule-based diagnosis and ML diagnosis agree on "
            f"'{final_cause}'. The rule engine confidence is "
            f"{rule_confidence:.2f} and the ML confidence is "
            f"{ml_confidence:.2f}, providing corroborating evidence."
        )

    if final_cause == rule_cause:
        return (
            f"The rule-based diagnosis selected '{rule_cause}' "
            f"with confidence {rule_confidence:.2f}, while the ML "
            f"model predicted '{ml_cause}' with confidence "
            f"{ml_confidence:.2f}. The rule-based result was retained "
            "because it provides the explainable safety baseline."
        )

    if final_cause == ml_cause:
        return (
            f"The ML model predicted '{ml_cause}' with confidence "
            f"{ml_confidence:.2f}, while the rule-based diagnosis "
            f"selected '{rule_cause}' with confidence "
            f"{rule_confidence:.2f}. The ML result was retained "
            "because it had stronger supported confidence."
        )

    return (
        "The rule-based and ML diagnosis disagreed. "
        f"The final diagnosis was conservatively selected as "
        f"'{final_cause}'."
    )


def diagnose_hybrid(
    session: dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """
    Produce a hybrid diagnosis for an abandoned checkout.

    Decision logic:

    1. Run the existing explainable rule diagnosis.
    2. Run the ML diagnosis.
    3. If both agree, retain the shared diagnosis and combine
       their confidence conservatively.
    4. If they disagree, retain the diagnosis with the stronger
       confidence.
    5. If neither result is sufficiently confident, return unknown.
    6. Never allow this function to authorize an action.

    Returns:
        cause
        confidence
        reasoning
        diagnosis_source
        rule_cause
        rule_confidence
        ml_cause
        ml_confidence
        agreement
        ml_probabilities
    """

    if session.get("status") != "abandoned":
        raise ValueError(
            "Hybrid diagnosis is only applicable "
            "to abandoned sessions."
        )

    rule_result = diagnose_session(
        session
    )

    ml_result = predict_session(
        session,
        model_path=model_path,
    )

    rule_cause = rule_result["cause"]
    rule_confidence = float(
        rule_result["confidence"]
    )

    ml_cause = ml_result["cause"]
    ml_confidence = float(
        ml_result["confidence"]
    )

    agreement = (
        rule_cause == ml_cause
    )

    rule_actionable = (
        rule_cause != "unknown"
        and rule_confidence >= CONFIDENCE_THRESHOLD
    )

    ml_actionable = (
        ml_cause != "unknown"
        and ml_confidence >= ML_CONFIDENCE_THRESHOLD
    )

    # ---------------------------------------------------------------
    # Case 1: Both systems agree.
    #
    # Agreement is the strongest evidence because two independent
    # diagnosis mechanisms reached the same conclusion.
    # ---------------------------------------------------------------

    if agreement and rule_actionable and ml_actionable:

        final_cause = rule_cause

        # Conservative confidence combination.
        #
        # We do not simply add the probabilities. Instead we use
        # the weaker of the two signals, preventing one confident
        # model from hiding a weak second signal.
        final_confidence = min(
            rule_confidence,
            ml_confidence,
        )

        source = "hybrid_agreement"

    # ---------------------------------------------------------------
    # Case 2: Rule diagnosis is actionable but ML is not.
    #
    # Preserve the explainable baseline.
    # ---------------------------------------------------------------

    elif rule_actionable and not ml_actionable:

        final_cause = rule_cause
        final_confidence = rule_confidence
        source = "rule_fallback"

    # ---------------------------------------------------------------
    # Case 3: ML diagnosis is actionable but rule diagnosis is not.
    #
    # ML can contribute, but we keep the confidence exactly as
    # supplied by the model rather than artificially increasing it.
    # ---------------------------------------------------------------

    elif ml_actionable and not rule_actionable:

        final_cause = ml_cause
        final_confidence = ml_confidence
        source = "ml_fallback"

    # ---------------------------------------------------------------
    # Case 4: Both systems disagree but both are actionable.
    #
    # Use the stronger confidence signal.
    # The policy engine remains the safety boundary.
    # ---------------------------------------------------------------

    elif rule_actionable and ml_actionable:

        if rule_confidence >= ml_confidence:
            final_cause = rule_cause
            final_confidence = rule_confidence
            source = "rule_preferred"

        else:
            final_cause = ml_cause
            final_confidence = ml_confidence
            source = "ml_preferred"

    # ---------------------------------------------------------------
    # Case 5: Neither diagnosis has sufficient evidence.
    # ---------------------------------------------------------------

    else:

        final_cause = "unknown"
        final_confidence = max(
            rule_confidence,
            ml_confidence,
        )

        source = "insufficient_evidence"

    reasoning = _build_reasoning(
        final_cause=final_cause,
        rule_result=rule_result,
        ml_result=ml_result,
        agreement=agreement,
    )

    return {
        "cause": final_cause,
        "confidence": round(
            final_confidence,
            4,
        ),
        "reasoning": reasoning,
        "diagnosis_source": source,
        "rule_cause": rule_cause,
        "rule_confidence": round(
            rule_confidence,
            4,
        ),
        "ml_cause": ml_cause,
        "ml_confidence": round(
            ml_confidence,
            4,
        ),
        "agreement": agreement,
        "ml_probabilities": ml_result[
            "probabilities"
        ],
    }
