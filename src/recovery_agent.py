"""
Checkout Recovery Agent.

This module orchestrates:
1. Session validation
2. Hybrid diagnosis
3. Bounded policy evaluation
4. Simulated recovery execution
5. Audit logging

The hybrid diagnosis combines an explainable rule-based
diagnoser with a machine-learning model.

No real payment, refund, or customer communication
is performed.
"""

from __future__ import annotations

from typing import Any

from src.audit_logger import log_session_decision
from src.hybrid_diagnoser import diagnose_hybrid
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
    audit_path=None,
) -> dict[str, Any]:
    """
    Process one checkout session through the recovery pipeline.

    Pipeline:

        session
          ↓
        validation
          ↓
        hybrid diagnosis
          ↓
        policy
          ↓
        simulated execution
          ↓
        audit log
    """

    status = session.get("status")

    if status == "completed":
        diagnosis = None

        policy = {
            "decision": "no_action",
            "action": None,
            "reason": (
                "Session was completed successfully."
            ),
        }

        execution = {
            "execution_status": "not_executed",
            "execution_message": (
                "Completed sessions are never touched."
            ),
        }

    elif status == "abandoned":
        # -----------------------------------------------------------
        # Hybrid diagnosis
        # -----------------------------------------------------------

        diagnosis = diagnose_hybrid(
            session
        )

        # -----------------------------------------------------------
        # Safety policy
        # -----------------------------------------------------------

        policy = evaluate_policy(
            session,
            diagnosis,
        )

        # -----------------------------------------------------------
        # Bounded simulated execution
        # -----------------------------------------------------------

        execution = execute_action(
            session,
            policy,
        )

    else:
        raise ValueError(
            f"Unsupported session status: {status}"
        )

    # ---------------------------------------------------------------
    # Audit every session decision
    # ---------------------------------------------------------------

    audit_record = log_session_decision(
        session=session,
        diagnosis=diagnosis,
        policy=policy,
        execution=execution,
        audit_path=audit_path,
    )

    return {
        "session_id": session["session_id"],
        "diagnosis": diagnosis,
        "policy": policy,
        "execution": execution,
        "audit": audit_record,
    }


def process_sessions(
    sessions: list[dict[str, Any]],
    audit_path=None,
) -> list[dict[str, Any]]:
    """Process multiple checkout sessions."""

    return [
        process_session(
            session,
            audit_path,
        )
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