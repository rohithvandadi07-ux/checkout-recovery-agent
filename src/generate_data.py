from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
NUM_SESSIONS = 5000
LABEL_NOISE_RATE = 0.12

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "sessions.json"

PAYMENT_METHODS = [
    "UPI",
    "card",
    "netbanking",
    "wallet",
]

DEVICES = [
    "mobile",
    "desktop",
    "tablet",
]

CAUSES = [
    "otp_timeout",
    "price_shock",
    "network_drop",
    "bank_page_timeout",
    "insufficient_funds",
    "distraction_exit",
    "fraud_suspected",
    "unknown",
]


def clipped_normal(
    rng: np.random.Generator,
    mean: float,
    std: float,
    minimum: float,
    maximum: float,
) -> float:
    value = rng.normal(mean, std)
    return float(np.clip(value, minimum, maximum))


def generate_hidden_cause(rng: np.random.Generator) -> str:
    probabilities = [
        0.20,  # otp_timeout
        0.14,  # price_shock
        0.12,  # network_drop
        0.10,  # bank_page_timeout
        0.10,  # insufficient_funds
        0.14,  # distraction_exit
        0.05,  # fraud_suspected
        0.15,  # unknown
    ]

    return str(rng.choice(CAUSES, p=probabilities))


def generate_cart_value(
    rng: np.random.Generator,
    cause: str,
) -> float:
    if cause == "fraud_suspected":
        value = rng.lognormal(np.log(12000), 0.55)
    elif cause == "price_shock":
        value = rng.lognormal(np.log(6500), 0.50)
    else:
        value = rng.lognormal(np.log(2500), 0.65)

    return round(float(np.clip(value, 200, 50000)), 2)


def generate_payment_method(
    rng: np.random.Generator,
    cause: str,
) -> str:
    if cause == "otp_timeout":
        probabilities = [0.75, 0.10, 0.10, 0.05]
    elif cause == "bank_page_timeout":
        probabilities = [0.05, 0.10, 0.80, 0.05]
    else:
        probabilities = [0.40, 0.35, 0.20, 0.05]

    return str(rng.choice(PAYMENT_METHODS, p=probabilities))


def generate_device(
    rng: np.random.Generator,
    cause: str,
) -> str:
    if cause == "network_drop":
        probabilities = [0.75, 0.20, 0.05]
    elif cause == "distraction_exit":
        probabilities = [0.55, 0.35, 0.10]
    else:
        probabilities = [0.55, 0.40, 0.05]

    return str(rng.choice(DEVICES, p=probabilities))


def generate_duration(
    rng: np.random.Generator,
    cause: str,
) -> float:
    distributions = {
        "otp_timeout": (0.8, 0.35, 0.15, 1.5),
        "price_shock": (2.5, 0.75, 1.2, 4.0),
        "network_drop": (0.5, 0.20, 0.10, 0.8),
        "bank_page_timeout": (6.0, 1.50, 3.5, 9.5),
        "insufficient_funds": (3.0, 1.50, 0.5, 8.0),
        "distraction_exit": (14.0, 3.50, 10.0, 25.0),
        "fraud_suspected": (0.35, 0.10, 0.10, 0.5),
        "unknown": (5.0, 3.0, 0.2, 15.0),
    }

    mean, std, minimum, maximum = distributions[cause]

    return round(
        clipped_normal(
            rng,
            mean,
            std,
            minimum,
            maximum,
        ),
        2,
    )


def generate_session(
    rng: np.random.Generator,
    session_number: int,
) -> dict:
    session_id = f"cs_{session_number:06d}"

    completed = bool(rng.random() < 0.50)

    if completed:
        cart_value = generate_cart_value(rng, "unknown")

        payment_method = str(
            rng.choice(
                PAYMENT_METHODS,
                p=[0.45, 0.30, 0.20, 0.05],
            )
        )

        device = str(
            rng.choice(
                DEVICES,
                p=[0.55, 0.40, 0.05],
            )
        )

        duration = round(
            clipped_normal(
                rng,
                4.0,
                3.0,
                0.1,
                20.0,
            ),
            2,
        )

        true_cause = None

    else:
        true_cause = generate_hidden_cause(rng)

        cart_value = generate_cart_value(
            rng,
            true_cause,
        )

        payment_method = generate_payment_method(
            rng,
            true_cause,
        )

        device = generate_device(
            rng,
            true_cause,
        )

        duration = generate_duration(
            rng,
            true_cause,
        )

    return {
        "session_id": session_id,
        "cart_value": cart_value,
        "payment_method": payment_method,
        "device": device,
        "checkout_duration_minutes": duration,
        "status": "completed" if completed else "abandoned",
        "true_cause": true_cause,
    }


def inject_label_noise(
    sessions: list[dict],
    rng: np.random.Generator,
) -> None:
    abandoned = [
        session
        for session in sessions
        if session["status"] == "abandoned"
    ]

    number_to_modify = int(
        len(abandoned) * LABEL_NOISE_RATE
    )

    if number_to_modify == 0:
        return

    selected = rng.choice(
        len(abandoned),
        size=number_to_modify,
        replace=False,
    )

    for index in selected:
        session = abandoned[index]

        modification = rng.choice(
            ["duration", "device", "payment"]
        )

        if modification == "duration":
            session["checkout_duration_minutes"] = round(
                float(
                    np.clip(
                        session["checkout_duration_minutes"]
                        * rng.uniform(0.7, 1.5),
                        0.1,
                        25.0,
                    )
                ),
                2,
            )

        elif modification == "device":
            session["device"] = str(
                rng.choice(DEVICES)
            )

        else:
            session["payment_method"] = str(
                rng.choice(PAYMENT_METHODS)
            )


def generate_dataset(
    num_sessions: int = NUM_SESSIONS,
    seed: int = SEED,
) -> list[dict]:
    rng = np.random.default_rng(seed)

    sessions = [
        generate_session(
            rng,
            i + 1,
        )
        for i in range(num_sessions)
    ]

    inject_label_noise(
        sessions,
        rng,
    )

    return sessions


def save_dataset(
    sessions: list[dict],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            sessions,
            file,
            indent=2,
        )


def print_summary(
    sessions: list[dict],
) -> None:
    dataframe = pd.DataFrame(sessions)

    total = len(dataframe)

    completed = int(
        (dataframe["status"] == "completed").sum()
    )

    abandoned = int(
        (dataframe["status"] == "abandoned").sum()
    )

    abandoned_value = dataframe.loc[
        dataframe["status"] == "abandoned",
        "cart_value",
    ].sum()

    print("\n" + "=" * 60)
    print("CHECKOUT DATASET GENERATED")
    print("=" * 60)

    print(f"Total sessions       : {total}")
    print(f"Completed sessions   : {completed}")
    print(f"Abandoned sessions   : {abandoned}")
    print(
        f"Value at risk        : ₹{abandoned_value:,.2f}"
    )

    print("\nAbandonment causes:")

    cause_counts = (
        dataframe.loc[
            dataframe["status"] == "abandoned",
            "true_cause",
        ]
        .value_counts()
    )

    for cause, count in cause_counts.items():
        print(f"  {cause:<22} {count}")

    print("\nPayment methods:")

    for method, count in dataframe["payment_method"].value_counts().items():
        print(f"  {method:<22} {count}")

    print("\nDevices:")

    for device, count in dataframe["device"].value_counts().items():
        print(f"  {device:<22} {count}")

    print("=" * 60)
    print(f"Saved to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    sessions = generate_dataset()

    save_dataset(sessions)

    print_summary(sessions)
