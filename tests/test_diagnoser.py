import pytest

from src.diagnoser import (
    CONFIDENCE_THRESHOLD,
    diagnose_session,
    is_actionable,
)


def make_session(
    payment_method="UPI",
    device="mobile",
    duration=0.8,
    cart_value=2500.0,
):
    return {
        "session_id": "cs_test",
        "payment_method": payment_method,
        "device": device,
        "checkout_duration_minutes": duration,
        "cart_value": cart_value,
        "status": "abandoned",
    }


def test_otp_timeout_diagnosis():
    session = make_session(
        payment_method="UPI",
        duration=0.8,
    )

    result = diagnose_session(session)

    assert result["cause"] == "otp_timeout"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD
    assert "UPI" in result["reasoning"]


def test_bank_page_timeout_diagnosis():
    session = make_session(
        payment_method="netbanking",
        duration=6.0,
    )

    result = diagnose_session(session)

    assert result["cause"] == "bank_page_timeout"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD
    assert "Netbanking" in result["reasoning"]


def test_price_shock_diagnosis():
    session = make_session(
        payment_method="card",
        duration=2.5,
        cart_value=8000.0,
    )

    result = diagnose_session(session)

    assert result["cause"] == "price_shock"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD


def test_network_drop_diagnosis():
    session = make_session(
        device="mobile",
        duration=0.5,
        payment_method="card",
    )

    result = diagnose_session(session)

    assert result["cause"] == "network_drop"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD


def test_distraction_exit_diagnosis():
    session = make_session(
        duration=15.0,
        payment_method="card",
    )

    result = diagnose_session(session)

    assert result["cause"] == "distraction_exit"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD


def test_fraud_diagnosis():
    session = make_session(
        cart_value=20000.0,
        duration=0.3,
        payment_method="card",
    )

    result = diagnose_session(session)

    assert result["cause"] == "fraud_suspected"
    assert result["confidence"] >= CONFIDENCE_THRESHOLD
    assert "high-value" in result["reasoning"]


def test_unknown_when_no_signal_exists():
    session = make_session(
        payment_method="card",
        device="desktop",
        duration=5.0,
        cart_value=2500.0,
    )

    result = diagnose_session(session)

    assert result["cause"] == "unknown"
    assert result["confidence"] < CONFIDENCE_THRESHOLD


def test_completed_session_cannot_be_diagnosed():
    session = make_session()

    session["status"] = "completed"

    with pytest.raises(ValueError):
        diagnose_session(session)


def test_actionable_above_threshold():
    diagnosis = {
        "cause": "otp_timeout",
        "confidence": 0.72,
    }

    assert is_actionable(diagnosis) is True


def test_not_actionable_below_threshold():
    diagnosis = {
        "cause": "unknown",
        "confidence": 0.20,
    }

    assert is_actionable(diagnosis) is False


def test_confidence_threshold():
    assert CONFIDENCE_THRESHOLD == 0.50