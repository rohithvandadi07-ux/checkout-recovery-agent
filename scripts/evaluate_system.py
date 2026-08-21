"""
System-level evaluation for Checkout Recovery Intelligence.

This script evaluates:
- ML diagnosis performance
- Hybrid diagnosis behavior
- Policy decisions
- Simulated revenue recovery
- Safety outcomes

All results are derived from the existing synthetic dataset
and the production pipeline.
"""

from __future__ import annotations

import json

from src.ml_diagnoser import train_model
from src.recovery_agent import (
    process_sessions,
    summarize_results,
)
from src.revenue_simulator import (
    simulate_results,
    summarize_revenue,
)


DATA_PATH = "data/sessions.json"


def load_sessions() -> list[dict]:
    """Load checkout sessions."""

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def summarize_hybrid(results: list[dict]) -> dict[str, int]:
    """Summarize hybrid diagnosis behavior."""

    summary = {
        "hybrid_agreement": 0,
        "rule_fallback": 0,
        "ml_fallback": 0,
        "rule_preferred": 0,
        "ml_preferred": 0,
        "insufficient_evidence": 0,
    }

    for result in results:
        diagnosis = result.get("diagnosis")

        if diagnosis is None:
            continue

        source = diagnosis.get("diagnosis_source")

        if source in summary:
            summary[source] += 1

    return summary


def summarize_safety(results: list[dict]) -> dict[str, int]:
    """Summarize safety-related decisions."""

    fraud_escalations = 0
    high_value_escalations = 0
    automated_fraud_recoveries = 0

    for result in results:
        diagnosis = result.get("diagnosis")
        policy = result["policy"]

        if diagnosis is None:
            continue

        if diagnosis.get("cause") == "fraud_suspected":
            if policy["decision"] == "escalate":
                fraud_escalations += 1

            if policy["decision"] == "recover":
                automated_fraud_recoveries += 1

        if (
            policy["decision"] == "escalate"
            and "exceeds the automatic recovery limit"
            in policy["reason"]
        ):
            high_value_escalations += 1

    return {
        "fraud_escalations": fraud_escalations,
        "high_value_escalations": high_value_escalations,
        "automated_fraud_recoveries": automated_fraud_recoveries,
    }


def main() -> None:
    """Run complete system evaluation."""

    print()
    print("=" * 72)
    print("CHECKOUT RECOVERY INTELLIGENCE")
    print("SYSTEM EVALUATION")
    print("=" * 72)

    sessions = load_sessions()

    abandoned = sum(
        session["status"] == "abandoned"
        for session in sessions
    )

    completed = sum(
        session["status"] == "completed"
        for session in sessions
    )

    # ---------------------------------------------------------------
    # ML evaluation
    # ---------------------------------------------------------------

    ml_metrics = train_model()

    print()
    print("DATASET")
    print("-" * 72)
    print(f"Total sessions       : {len(sessions)}")
    print(f"Abandoned sessions   : {abandoned}")
    print(f"Completed sessions   : {completed}")

    print()
    print("ML DIAGNOSIS")
    print("-" * 72)
    print(f"Training samples     : {ml_metrics['training_samples']}")
    print(f"Test samples         : {ml_metrics['test_samples']}")
    print(f"Accuracy             : {ml_metrics['accuracy']:.2%}")
    print(
        f"Macro Precision      : "
        f"{ml_metrics['macro_precision']:.2%}"
    )
    print(
        f"Macro Recall         : "
        f"{ml_metrics['macro_recall']:.2%}"
    )
    print(
        f"Macro F1             : "
        f"{ml_metrics['macro_f1']:.2%}"
    )

    # ---------------------------------------------------------------
    # Full recovery pipeline
    # ---------------------------------------------------------------

    results = process_sessions(sessions)

    execution_summary = summarize_results(results)
    hybrid_summary = summarize_hybrid(results)

    simulated = simulate_results(
        sessions,
        results,
    )

    revenue = summarize_revenue(simulated)
    safety = summarize_safety(results)

    print()
    print("HYBRID DIAGNOSIS")
    print("-" * 72)

    for key, value in hybrid_summary.items():
        print(
            f"{key.replace('_', ' ').title():22}: {value}"
        )

    print()
    print("POLICY OUTCOMES")
    print("-" * 72)
    print(
        f"Recover              : "
        f"{execution_summary['recover']}"
    )
    print(
        f"No action            : "
        f"{execution_summary['no_action']}"
    )
    print(
        f"Escalate             : "
        f"{execution_summary['escalate']}"
    )
    print(
        f"Simulated actions    : "
        f"{execution_summary['simulated_actions']}"
    )

    print()
    print("REVENUE IMPACT")
    print("-" * 72)
    print(
        f"Value at risk        : "
        f"₹{revenue['value_at_risk']:,.2f}"
    )
    print(
        f"Eligible sessions    : "
        f"{revenue['eligible_sessions']}"
    )
    print(
        f"Eligible value       : "
        f"₹{revenue['eligible_value']:,.2f}"
    )
    print(
        f"Successful recoveries: "
        f"{revenue['successful_recoveries']}"
    )
    print(
        f"Recovered revenue    : "
        f"₹{revenue['recovered_revenue']:,.2f}"
    )
    print(
        f"Recovery rate        : "
        f"{revenue['recovery_rate']:.2%}"
    )
    print(
        f"Revenue recovery     : "
        f"{revenue['revenue_recovery_rate']:.2%}"
    )

    print()
    print("SAFETY")
    print("-" * 72)
    print(
        f"Fraud escalations    : "
        f"{safety['fraud_escalations']}"
    )
    print(
        f"High-value escalations: "
        f"{safety['high_value_escalations']}"
    )
    print(
        f"Automated fraud      : "
        f"{safety['automated_fraud_recoveries']}"
    )

    print()
    print("=" * 72)
    print("EVALUATION COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
