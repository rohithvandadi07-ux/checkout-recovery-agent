import json

from src.audit_logger import (
    create_audit_record,
    log_session_decision,
    read_audit_records,
    write_audit_record,
)


def make_session():
    return {
        "session_id": "cs_audit_001",
        "cart_value": 2500.0,
        "payment_method": "UPI",
        "device": "mobile",
        "checkout_duration_minutes": 0.8,
        "status": "abandoned",
    }


def make_diagnosis():
    return {
        "cause": "otp_timeout",
        "confidence": 0.80,
        "reasoning": "OTP timeout suspected.",
    }


def make_policy():
    return {
        "decision": "recover",
        "action": "send_payment_retry_prompt",
        "reason": "Eligible for bounded recovery.",
    }


def make_execution():
    return {
        "execution_status": "simulated",
        "execution_message": (
            "Simulated recovery action."
        ),
    }


def test_create_audit_record():
    record = create_audit_record(
        make_session(),
        make_diagnosis(),
        make_policy(),
        make_execution(),
    )

    assert record["session_id"] == "cs_audit_001"
    assert record["diagnosis"] == "otp_timeout"
    assert record["confidence"] == 0.80
    assert record["policy_decision"] == "recover"
    assert record["action"] == "send_payment_retry_prompt"
    assert record["execution_status"] == "simulated"
    assert "timestamp" in record


def test_write_audit_record(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    record = create_audit_record(
        make_session(),
        make_diagnosis(),
        make_policy(),
        make_execution(),
    )

    write_audit_record(
        record,
        audit_path,
    )

    assert audit_path.exists()

    lines = audit_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored = json.loads(lines[0])

    assert stored["session_id"] == "cs_audit_001"


def test_multiple_records_are_appended(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    record = create_audit_record(
        make_session(),
        make_diagnosis(),
        make_policy(),
        make_execution(),
    )

    write_audit_record(record, audit_path)
    write_audit_record(record, audit_path)

    lines = audit_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 2


def test_log_session_decision_returns_record(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    record = log_session_decision(
        make_session(),
        make_diagnosis(),
        make_policy(),
        make_execution(),
        audit_path,
    )

    assert record["session_id"] == "cs_audit_001"
    assert audit_path.exists()


def test_read_audit_records(tmp_path):
    audit_path = tmp_path / "audit.jsonl"

    record = create_audit_record(
        make_session(),
        make_diagnosis(),
        make_policy(),
        make_execution(),
    )

    write_audit_record(record, audit_path)
    write_audit_record(record, audit_path)

    records = read_audit_records(audit_path)

    assert len(records) == 2
    assert records[0]["diagnosis"] == "otp_timeout"


def test_read_missing_audit_file(tmp_path):
    audit_path = tmp_path / "does_not_exist.jsonl"

    records = read_audit_records(audit_path)

    assert records == []


def test_completed_session_can_be_logged(tmp_path):
    session = make_session()
    session["status"] = "completed"

    policy = {
        "decision": "no_action",
        "action": None,
        "reason": "Session was completed successfully.",
    }

    execution = {
        "execution_status": "not_executed",
        "execution_message": (
            "Completed sessions are never touched."
        ),
    }

    audit_path = tmp_path / "audit.jsonl"

    record = log_session_decision(
        session,
        None,
        policy,
        execution,
        audit_path,
    )

    assert record["session_id"] == "cs_audit_001"
    assert record["diagnosis"] is None
    assert record["confidence"] is None
    assert record["policy_decision"] == "no_action"
    assert record["action"] is None
