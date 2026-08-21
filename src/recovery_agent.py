"""
Checkout Recovery Agent.

This module orchestrates the existing:
1. Risk detector
2. Diagnosis engine
3. Policy engine

It executes only bounded, simulated recovery actions.
No real payment or customer communication is performed.
"""

from __future__ import annotations

from typing import Any

from src.diagnoser import diagnose_session
from src.policy_engine import evaluate_policy


def execute_action(
    session: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a policy decision in simulation mode.

    No external systems are contacted.
    """

    action = decision["action"]

    if action is None:
        return {
            "execution_status": "not_executed",
            "execution_message": "No action was authorized.",
        }

    if action == "manual_review":
        return {
            "execution_status": "simulated",
            "execution_message": (
                "Session was simulated as escalated "
                "to manual review."
            ),
        }

    return {
        "execution_status": "simulated",
        "execution_message": (
            f"Simulated recovery action '{action}' "
            f"for session {session['session_id']}."
        ),
    }


def process_session(
    session: dict[str, Any],
) -> dict[str, Any]:
    """
    Process one checkout session through the recovery pipeline.

    Pipeline:
        session
          ↓
        diagnosis
          ↓
        policy
          ↓
        simulated execution
    """

    # Completed sessions should never enter recovery.
    if session.get("status") == "completed":
        return {
            "session_id": session["session_id"],
            "diagnosis": None,
            "policy": {
                "decision": "no_action",
                "action": None,
                "reason": "Session was completed successfully.",
            },
            "execution": {
                "execution_status": "not_executed",
                "execution_message": (
                    "Completed sessions are never touched."
                ),
            },
        }

    if session.get("status") != "abandoned":
        raise ValueError(
            f"Unsupported session status: {session.get('status')}"
        )

    # Step 1: Diagnose the abandonment.
    diagnosis = diagnose_session(session)

    # Step 2: Apply the safety policy.
    policy = evaluate_policy(
        session,
        diagnosis,
    )

    # Step 3: Execute only the action authorized by policy.
    execution = execute_action(
        session,
        policy,
    )

    return {
        "session_id": session["session_id"],
        "diagnosis": diagnosis,
        "policy": policy,
        "execution": execution,
    }


def process_sessions(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Process multiple checkout sessions."""

    return [
        process_session(session)
        for session in sessions
    ]


def summarize_results(
    results: list[dict[str, Any]],
) -> dict[str, int]:
    """Create high-level execution statistics."""

    return {
        "total_sessions": len(results),
        "recover": sum(
            result["policy"]["decision"] == "recover"
            for result in results
        ),
        "no_action": sum(
            result["policy"]["decision"] == "no_action"
            for result in results
        ),
        "escalate": sum(
            result["policy"]["decision"] == "escalate"
            for result in results
        ),
        "simulated_actions": sum(
            result["execution"]["execution_status"]
            == "simulated"
            for result in results
        ),
    }
