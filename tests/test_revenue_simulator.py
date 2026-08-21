from src.revenue_simulator import (
    RECOVERY_PROBABILITIES,
    deterministic_score,
    simulate_recovery,
    simulate_results,
    summarize_revenue,
)


def make_session(
    session_id="cs_revenue_001",
    cart_value=2500.0,
    status="abandoned",
):
    return {
        "session_id": session_id,
        "cart_value": cart_value,
        "status": status,
    }


def make_result(
    cause="otp_timeout",
    decision="recover",
):
    return {
        "diagnosis": {
            "cause": cause,
            "confidence": 0.80,
        },
        "policy": {
            "decision": decision,
            "action": (
                "send_payment_retry_prompt"
                if decision == "recover"
                else None
            ),
            "reason": "test",
        },
    }


def test_deterministic_score_is_reproducible():
    score1 = deterministic_score("cs_001")
    score2 = deterministic_score("cs_001")

    assert score1 == score2
    assert 0.0 <= score1 < 1.0


def test_different_sessions_can_have_different_scores():
    score1 = deterministic_score("cs_001")
    score2 = deterministic_score("cs_002")

    assert score1 != score2


def test_recoverable_session_is_eligible():
    session = make_session()

    result = simulate_recovery(
        session,
        make_result("otp_timeout"),
    )

    assert result["status"] == "abandoned"
    assert result["eligible"] is True
    assert result["cause"] == "otp_timeout"
    assert result["recovery_probability"] == 0.65


def test_no_action_session_is_not_eligible():
    session = make_session()

    result = simulate_recovery(
        session,
        make_result(
            "unknown",
            decision="no_action",
        ),
    )

    assert result["eligible"] is False
    assert result["recovered"] is False
    assert result["recovered_revenue"] == 0.0


def test_escalated_session_is_not_eligible():
    session = make_session(
        cart_value=20000.0,
    )

    result = simulate_recovery(
        session,
        make_result(
            "fraud_suspected",
            decision="escalate",
        ),
    )

    assert result["eligible"] is False
    assert result["recovered"] is False
    assert result["recovered_revenue"] == 0.0


def test_completed_session_is_not_eligible():
    session = make_session(
        session_id="cs_completed",
        cart_value=5000.0,
        status="completed",
    )

    result = simulate_recovery(
        session,
        make_result("otp_timeout"),
    )

    assert result["status"] == "completed"
    assert result["eligible"] is False
    assert result["recovered"] is False
    assert result["recovered_revenue"] == 0.0


def test_recovery_success_is_deterministic():
    session = make_session(
        session_id="cs_success_test",
        cart_value=5000.0,
    )

    first = simulate_recovery(
        session,
        make_result("otp_timeout"),
    )

    second = simulate_recovery(
        session,
        make_result("otp_timeout"),
    )

    assert first["recovered"] == second["recovered"]
    assert (
        first["recovered_revenue"]
        == second["recovered_revenue"]
    )


def test_successful_recovery_returns_cart_value():
    session = make_session(
        session_id="cs_forced_success",
        cart_value=5000.0,
    )

    result = simulate_recovery(
        session,
        make_result("otp_timeout"),
    )

    if result["recovered"]:
        assert result["recovered_revenue"] == 5000.0
    else:
        assert result["recovered_revenue"] == 0.0


def test_all_defined_probabilities_are_valid():
    for probability in RECOVERY_PROBABILITIES.values():
        assert 0.0 < probability <= 1.0


def test_simulate_multiple_results():
    sessions = [
        make_session(
            session_id="cs_001",
            cart_value=1000.0,
        ),
        make_session(
            session_id="cs_002",
            cart_value=2000.0,
        ),
    ]

    results = [
        make_result("otp_timeout"),
        make_result(
            "unknown",
            decision="no_action",
        ),
    ]

    simulations = simulate_results(
        sessions,
        results,
    )

    assert len(simulations) == 2
    assert simulations[0]["eligible"] is True
    assert simulations[1]["eligible"] is False


def test_simulate_results_requires_matching_lengths():
    sessions = [
        make_session("cs_001"),
    ]

    results = []

    try:
        simulate_results(
            sessions,
            results,
        )
        assert False
    except ValueError:
        assert True


def test_revenue_summary():
    simulations = [
        {
            "session_id": "cs_001",
            "status": "abandoned",
            "cause": "otp_timeout",
            "cart_value": 1000.0,
            "eligible": True,
            "recovered": True,
            "recovered_revenue": 1000.0,
        },
        {
            "session_id": "cs_002",
            "status": "abandoned",
            "cause": "network_drop",
            "cart_value": 2000.0,
            "eligible": True,
            "recovered": False,
            "recovered_revenue": 0.0,
        },
        {
            "session_id": "cs_003",
            "status": "abandoned",
            "cause": "unknown",
            "cart_value": 3000.0,
            "eligible": False,
            "recovered": False,
            "recovered_revenue": 0.0,
        },
    ]

    summary = summarize_revenue(
        simulations,
    )

    assert summary["total_sessions"] == 3
    assert summary["value_at_risk"] == 6000.0
    assert summary["eligible_sessions"] == 2
    assert summary["eligible_value"] == 3000.0
    assert summary["successful_recoveries"] == 1
    assert summary["recovered_revenue"] == 1000.0
    assert summary["recovery_rate"] == 0.5
    assert (
        summary["revenue_recovery_rate"]
        == 1000.0 / 3000.0
    )


def test_value_at_risk_only_includes_abandoned_sessions():
    simulations = [
        {
            "session_id": "cs_abandoned",
            "status": "abandoned",
            "cause": "otp_timeout",
            "cart_value": 1000.0,
            "eligible": True,
            "recovered": True,
            "recovered_revenue": 1000.0,
        },
        {
            "session_id": "cs_completed",
            "status": "completed",
            "cause": None,
            "cart_value": 5000.0,
            "eligible": False,
            "recovered": False,
            "recovered_revenue": 0.0,
        },
    ]

    summary = summarize_revenue(
        simulations,
    )

    assert summary["value_at_risk"] == 1000.0