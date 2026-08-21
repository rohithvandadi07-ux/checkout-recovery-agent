from src.recovery_agent import (
    execute_action,
    process_session,
    process_sessions,
    summarize_results,
)


def make_session(
    session_id="cs_test",
    status="abandoned",
    cart_value=2500.0,
    payment_method="UPI",
    device="mobile",
    duration=0.8,
):
    return {
        "session_id": session_id,
        "cart_value": cart_value,
        "payment_method": payment_method,
        "device": device,
        "checkout_duration_minutes": duration,
        "status": status,
    }


def test_otp_session_is_recovered():
    session = make_session(
        payment_method="UPI",
        duration=0.8,
    )

    result = process_session(session)

    assert result["diagnosis"]["cause"] == "otp_timeout"
    assert result["policy"]["decision"] == "recover"
    assert (
        result["execution"]["execution_status"]
        == "simulated"
    )


def test_unknown_session_gets_no_action():
    session = make_session(
        payment_method="card",
        device="desktop",
        duration=5.0,
        cart_value=2500.0,
    )

    result = process_session(session)

    assert result["diagnosis"]["cause"] == "unknown"
    assert result["policy"]["decision"] == "no_action"
    assert (
        result["execution"]["execution_status"]
        == "not_executed"
    )


def test_fraud_session_is_escalated():
    session = make_session(
        payment_method="card",
        device="desktop",
        duration=0.3,
        cart_value=20000.0,
    )

    result = process_session(session)

    assert result["diagnosis"]["cause"] == "fraud_suspected"
    assert result["policy"]["decision"] == "escalate"
    assert result["policy"]["action"] == "manual_review"
    assert (
        result["execution"]["execution_status"]
        == "simulated"
    )


def test_completed_session_is_never_touched():
    session = make_session(
        status="completed",
    )

    result = process_session(session)

    assert result["diagnosis"] is None
    assert result["policy"]["decision"] == "no_action"
    assert (
        result["execution"]["execution_status"]
        == "not_executed"
    )


def test_process_multiple_sessions():
    sessions = [
        make_session(
            session_id="cs_001",
            payment_method="UPI",
            duration=0.8,
        ),
        make_session(
            session_id="cs_002",
            payment_method="card",
            device="desktop",
            duration=5.0,
        ),
    ]

    results = process_sessions(sessions)

    assert len(results) == 2
    assert results[0]["policy"]["decision"] == "recover"
    assert results[1]["policy"]["decision"] == "no_action"


def test_manual_review_execution():
    session = make_session(
        cart_value=20000.0,
    )

    decision = {
        "decision": "escalate",
        "action": "manual_review",
        "reason": "test",
    }

    result = execute_action(
        session,
        decision,
    )

    assert result["execution_status"] == "simulated"
    assert "manual review" in result["execution_message"]


def test_no_action_execution():
    session = make_session()

    decision = {
        "decision": "no_action",
        "action": None,
        "reason": "test",
    }

    result = execute_action(
        session,
        decision,
    )

    assert result["execution_status"] == "not_executed"


def test_recovery_execution_message_contains_session():
    session = make_session(
        session_id="cs_123",
    )

    decision = {
        "decision": "recover",
        "action": "send_cart_reminder",
        "reason": "test",
    }

    result = execute_action(
        session,
        decision,
    )

    assert result["execution_status"] == "simulated"
    assert "cs_123" in result["execution_message"]


def test_summary_counts_results():
    sessions = [
        make_session(
            session_id="cs_001",
            payment_method="UPI",
            duration=0.8,
        ),
        make_session(
            session_id="cs_002",
            payment_method="card",
            device="desktop",
            duration=5.0,
        ),
        make_session(
            session_id="cs_003",
            payment_method="card",
            device="desktop",
            duration=0.3,
            cart_value=20000.0,
        ),
    ]

    results = process_sessions(sessions)

    summary = summarize_results(results)

    assert summary["total_sessions"] == 3
    assert summary["recover"] == 1
    assert summary["no_action"] == 1
    assert summary["escalate"] == 1
    assert summary["simulated_actions"] == 2


def test_invalid_status_raises_error():
    session = make_session(
        status="processing",
    )

    try:
        process_session(session)
        assert False
    except ValueError:
        assert True
