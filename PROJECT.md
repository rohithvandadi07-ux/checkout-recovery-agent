# Checkout Drop-off Recovery Agent — Project Specification

## 1. Project Objective

Build an agent that detects revenue at risk from abandoned checkout sessions, determines the likely cause of abandonment, decides whether an automated recovery intervention is appropriate, executes a bounded recovery workflow, and records every decision.

The project focuses specifically on **checkout drop-off recovery**.

The objective is not to maximize the number of automated actions.

The objective is to maximize **safe revenue recovery**.

---

# 2. Problem Definition

A customer starts checkout but does not complete payment.

Possible reasons include:

* OTP timeout
* Network interruption
* Bank-page timeout
* Price shock
* Distraction
* Insufficient funds
* Suspicious activity
* Unknown causes

The system must determine whether the abandoned checkout represents recoverable revenue and, if enough evidence exists, select an appropriate intervention.

The system must also recognize situations where it should **not act**.

---

# 3. Scope

### In Scope

* Checkout abandonment detection
* Synthetic checkout-session generation
* Abandonment-cause diagnosis
* Confidence estimation
* Recovery-policy decisions
* Bounded recovery actions
* Human escalation
* Recovery-outcome simulation
* Audit logging
* Revenue-recovery metrics
* Interactive dashboard
* ML-based diagnosis experimentation

### Out of Scope

* Real customer data
* Real payment processing
* Real financial transactions
* Autonomous fraud enforcement
* Unlimited automated customer messaging
* Real monetary discounts
* Unrestricted LLM-driven financial decisions

The initial implementation will simulate payment and recovery outcomes.

---

# 4. System Architecture

```text
                    ┌──────────────────────┐
                    │ Synthetic Data       │
                    │ Generator             │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Checkout Sessions    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Risk Detector        │
                    └──────────┬───────────┘
                               │
                         Abandoned?
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Cause Diagnoser      │
                    │                      │
                    │ Cause + Confidence   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Policy Engine        │
                    │                      │
                    │ Safety + Limits      │
                    └──────────┬───────────┘
                               │
                   ┌───────────┼───────────┐
                   │           │           │
                   ▼           ▼           ▼
                Recover     Review       Stop
                   │           │           │
                   └───────────┼───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Outcome Simulator    │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Audit Logger         │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Dashboard            │
                    └──────────────────────┘
```

---

# 5. Data Model

Each checkout session will contain observable features.

Example:

```json
{
  "session_id": "cs_000001",
  "cart_value": 2499.00,
  "payment_method": "UPI",
  "device": "mobile",
  "checkout_duration": 0.8,
  "status": "abandoned"
}
```

The dataset generator will maintain a hidden ground-truth cause:

```text
otp_timeout
```

The hidden cause must never be passed to the diagnosis engine.

It exists only for post-run evaluation.

---

# 6. Synthetic Data Generation

The data generator must create realistic relationships between observable features and hidden causes.

Randomly assigning causes independently of features is not acceptable because it creates a dataset with no meaningful signal.

Examples of intended correlations:

### OTP Timeout

```text
UPI
+
short checkout duration
```

### Bank Page Timeout

```text
Netbanking
+
longer checkout duration
```

### Price Shock

```text
Higher cart value
+
moderate checkout duration
```

### Network Drop

```text
Mobile device
+
very short session
```

### Distraction Exit

```text
Long checkout duration
```

The generator should also introduce controlled noise so that the diagnosis problem is not artificially perfect.

---

# 7. Detection Layer

The detector identifies sessions that require attention.

### Completed

```text
status = completed
        ↓
No action
```

### Abandoned

```text
status = abandoned
        ↓
Revenue at risk
```

The detector should calculate the monetary value represented by abandoned sessions.

---

# 8. Diagnosis Layer

The initial diagnosis engine will use explainable rules.

Each diagnosis returns:

```text
Cause
Confidence
Reasoning
```

Example:

```text
Cause:
otp_timeout

Confidence:
0.72

Reasoning:
UPI checkout was abandoned after a very short duration,
which is consistent with an OTP delivery or entry timeout.
```

Initial causes:

```text
otp_timeout
bank_page_timeout
price_shock
network_drop
distraction_exit
fraud_suspected
insufficient_funds
unknown
```

A diagnosis should default to `unknown` when no strong rule matches.

---

# 9. Confidence System

Every diagnosis receives a confidence score.

The policy engine uses the confidence score to determine whether automated action is permitted.

Conceptually:

```text
High confidence
      ↓
Potentially actionable

Low confidence
      ↓
Do not guess
      ↓
Manual review
```

Initial acting threshold:

```text
0.40
```

The threshold can later be calibrated experimentally.

---

# 10. Policy / Safety Engine

The policy engine is responsible for determining whether a proposed recovery action is allowed.

The AI/diagnosis layer does not directly execute financial actions.

The policy engine must enforce the following constraints.

## Rule 1 — One Automated Attempt

Maximum:

```text
1 automated recovery attempt / session
```

No retry loops.

---

## Rule 2 — Fraud Gate

```text
fraud_suspected
        ↓
Never automatically recover
        ↓
Human escalation
```

The system should not attempt autonomous fraud enforcement.

---

## Rule 3 — Insufficient Funds

```text
insufficient_funds
        ↓
No automated recovery action
```

The system records the case and can route it for review.

---

## Rule 4 — Confidence Gate

```text
confidence < 0.40
        ↓
Do not act
        ↓
Manual review
```

This represents a deliberate decision by the system to acknowledge uncertainty.

---

## Rule 5 — High-Value Discount Gate

For a price-shock diagnosis:

```text
cart value <= allowed threshold
        ↓
Discount nudge may be allowed
```

while:

```text
cart value > allowed threshold
        ↓
Human approval required
```

Initial threshold:

```text
₹10,000
```

This threshold is a configurable policy value and should not be hard-coded throughout the system.

---

# 11. Recovery Actions

Initial simulated actions:

### Retry Reminder

Used for cases such as probable OTP timeout or network interruption.

```text
retry_reminder
```

### Reminder Email

```text
reminder_email
```

### Alternative Payment Method

```text
alt_method_offer
```

### Discount Nudge

```text
discount_nudge
```

### Manual Review

```text
manual_review
```

### Human Escalation

```text
escalate_to_human
```

The action layer will initially simulate outcomes rather than calling real payment or notification services.

---

# 12. Outcome Simulation

Every automated action should produce a simulated outcome.

Possible outcomes:

```text
recovered
not_recovered
blocked
manual_review
escalated
```

Recovery probabilities should be configurable and should not be artificially selected to guarantee impressive results.

---

# 13. Audit Logging

Every processed abandoned session must produce an audit record.

Minimum fields:

```text
session_id
cart_value
payment_method
device
checkout_duration
diagnosed_cause
confidence
reasoning
action
gate_decision
gate_reason
outcome
true_hidden_cause
```

The hidden cause may be stored for evaluation but must never be used by the decision engine.

---

# 14. Evaluation

The project will evaluate both intelligence and business impact.

## Business Metrics

```text
Total Value at Risk
Total Value Recovered
Value Recovery Rate
Session Recovery Rate
```

### Value Recovery Rate

```text
Recovered Value
──────────────── × 100
At-Risk Value
```

### Session Recovery Rate

```text
Recovered Sessions
────────────────── × 100
Abandoned Sessions
```

---

# 15. Diagnosis Metrics

We will calculate:

* Overall diagnosis accuracy
* Accuracy by abandonment cause
* Confusion matrix
* Precision
* Recall
* F1 score
* Confidence distribution
* Unknown / low-confidence percentage

We will separately analyze causes that have weak observable signals.

---

# 16. Safety Metrics

We will also measure:

* Fraud cases automatically blocked
* Low-confidence actions prevented
* High-value discount actions blocked
* Manual-review count
* Human-escalation count
* Automated actions per session
* Policy violations

The system should have:

```text
Automated actions per session <= 1
```

---

# 17. Dashboard

The dashboard will contain three primary sections.

## 17.1 Revenue Ledger

Display:

* Revenue at risk
* Revenue recovered
* Recovery rate
* Diagnosis accuracy
* Escalation count

## 17.2 Recovery Funnel

```text
Abandoned Sessions
        ↓
Diagnosed
        ↓
Action Eligible
        ↓
Action Attempted
        ↓
Recovered
```

## 17.3 Audit Table

Display individual sessions with:

* Session ID
* Cart value
* Cause
* Confidence
* Reasoning
* Action
* Gate
* Outcome

Filters should include:

```text
Recovered
Escalated
Manual Review
Misdiagnosed
Blocked
```

---

# 18. ML Extension

The first implementation will establish an explainable rule-based baseline.

After the baseline works, we will evaluate ML models for diagnosis.

Potential approach:

```text
Observable Checkout Features
            ↓
       ML Classifier
            ↓
      Cause Probability
            ↓
       Policy Engine
            ↓
         Action
```

Possible models include:

* Random Forest
* Gradient Boosting
* LightGBM / XGBoost if justified

The ML model will provide recommendations.

The policy engine will continue to control whether actions are permitted.

---

# 19. LLM / Agent Extension

An LLM should only be introduced where it provides measurable value.

Potential use case:

```text
Ambiguous / Unknown Case
          ↓
LLM Reasoning
          ↓
Structured Recommendation
          ↓
Policy Validation
          ↓
Action or Human Review
```

The LLM must not bypass:

* Fraud gates
* Confidence gates
* Value limits
* Maximum-action limits
* Human approval requirements

The LLM is therefore a reasoning component, not the final authority over financial actions.

---

# 20. Testing Strategy

The system will include unit tests for:

### Detector

* Completed session
* Abandoned session

### Diagnoser

* Strong OTP signal
* Strong bank-timeout signal
* Price shock
* Unknown case
* Ambiguous case

### Policy Engine

* Fraud blocking
* Low-confidence blocking
* High-value discount blocking
* Insufficient-funds blocking
* One-action limit

### Agent

* End-to-end recovery
* Failed recovery
* Successful recovery
* Manual escalation
* Audit generation

---

# 21. Development Phases

## Phase 1 — Repository & Foundation

* Project structure
* Documentation
* Dependencies
* Git workflow

## Phase 2 — Synthetic Data

* Session generator
* Cause distributions
* Noise injection
* Dataset validation

## Phase 3 — Detection

* Abandonment detection
* Revenue-at-risk calculation

## Phase 4 — Diagnosis

* Explainable rules
* Confidence scores
* Reasoning generation
* Baseline evaluation

## Phase 5 — Policy Engine

* Safety gates
* Action limits
* Human escalation

## Phase 6 — Recovery Simulation

* Recovery actions
* Outcome generation
* Revenue recovery calculation

## Phase 7 — Audit System

* Per-session logs
* Summary metrics

## Phase 8 — Dashboard

* Ledger
* Funnel
* Audit table
* Filters

## Phase 9 — ML Enhancement

* Feature engineering
* Baseline ML model
* Model evaluation
* Confidence calibration

## Phase 10 — Final Engineering

* Testing
* Documentation
* Error handling
* Reproducibility
* Demo
* Deployment preparation

---

# 22. Success Criteria

The project will be considered successful when:

1. Abandoned sessions are reliably detected.
2. Diagnosis can be evaluated against hidden ground truth.
3. Every diagnosis includes an explanation.
4. Unsafe actions are blocked by deterministic policy rules.
5. No session receives more than one automated attempt.
6. Recovery outcomes are measurable.
7. Revenue recovered can be calculated.
8. Every decision is auditable.
9. Failure cases are visible rather than hidden.
10. The dashboard allows a reviewer to understand the system quickly.
11. ML improvements can be compared against the explainable baseline.

---

# 23. Current Status

```text
Repository        ✓
Git initialization ✓
Project structure ✓
Documentation     → Initial version
Data generator    → Not started
Detection         → Not started
Diagnosis         → Not started
Policy engine     → Not started
Recovery          → Not started
Audit             → Not started
Dashboard         → Not started
ML extension      → Not started
```

## Next Milestone

Implement:

```text
src/generate_data.py
```

The first generator will create a reproducible synthetic checkout dataset with correlated abandonment signatures and hidden ground-truth causes.
