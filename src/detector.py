"""
Checkout risk detection module.

Responsibilities:
- Identify abandoned checkout sessions.
- Leave completed sessions untouched.
- Calculate revenue currently at risk.
- Produce structured detection results.

The detector does NOT diagnose why a customer abandoned checkout.
That responsibility belongs to the diagnosis layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "sessions.json"


def load_sessions(
    data_file: Path = DATA_FILE,
) -> list[dict[str, Any]]:
    """Load checkout sessions from a JSON file."""

    if not data_file.exists():
        raise FileNotFoundError(
            f"Session data not found: {data_file}"
        )

    with data_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        sessions = json.load(file)

    if not isinstance(sessions, list):
        raise ValueError(
            "Session data must contain a JSON list."
        )

    return sessions


def detect_session(
    session: dict[str, Any],
) -> dict[str, Any]:
    """
    Determine whether a checkout session is at risk.

    Completed sessions are never considered at risk.
    Abandoned sessions are considered revenue at risk.
    """

    status = session.get("status")

    if status == "completed":
        return {
            "session_id": session["session_id"],
            "is_at_risk": False,
            "cart_value": session["cart_value"],
            "status": "completed",
            "reason": "Checkout completed successfully.",
        }

    if status == "abandoned":
        return {
            "session_id": session["session_id"],
            "is_at_risk": True,
            "cart_value": session["cart_value"],
            "status": "abandoned",
            "reason": "Checkout was abandoned before payment completion.",
        }

    raise ValueError(
        f"Unknown checkout status: {status}"
    )


def detect_risk(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run risk detection across all checkout sessions."""

    return [
        detect_session(session)
        for session in sessions
    ]


def calculate_risk_summary(
    detections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate batch-level risk metrics."""

    total_sessions = len(detections)

    completed_sessions = sum(
        not detection["is_at_risk"]
        for detection in detections
    )

    abandoned_sessions = sum(
        detection["is_at_risk"]
        for detection in detections
    )

    total_value_at_risk = sum(
        detection["cart_value"]
        for detection in detections
        if detection["is_at_risk"]
    )

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "abandoned_sessions": abandoned_sessions,
        "total_value_at_risk": round(
            total_value_at_risk,
            2,
        ),
    }


def main() -> None:
    """Run the detector against the generated dataset."""

    sessions = load_sessions()

    detections = detect_risk(sessions)

    summary = calculate_risk_summary(detections)

    print("\n" + "=" * 60)
    print("CHECKOUT RISK DETECTION")
    print("=" * 60)

    print(
        f"Total sessions       : "
        f"{summary['total_sessions']}"
    )

    print(
        f"Completed sessions   : "
        f"{summary['completed_sessions']}"
    )

    print(
        f"Abandoned sessions   : "
        f"{summary['abandoned_sessions']}"
    )

    print(
        f"Value at risk        : "
        f"₹{summary['total_value_at_risk']:,.2f}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
