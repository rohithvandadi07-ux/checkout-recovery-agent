import pytest

from src.detector import (
    calculate_risk_summary,
    detect_session,
    detect_risk,
)


def test_completed_session_is_not_at_risk():
    session = {
        "session_id": "cs_test_001",
        "cart_value": 2500.00,
        "status": "completed",
    }

    result = detect_session(session)

    assert result["is_at_risk"] is False
    assert result["status"] == "completed"


def test_abandoned_session_is_at_risk():
    session = {
        "session_id": "cs_test_002",
        "cart_value": 3000.00,
        "status": "abandoned",
    }

    result = detect_session(session)

    assert result["is_at_risk"] is True
    assert result["status"] == "abandoned"
    assert result["cart_value"] == 3000.00


def test_unknown_status_raises_error():
    session = {
        "session_id": "cs_test_003",
        "cart_value": 1000.00,
        "status": "processing",
    }

    with pytest.raises(ValueError):
        detect_session(session)


def test_risk_summary():
    detections = [
        {
            "session_id": "cs_001",
            "is_at_risk": False,
            "cart_value": 1000.00,
            "status": "completed",
            "reason": "completed",
        },
        {
            "session_id": "cs_002",
            "is_at_risk": True,
            "cart_value": 2500.00,
            "status": "abandoned",
            "reason": "abandoned",
        },
        {
            "session_id": "cs_003",
            "is_at_risk": True,
            "cart_value": 1500.00,
            "status": "abandoned",
            "reason": "abandoned",
        },
    ]

    summary = calculate_risk_summary(detections)

    assert summary["total_sessions"] == 3
    assert summary["completed_sessions"] == 1
    assert summary["abandoned_sessions"] == 2
    assert summary["total_value_at_risk"] == 4000.00


def test_detect_risk_processes_all_sessions():
    sessions = [
        {
            "session_id": "cs_001",
            "cart_value": 1000.00,
            "status": "completed",
        },
        {
            "session_id": "cs_002",
            "cart_value": 2000.00,
            "status": "abandoned",
        },
    ]

    results = detect_risk(sessions)

    assert len(results) == 2
    assert results[0]["is_at_risk"] is False
    assert results[1]["is_at_risk"] is True
