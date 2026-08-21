"""
Machine-learning checkout abandonment diagnosis.

This module trains and uses a Random Forest classifier to predict
the likely cause of an abandoned checkout.

Important design rule:
- `true_cause` is used ONLY as the training target.
- `true_cause` is NEVER used as an input feature.
- The ML model predicts a cause.
- The existing policy engine remains responsible for deciding
  whether a recovery action is safe.

This module is intentionally independent from the existing
rule-based diagnoser until the ML model is validated.
"""

from __future__ import annotations

import json
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any
from functools import lru_cache

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DATA_PATH = (
    PROJECT_ROOT / "data" / "sessions.json"
)

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT / "models" / "checkout_diagnosis.joblib"
)


TARGET_COLUMN = "true_cause"


FEATURE_COLUMNS = [
    "cart_value",
    "payment_method",
    "device",
    "checkout_duration_minutes",
]


NUMERIC_FEATURES = [
    "cart_value",
    "checkout_duration_minutes",
]


CATEGORICAL_FEATURES = [
    "payment_method",
    "device",
]


def load_training_data(
    data_path: Path = DEFAULT_DATA_PATH,
) -> pd.DataFrame:
    """
    Load abandoned checkout sessions for ML training.

    Only abandoned sessions with a known true_cause are used.
    """

    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found: {data_path}"
        )

    with data_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        sessions = json.load(file)

    if not isinstance(sessions, list):
        raise ValueError(
            "Training data must contain a JSON list."
        )

    dataframe = pd.DataFrame(sessions)

    required_columns = (
        FEATURE_COLUMNS
        + [
            "status",
            TARGET_COLUMN,
        ]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Training data is missing required columns: "
            + ", ".join(missing_columns)
        )

    # Only abandoned sessions are relevant for diagnosis.
    dataframe = dataframe[
        dataframe["status"] == "abandoned"
    ].copy()

    # Remove incomplete training rows.
    dataframe = dataframe.dropna(
        subset=FEATURE_COLUMNS + [TARGET_COLUMN]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid abandoned sessions are available "
            "for ML training."
        )

    return dataframe


def build_pipeline() -> Pipeline:
    """
    Build the preprocessing + Random Forest pipeline.

    Categorical values are one-hot encoded.
    Numeric values are passed directly to the classifier.
    """

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


def train_model(
    data_path: Path = DEFAULT_DATA_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """
    Train, evaluate, and persist the ML diagnosis model.

    Returns evaluation metrics.
    """

    dataframe = load_training_data(
        data_path
    )

    X = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    pipeline = build_pipeline()

    pipeline.fit(
        X_train,
        y_train,
    )

    predictions = pipeline.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        y_test,
        predictions,
        zero_division=0,
    )

    model_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        pipeline,
        model_path,
    )

    # If an older version of this model was cached,
    # force future predictions to use the newly trained model.
    load_model.cache_clear()

    return {
        "model_path": str(model_path),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(
            accuracy,
            4,
        ),
        "macro_precision": round(
            precision,
            4,
        ),
        "macro_recall": round(
            recall,
            4,
        ),
        "macro_f1": round(
            f1,
            4,
        ),
        "classification_report": report,
    }


@lru_cache(maxsize=4)
def load_model(
    model_path: Path = DEFAULT_MODEL_PATH,
) -> Pipeline:
    """
    Load a previously trained diagnosis model.

    Models are cached in memory so repeated predictions do not
    repeatedly deserialize the same joblib file.

    This is important when processing thousands of checkout
    sessions in one run.
    """

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"ML model not found: {model_path}. "
            "Train the model first."
        )

    # NumPy 2.5 + older joblib versions can emit a known
    # deprecation warning while restoring serialized arrays.
    # The warning is limited strictly to this deserialization step.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                "Setting the shape on a NumPy array has "
                "been deprecated"
            ),
            category=DeprecationWarning,
            module=r"joblib\.numpy_pickle",
        )

        model = joblib.load(
            model_path
        )

    return model


def predict_session(
    session: dict[str, Any],
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """
    Predict the likely abandonment cause for one session.

    Returns:
        cause
        confidence
        model
        probabilities
    """

    if session.get("status") != "abandoned":
        raise ValueError(
            "ML diagnosis is only applicable "
            "to abandoned sessions."
        )

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in session
    ]

    if missing_features:
        raise ValueError(
            "Session is missing required features: "
            + ", ".join(missing_features)
        )

    model = load_model(
        Path(model_path)
    )

    dataframe = pd.DataFrame(
        [
            {
                feature: session[feature]
                for feature in FEATURE_COLUMNS
            }
        ]
    )

    prediction = model.predict(
        dataframe
    )[0]

    probabilities = model.predict_proba(
        dataframe
    )[0]

    classes = model.classes_

    probability_map = {
        str(label): round(
            float(probability),
            4,
        )
        for label, probability
        in zip(
            classes,
            probabilities,
        )
    }

    confidence = max(
        probability_map.values()
    )

    return {
        "cause": str(prediction),
        "confidence": round(
            confidence,
            4,
        ),
        "model": "random_forest",
        "probabilities": probability_map,
    }


def main() -> None:
    """Train the checkout diagnosis model."""

    print("\n" + "=" * 60)
    print("ML CHECKOUT DIAGNOSIS")
    print("=" * 60)

    metrics = train_model()

    print(
        f"Training samples : "
        f"{metrics['training_samples']}"
    )

    print(
        f"Test samples     : "
        f"{metrics['test_samples']}"
    )

    print(
        f"Accuracy         : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Macro Precision  : "
        f"{metrics['macro_precision']:.4f}"
    )

    print(
        f"Macro Recall     : "
        f"{metrics['macro_recall']:.4f}"
    )

    print(
        f"Macro F1         : "
        f"{metrics['macro_f1']:.4f}"
    )

    print(
        f"Model saved to   : "
        f"{metrics['model_path']}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()