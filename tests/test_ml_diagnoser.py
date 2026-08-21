from pathlib import Path

import pytest

from src.ml_diagnoser import (
    DEFAULT_MODEL_PATH,
    FEATURE_COLUMNS,
    load_model,
    load_training_data,
    predict_session,
    train_model,
)


def make_session(
    status="abandoned",
    cart_value=2500.0,
    payment_method="UPI",
    device="mobile",
    duration=0.8,
):
    return {
        "session_id": "cs_ml_test",
        "cart_value": cart_value,
        "payment_method": payment_method,
        "device": device,
        "checkout_duration_minutes": duration,
        "status": status,
        "true_cause": "otp_timeout",
    }


def test_training_data_contains_required_features():
    dataframe = load_training_data()

    for feature in FEATURE_COLUMNS:
        assert feature in dataframe.columns

    assert "true_cause" in dataframe.columns
    assert len(dataframe) > 0


def test_training_data_contains_only_abandoned_sessions():
    dataframe = load_training_data()

    assert (
        dataframe["status"]
        .eq("abandoned")
        .all()
    )


def test_model_can_be_trained(tmp_path):
    model_path = (
        tmp_path / "checkout_model.joblib"
    )

    metrics = train_model(
        model_path=model_path
    )

    assert model_path.exists()
    assert metrics["training_samples"] > 0
    assert metrics["test_samples"] > 0

    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_precision"] <= 1.0
    assert 0.0 <= metrics["macro_recall"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0


def test_model_can_be_loaded(tmp_path):
    model_path = (
        tmp_path / "checkout_model.joblib"
    )

    train_model(
        model_path=model_path
    )

    model = load_model(
        model_path
    )

    assert model is not None


def test_model_can_predict_session(tmp_path):
    model_path = (
        tmp_path / "checkout_model.joblib"
    )

    train_model(
        model_path=model_path
    )

    session = make_session()

    result = predict_session(
        session,
        model_path=model_path,
    )

    assert "cause" in result
    assert "confidence" in result
    assert "model" in result
    assert "probabilities" in result

    assert result["model"] == "random_forest"

    assert 0.0 <= result["confidence"] <= 1.0


def test_model_probabilities_sum_to_one(tmp_path):
    model_path = (
        tmp_path / "checkout_model.joblib"
    )

    train_model(
        model_path=model_path
    )

    result = predict_session(
        make_session(),
        model_path=model_path,
    )

    total_probability = sum(
        result["probabilities"].values()
    )

    assert total_probability == pytest.approx(
        1.0,
        abs=0.01,
    )


def test_completed_session_is_rejected(tmp_path):
    model_path = (
        tmp_path / "checkout_model.joblib"
    )

    train_model(
        model_path=model_path
    )

    session = make_session(
        status="completed"
    )

    with pytest.raises(ValueError):
        predict_session(
            session,
            model_path=model_path,
        )


def test_missing_model_is_rejected():
    session = make_session()

    missing_model = Path(
        "models/does_not_exist.joblib"
    )

    with pytest.raises(FileNotFoundError):
        predict_session(
            session,
            model_path=missing_model,
        )

