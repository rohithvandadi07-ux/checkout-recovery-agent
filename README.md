# Checkout Drop-off Recovery Agent

An AI-powered revenue recovery agent designed to identify abandoned checkout sessions, diagnose the likely reason for drop-off, determine whether a recovery action is safe, execute a bounded intervention, and maintain a complete audit trail.

> **Built for the Razorpay AI Buildathon — Track 03: AI Revenue Recovery**

---

## Overview

Checkout abandonment represents revenue at risk.

A customer may begin a payment and leave before completing it because of reasons such as:

* OTP timeout
* Bank-page timeout
* Network failure
* Price shock
* Distraction
* Insufficient funds
* Suspicious checkout behaviour
* Unknown or ambiguous causes

Instead of treating every abandoned checkout the same way, this project builds an agent that follows:

```text
Checkout Session
       ↓
Risk Detection
       ↓
Cause Diagnosis
       ↓
Safety / Policy Check
       ↓
Recovery Action or Human Review
       ↓
Outcome
       ↓
Audit Log
       ↓
Dashboard
```

The project deliberately focuses on **one narrow problem — checkout drop-off recovery — rather than attempting to solve every possible payment degradation scenario.**

---

## Problem Statement

When a customer abandons checkout, the merchant potentially loses the entire transaction value.

A recovery system should therefore answer four questions:

1. **Is this checkout actually at risk?**
2. **Why did the customer abandon it?**
3. **Is an automated intervention appropriate and safe?**
4. **Did the intervention recover the revenue?**

The system is designed to answer these questions while maintaining strict limits on autonomous actions.

---

## Core Idea

The system separates **prediction** from **action**.

The intelligence layer determines:

```text
Likely Cause + Confidence
```

The policy layer then determines:

```text
Should the system act?
```

This means the AI is not given unrestricted control over customer or financial actions.

For example:

```text
Low confidence
      ↓
Do not guess
      ↓
Manual review
```

and:

```text
Fraud suspected
      ↓
Never auto-action
      ↓
Human escalation
```

---

## Key Design Principles

### 1. Explainability

Every diagnosis should have a reason that a human can understand.

### 2. Bounded Automation

A session can receive at most one automated recovery attempt.

### 3. Safety Gates

Certain conditions override the AI's recommendation.

Examples:

* Fraud → human review
* Low confidence → manual review
* High-value discount → human approval
* Insufficient funds → no automatic recovery action

### 4. Failure Awareness

The system should be able to say:

> "I don't have enough evidence to determine the cause."

Not every checkout problem can be reliably inferred from behavioural telemetry.

### 5. Auditability

Every session should produce an auditable decision record containing the diagnosis, confidence, reasoning, action, gate decision, and outcome.

### 6. Business Impact

The primary business metric is not only classification accuracy.

We also measure:

```text
Revenue at Risk
       ↓
Revenue Recovered
       ↓
Recovery Rate
```

---

## System Architecture

```text
                  Synthetic Checkout Data
                           │
                           ▼
                  ┌──────────────────┐
                  │  Risk Detector   │
                  └────────┬─────────┘
                           │
                    Abandoned?
                           │
                           ▼
                  ┌──────────────────┐
                  │    Diagnoser     │
                  │                  │
                  │ Cause + Confidence│
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  Policy Engine   │
                  │                  │
                  │ Safety + Limits  │
                  └────────┬─────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          Recovery Action       Human Review
                 │                   │
                 └─────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │ Outcome Simulator│
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │   Audit Logger   │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │    Dashboard     │
                  └──────────────────┘
```

---

## Project Structure

```text
checkout-recovery-agent/
│
├── data/
│   ├── sessions.json
│   ├── audit_log.json
│   └── summary.json
│
├── dashboard/
│   └── dashboard.html
│
├── models/
│
├── src/
│   ├── generate_data.py
│   ├── detector.py
│   ├── diagnoser.py
│   ├── policy_engine.py
│   ├── recovery_agent.py
│   ├── simulator.py
│   └── audit_logger.py
│
├── tests/
│   ├── test_detector.py
│   ├── test_diagnoser.py
│   ├── test_policy_engine.py
│   └── test_agent.py
│
├── PROJECT.md
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Abandonment Causes

The initial system models the following causes:

| Cause                | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| `otp_timeout`        | OTP delivery or entry takes too long                        |
| `price_shock`        | Customer abandons after seeing the effective price          |
| `network_drop`       | Network/connectivity interruption                           |
| `bank_page_timeout`  | Banking page takes too long to complete                     |
| `insufficient_funds` | Customer cannot complete the payment financially            |
| `distraction_exit`   | Customer leaves after spending significant time in checkout |
| `fraud_suspected`    | Checkout behaviour triggers a fraud concern                 |
| `unknown`            | Insufficient evidence for a reliable diagnosis              |

---

## Safety Policy

The recovery agent follows hard constraints.

```text
Maximum automated attempts per session = 1
```

### Fraud

```text
fraud_suspected
        ↓
Human escalation
```

### Insufficient Funds

```text
insufficient_funds
        ↓
No automated recovery action
```

### Low Confidence

```text
confidence < threshold
        ↓
Manual review
```

### High-Value Discount

```text
price_shock
+
cart value above allowed limit
        ↓
Human approval
```

The policy layer therefore acts as a safety boundary between AI recommendations and financial actions.

---

## Data Generation

The initial dataset will be synthetic.

Each generated checkout session will contain observable information such as:

* Session ID
* Cart value
* Payment method
* Device
* Checkout duration
* Session status

The generator will also maintain a hidden ground-truth abandonment cause.

The recovery system will **not receive the hidden cause** during diagnosis.

This allows diagnosis accuracy to be evaluated honestly after the recovery process.

The synthetic data will contain correlations between checkout behaviour and abandonment causes rather than assigning causes completely at random.

---

## Evaluation Metrics

The system will measure:

### Operational Metrics

* Total checkout sessions
* Completed sessions
* Abandoned sessions
* Total value at risk
* Total value recovered

### Recovery Metrics

* Recovery rate by transaction value
* Recovery rate by session count
* Recovery action success rate
* Revenue recovered per action

### Intelligence Metrics

* Overall diagnosis accuracy
* Diagnosis accuracy by cause
* Confidence distribution
* Unknown / low-confidence rate

### Safety Metrics

* Number of human escalations
* Number of blocked actions
* Fraud cases prevented from automatic action
* High-value actions blocked
* Maximum-action violations

---

## Technology

Initial implementation:

* Python
* NumPy
* Pandas
* Scikit-learn
* Pytest
* HTML/CSS/JavaScript for the dashboard

The first implementation will prioritize deterministic, explainable logic.

Machine-learning-based diagnosis can then be introduced and evaluated against the baseline.

---

## Development Strategy

### Phase 1 — Data

Build a realistic synthetic checkout-session generator.

### Phase 2 — Detection

Identify abandoned sessions and calculate revenue at risk.

### Phase 3 — Diagnosis

Build explainable cause prediction with confidence scores.

### Phase 4 — Policy

Implement safety gates, action limits, and human escalation.

### Phase 5 — Recovery

Simulate bounded recovery interventions and their outcomes.

### Phase 6 — Audit

Record every decision and outcome.

### Phase 7 — Dashboard

Build a visual recovery console showing business metrics and individual decisions.

### Phase 8 — Intelligence Upgrade

Evaluate ML-based diagnosis and introduce AI/LLM capabilities only where they provide measurable value.

### Phase 9 — Testing & Hardening

Test edge cases, safety boundaries, failure recovery, and reproducibility.

---

## Current Status

**Project initialized.**

Implementation has not started yet.

The next milestone is the synthetic checkout-session generator.

---

## Project Philosophy

The goal is not to build an agent that acts on everything.

The goal is to build an agent that understands:

```text
When to act
When not to act
Why it acted
Why it did not act
What happened afterward
```

That distinction is central to building reliable AI systems for financial workflows.
