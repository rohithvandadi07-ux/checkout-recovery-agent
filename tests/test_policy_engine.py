import pytest

from src.policy_engine import (
    MAX_AUTO_RECOVERY_VALUE,
    evaluate_policy,
)


def make_session(
    cart_value=2500.0,
    status="abandoned",
):
    return {
        "session_id": "cs_policy_test",
        "cart_value": cart_value,
        "status": status,
    }


def make_diagnosis(
    cause="otp_timeout",
    confidence=0.80,
):
    return {
        "cause": cause,
        "confidence": confidence,
        "reasoning": "test diagnosis",
    }


def test_otp_timeout_can_be_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("otp_timeout", 0.80),
    )

    assert result["decision"] == "recover"
    assert result["action"] == "send_payment_retry_prompt"


def test_bank_timeout_can_be_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("bank_page_timeout", 0.80),
    )

    assert result["decision"] == "recover"
    assert result["action"] == "send_payment_retry_prompt"


def test_network_drop_can_be_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("network_drop", 0.80),
    )

    assert result["decision"] == "recover"
    assert result["action"] == "send_checkout_resume_prompt"


def test_price_shock_can_be_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("price_shock", 0.80),
    )

    assert result["decision"] == "recover"
    assert result["action"] == "send_cart_reminder"


def test_distraction_can_be_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("distraction_exit", 0.80),
    )

    assert result["decision"] == "recover"
    assert result["action"] == "send_checkout_resume_prompt"


def test_low_confidence_means_no_action():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("otp_timeout", 0.30),
    )

    assert result["decision"] == "no_action"
    assert result["action"] is None


def test_unknown_means_no_action():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("unknown", 0.80),
    )

    assert result["decision"] == "no_action"
    assert result["action"] is None


def test_fraud_is_escalated():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("fraud_suspected", 0.95),
    )

    assert result["decision"] == "escalate"
    assert result["action"] == "manual_review"


def test_insufficient_funds_is_not_automatically_recovered():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("insufficient_funds", 0.80),
    )

    assert result["decision"] == "no_action"
    assert result["action"] is None


def test_high_value_cart_is_escalated():
    result = evaluate_policy(
        make_session(cart_value=15000.0),
        make_diagnosis("otp_timeout", 0.90),
    )

    assert result["decision"] == "escalate"
    assert result["action"] == "manual_review"


def test_completed_session_is_never_recovered():
    result = evaluate_policy(
        make_session(status="completed"),
        make_diagnosis("otp_timeout", 0.90),
    )

    assert result["decision"] == "no_action"
    assert result["action"] is None


def test_unknown_cause_without_approved_action():
    result = evaluate_policy(
        make_session(),
        make_diagnosis("some_new_cause", 0.90),
    )

    assert result["decision"] == "no_action"
    assert result["action"] is None


def test_recovery_limit_is_defined():
    assert MAX_AUTO_RECOVERY_VALUE == 10000.0

