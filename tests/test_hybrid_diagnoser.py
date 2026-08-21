import pytest

from src.hybrid_diagnoser import (
    diagnose_hybrid,
)


def make_session(
    payment_method="UPI",
    device="mobile",
    duration=0.8,
    cart_value=2500.0,
):
    return {
        "session_id": "cs_hybrid_test",
        "payment_method": payment_method,
        "device": device,
        "checkout_duration_minutes": duration,
        "cart_value": cart_value,
        "status": "abandoned",
    }


def test_hybrid_diagnosis_returns_required_fields():
    session = make_session()

    result = diagnose_hybrid(
        session
    )

    assert "cause" in result
    assert "confidence" in result
    assert "reasoning" in result
    assert "diagnosis_source" in result
    assert "rule_cause" in result
    assert "rule_confidence" in result
    assert "ml_cause" in result
    assert "ml_confidence" in result
    assert "agreement" in result
    assert "ml_probabilities" in result


def test_hybrid_otp_session():
    session = make_session(
        payment_method="UPI",
        duration=0.8,
    )

    result = diagnose_hybrid(
        session
    )

    assert result["cause"] == "otp_timeout"
    assert result["confidence"] >= 0.50


def test_hybrid_bank_timeout_session():
    session = make_session(
        payment_method="netbanking",
        duration=6.0,
    )

    result = diagnose_hybrid(
        session
    )

    assert result["cause"] == "bank_page_timeout"
    assert result["confidence"] >= 0.50


def test_hybrid_price_shock_session():
    session = make_session(
        payment_method="card",
        duration=2.5,
        cart_value=8000.0,
    )

    result = diagnose_hybrid(
        session
    )

    assert result["cause"] == "price_shock"
    assert result["confidence"] >= 0.50


def test_hybrid_network_session():
    session = make_session(
        payment_method="card",
        device="mobile",
        duration=0.5,
    )

    result = diagnose_hybrid(
        session
    )

    assert result["cause"] in {
        "network_drop",
        "otp_timeout",
    }


def test_hybrid_fraud_session():
    session = make_session(
        payment_method="card",
        device="desktop",
        duration=0.3,
        cart_value=20000.0,
    )

    result = diagnose_hybrid(
        session
    )

    assert result["cause"] == "fraud_suspected"
    assert result["confidence"] >= 0.50


def test_completed_session_is_rejected():
    session = make_session()

    session["status"] = "completed"

    with pytest.raises(ValueError):
        diagnose_hybrid(
            session
        )


def test_hybrid_confidence_is_bounded():
    session = make_session()

    result = diagnose_hybrid(
        session
    )

    assert 0.0 <= result["confidence"] <= 1.0


def test_hybrid_agreement_is_boolean():
    session = make_session()

    result = diagnose_hybrid(
        session
    )

    assert isinstance(
        result["agreement"],
        bool,
    )

