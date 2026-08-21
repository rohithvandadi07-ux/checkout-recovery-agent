# Checkout Recovery Intelligence

> AI-powered checkout abandonment diagnosis, safety-aware recovery decisions, and revenue impact simulation.

**DETECT → DIAGNOSE → DECIDE → RECOVER → MEASURE**

Checkout Recovery Intelligence is an agentic revenue-recovery prototype designed to identify abandoned checkout sessions, determine the most likely abandonment cause, apply bounded recovery policies, simulate recovery actions, and measure the resulting revenue impact.

The system combines an explainable rule-based diagnosis engine with a machine-learning model and a conservative policy layer that prevents unsafe automated interventions.

> **Important:** This project currently operates in a synthetic/simulation environment. Recovery actions are simulated and do not trigger real payments, incentives, or customer communications.

---

## 🚀 The Problem

Checkout abandonment represents potentially recoverable revenue.

A simple system can detect that a customer abandoned checkout, but detection alone does not answer the important questions:

- Why did the customer abandon?
- Should the system attempt recovery?
- What recovery action is appropriate?
- When should the system do nothing?
- When should a case be escalated to a human?
- How much revenue could actually be recovered?
- Can automated recovery be prevented in suspicious cases?

Checkout Recovery Intelligence addresses these questions as one end-to-end decision system.

---

## 💡 The Solution

The system processes checkout sessions through five stages:

```text
DETECT
   ↓
DIAGNOSE
   ↓
DECIDE
   ↓
RECOVER
   ↓
MEASURE
```

### 1. Detect

Identify abandoned checkout sessions and calculate the value currently at risk.

Completed sessions are never treated as recovery opportunities.

### 2. Diagnose

Determine the most likely reason for abandonment.

The system uses two independent diagnosis mechanisms:

- Explainable rule-based diagnosis
- Random Forest machine-learning diagnosis

These are combined through a hybrid diagnosis layer.

### 3. Decide

The policy engine determines whether automated recovery is permitted.

Safety gates include:

- Minimum confidence requirement
- Unknown-cause protection
- Fraud protection
- Insufficient-funds protection
- High-value transaction protection

### 4. Recover

Approved recovery actions are simulated.

Examples include:

```text
send_payment_retry_prompt
send_checkout_resume_prompt
send_cart_reminder
manual_review
```

No real payment or customer communication is performed.

### 5. Measure

The revenue simulator estimates:

- Eligible sessions
- Eligible value
- Successful recoveries
- Recovered revenue
- Recovery rate
- Revenue recovery rate

---

# 🤖 Why This Is Agentic

This is not simply a classification model.

The system performs a complete decision loop:

```text
Checkout Event
      ↓
Risk Detection
      ↓
Cause Diagnosis
      ↓
Evidence Evaluation
      ↓
Policy Decision
      ↓
Action Selection
      ↓
Simulated Execution
      ↓
Audit Logging
      ↓
Revenue Measurement
```

The diagnosis layer provides intelligence, while the policy layer determines what the system is actually allowed to do.

This separation is intentional.

The AI can recommend a cause, but it cannot bypass the safety policy.

---

# 🧠 Hybrid AI Diagnosis

The diagnosis architecture combines two approaches.

```text
                  Checkout Session
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Rule-Based Engine       ML Classifier
              │                     │
              │                Random Forest
              │                     │
              └──────────┬──────────┘
                         ▼
                 Hybrid Diagnoser
                         │
                         ▼
                Final Diagnosis
                         │
                         ▼
                  Policy Engine
```

## Rule-Based Diagnosis

The rule engine uses observable checkout features such as:

- Payment method
- Device
- Checkout duration
- Cart value

It produces:

```text
cause
confidence
reasoning
```

The rule engine is deliberately explainable.

---

## Machine Learning Diagnosis

The ML model uses a Random Forest classifier.

### Input features

```text
cart_value
payment_method
device
checkout_duration_minutes
```

### Target

```text
true_cause
```

`true_cause` is used only as the training target.

It is **never provided as an input feature** during prediction.

### Preprocessing

Categorical features are one-hot encoded:

```text
payment_method
device
```

Numeric features are passed directly:

```text
cart_value
checkout_duration_minutes
```

### Model

```text
RandomForestClassifier
n_estimators = 300
class_weight = balanced
random_state = 42
```

---

# 🔀 Hybrid Decision Logic

The hybrid layer compares the rule-based and ML diagnoses.

### Agreement

If both systems agree and both are sufficiently confident:

```text
Rule diagnosis = ML diagnosis
        ↓
Hybrid agreement
        ↓
Final diagnosis
```

The final confidence uses the weaker of the two confidence values.

This prevents a highly confident model from hiding a weak second signal.

### Rule fallback

If the rule engine is actionable but the ML model is not:

```text
Rule diagnosis retained
```

### ML fallback

If the ML model is actionable but the rule engine is not:

```text
ML diagnosis retained
```

### Disagreement

If both are actionable but disagree, the system selects the stronger supported confidence.

### Insufficient evidence

If neither system provides sufficient evidence:

```text
unknown
```

The hybrid diagnosis layer never authorizes a recovery action.

That responsibility belongs to the policy engine.

---

# 🛡️ Safety-First Policy Engine

The system is designed around bounded automation.

The policy engine contains multiple safety gates.

## Confidence Gate

Low-confidence diagnoses cannot automatically trigger recovery.

```text
confidence < 0.50
        ↓
no_action
```

---

## Unknown Cause Gate

If the cause cannot be reliably identified:

```text
unknown
   ↓
no_action
```

---

## Fraud Gate

Fraud-suspected sessions are never automatically recovered.

```text
fraud_suspected
       ↓
manual_review
```

No automated recovery or incentive is permitted.

---

## Insufficient Funds Gate

Insufficient-funds cases do not trigger automated recovery.

---

## High-Value Gate

Transactions above the automatic recovery limit are escalated.

```text
cart value > ₹10,000
        ↓
manual_review
```

---

## Bounded Recovery

Only explicitly approved recovery actions can be executed.

The policy engine does not allow arbitrary actions.

---

# 💰 Business Impact

The current synthetic evaluation contains:

| Metric | Result |
|---|---:|
| Total sessions | 5,000 |
| Abandoned sessions | 2,470 |
| Completed sessions | 2,530 |
| Value at risk | ₹10,754,115.34 |
| Eligible sessions | 1,772 |
| Eligible value | ₹6,187,205.63 |
| Successful recoveries | 899 |
| Recovered revenue | ₹2,824,402.06 |
| Recovery rate | 50.73% |
| Revenue recovery rate | 45.65% |

These are **simulation results on synthetic checkout data**, not production Razorpay results.

---

# 📊 ML Evaluation

The Random Forest diagnosis model was evaluated using a held-out test set.

```text
Training samples : 1,976
Test samples     : 494
```

| Metric | Result |
|---|---:|
| Accuracy | 68.22% |
| Macro Precision | 66.11% |
| Macro Recall | 69.21% |
| Macro F1 | 67.27% |

The model is intentionally not treated as the sole decision-maker.

Its predictions are combined with the explainable diagnosis engine before reaching the policy layer.

---

# 🔬 Hybrid Evaluation

Across the evaluation:

| Hybrid outcome | Sessions |
|---|---:|
| Hybrid Agreement | 1,234 |
| Rule Fallback | 130 |
| ML Fallback | 554 |
| Rule Preferred | 193 |
| ML Preferred | 51 |
| Insufficient Evidence | 308 |

This provides visibility into how the two diagnosis mechanisms interact rather than hiding the model's behavior behind a single prediction.

---

# 🛡️ Safety Evaluation

Safety behavior is explicitly measured.

| Safety metric | Result |
|---|---:|
| Fraud escalations | 112 |
| High-value escalations | 100 |
| Automated fraud recoveries | **0** |

The key safety property is:

```text
Fraud detected
     ↓
Escalation
     ↓
No automated recovery
```

This demonstrates that revenue optimization is constrained by safety policy rather than allowed to operate without boundaries.

---

# 📈 Recovery Outcomes

The evaluated policy produced:

```text
Recover       : 1,772
No action     : 3,016
Escalate      :   212
```

Simulated actions:

```text
1,984
```

Revenue simulation:

```text
Value at risk        : ₹10,754,115.34
Eligible value       : ₹6,187,205.63
Recovered revenue    : ₹2,824,402.06
Recovery rate        : 50.73%
Revenue recovery     : 45.65%
```

---

# 📊 Dashboard

The project includes a Streamlit dashboard providing visibility into the complete recovery pipeline.

The dashboard displays:

- Checkout sessions
- Value at risk
- Recovered revenue
- Recovery rate
- Eligible sessions
- Successful recoveries
- Abandonment causes
- Agent decisions
- Payment-method behavior
- Device behavior
- Recovery performance by cause
- Individual session explorer
- Decision audit trail

The dashboard is intended to make the agent's decisions inspectable rather than presenting only a final revenue number.

---

# 🔎 Session-Level Explainability

Each processed session can expose information such as:

```text
session_id
status
cart_value
payment_method
device
cause
confidence
decision
action
eligible
recovered
recovered_revenue
```

The diagnosis also records:

```text
diagnosis_source
rule_cause
rule_confidence
ml_cause
ml_confidence
agreement
ml_probabilities
```

This allows the reasoning behind an automated decision to be inspected.

---

# 🧾 Decision Audit Trail

Every processed session can be recorded in the audit trail.

The audit contains information including:

```text
timestamp
session_id
diagnosis
confidence
policy_decision
action
execution_status
reason
execution_message
```

Completed sessions are explicitly recorded as untouched.

Example:

```text
policy_decision : no_action
execution_status: not_executed
reason          : Session was completed successfully.
```

This creates an auditable record of system behavior.

---

# 🏗️ System Architecture

```text
                         ┌────────────────────┐
                         │ Checkout Sessions  │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │  Risk Detection    │
                         └──────────┬─────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │     Hybrid Diagnosis        │
                    │                             │
                    │ ┌─────────┐   ┌──────────┐ │
                    │ │ Rules   │ + │ Random   │ │
                    │ │ Engine  │   │ Forest   │ │
                    │ └─────────┘   └──────────┘ │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │   Policy Engine    │
                         │                    │
                         │ Confidence Gate    │
                         │ Fraud Gate         │
                         │ Value Gate         │
                         │ Unknown Gate       │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │ Recovery Agent     │
                         │                    │
                         │ Simulated Action   │
                         └──────────┬─────────┘
                                    │
                         ┌──────────┴─────────┐
                         ▼                    ▼
                ┌────────────────┐   ┌────────────────┐
                │ Audit Logger   │   │ Revenue        │
                │                │   │ Simulator      │
                └────────────────┘   └───────┬────────┘
                                             │
                                             ▼
                                    ┌────────────────┐
                                    │ Dashboard      │
                                    └────────────────┘
```

---

# 📁 Project Structure

```text
checkout-recovery-agent/
│
├── data/
│   └── sessions.json
│
├── dashboard/
│   └── app.py
│
├── evaluation/
│   └── system_evaluation.md
│
├── models/
│   └── checkout_diagnosis.joblib
│
├── scripts/
│   └── evaluate_system.py
│
├── src/
│   ├── __init__.py
│   ├── audit_logger.py
│   ├── detector.py
│   ├── diagnoser.py
│   ├── generate_data.py
│   ├── hybrid_diagnoser.py
│   ├── ml_diagnoser.py
│   ├── policy_engine.py
│   ├── recovery_agent.py
│   └── revenue_simulator.py
│
├── tests/
│   ├── test_diagnoser.py
│   ├── test_hybrid_diagnoser.py
│   ├── test_ml_diagnoser.py
│   └── ...
│
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/rohithvandadi07-ux/checkout-recovery-agent.git
cd checkout-recovery-agent
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🧪 Run Tests

Run the complete test suite:

```bash
pytest -q
```

Current result:

```text
76 passed
```

The tests cover diagnosis, ML prediction, hybrid diagnosis, policy behavior, recovery-agent behavior, and other core components.

---

# 🤖 Train the ML Model

Run:

```bash
python -m src.ml_diagnoser
```

Example output:

```text
ML CHECKOUT DIAGNOSIS

Training samples : 1976
Test samples     : 494
Accuracy         : 0.6822
Macro Precision  : 0.6611
Macro Recall     : 0.6921
Macro F1         : 0.6727
```

The trained model is stored locally at:

```text
models/checkout_diagnosis.joblib
```

---

# 🔬 Run System Evaluation

Run:

```bash
python -m scripts.evaluate_system
```

This evaluates:

- Dataset statistics
- ML performance
- Hybrid diagnosis behavior
- Policy outcomes
- Revenue impact
- Safety behavior

The detailed evaluation is documented in:

```text
evaluation/system_evaluation.md
```

---

# 💻 Run the Dashboard

Start Streamlit:

```bash
streamlit run dashboard/app.py
```

Then open the local Streamlit URL shown in the terminal.

The dashboard provides an interactive view of the simulated recovery system.

---

# 🧪 Example Diagnosis

Example abandoned session:

```python
session = {
    "session_id": "cs_demo",
    "cart_value": 2500.0,
    "payment_method": "UPI",
    "device": "mobile",
    "checkout_duration_minutes": 0.8,
    "status": "abandoned"
}
```

The hybrid system can produce:

```text
cause:
otp_timeout

confidence:
0.73

diagnosis_source:
hybrid_agreement
```

The rule and ML systems both identify the same likely cause.

---

# 🚨 Example Fraud Case

Example:

```python
session = {
    "session_id": "cs_fraud_demo",
    "cart_value": 20000.0,
    "payment_method": "card",
    "device": "desktop",
    "checkout_duration_minutes": 0.3,
    "status": "abandoned"
}
```

The system identifies:

```text
Diagnosis:
fraud_suspected

Policy:
escalate

Action:
manual_review
```

The recovery action is not automatically executed.

This is a deliberate safety boundary.

---

# 🔐 Design Principles

## Explainability

The system should be able to explain why a session received a diagnosis.

## Bounded Automation

The AI does not have unrestricted control over recovery actions.

## Conservative Decision-Making

When evidence is insufficient, the system can choose:

```text
no_action
```

instead of forcing a recovery decision.

## Safety Before Revenue

Fraud and high-value cases are escalated rather than automatically recovered.

## Auditability

Decisions and simulated executions are logged.

## Separation of Concerns

Diagnosis and policy are separate components.

```text
Diagnosis:
"What is probably happening?"

Policy:
"What are we allowed to do?"
```

---

# ⚠️ Current Limitations

This is a prototype and not a production payment-recovery system.

Current limitations include:

1. The dataset is synthetic.
2. The system is not connected to live Razorpay payment events.
3. Recovery actions are simulated.
4. No real customer communication is triggered.
5. The ML model currently achieves 68.22% accuracy.
6. The feature set is intentionally small.
7. The system does not yet learn continuously from real production outcomes.
8. Revenue recovery results are simulation estimates rather than real business results.

These limitations are intentionally documented rather than hidden.

---

# 🚀 Future Roadmap

## Phase 1 — Production Data

Replace synthetic checkout sessions with anonymized real checkout telemetry.

Potential signals:

```text
payment state transitions
gateway response codes
latency
retry count
checkout step
session duration
device/network context
```

## Phase 2 — Online Learning

Use actual recovery outcomes as feedback.

```text
Prediction
    ↓
Recovery
    ↓
Outcome
    ↓
Feedback
    ↓
Model improvement
```

## Phase 3 — Experimentation

Introduce controlled experiments to measure:

- Incremental conversion
- Recovery uplift
- Customer response
- False-positive recovery
- Revenue per intervention

## Phase 4 — Payment Platform Integration

Connect the recovery intelligence layer to appropriate payment and checkout infrastructure.

The policy engine would remain the safety boundary.

## Phase 5 — Real-Time Agent

Move from batch simulation toward event-driven processing:

```text
Checkout event
      ↓
Real-time detection
      ↓
Diagnosis
      ↓
Policy
      ↓
Bounded action
      ↓
Outcome
```

---

# 🎯 Razorpay-Oriented Use Case

A payment platform can observe millions of checkout attempts.

Instead of treating every abandoned checkout identically, a recovery intelligence layer can distinguish between different situations.

For example:

```text
OTP timeout
    ↓
Payment retry prompt

Network interruption
    ↓
Checkout resume prompt

Price shock
    ↓
Cart reminder

Fraud suspicion
    ↓
Manual review

Low confidence
    ↓
No action

High-value transaction
    ↓
Manual review
```

The key idea is:

> **Do not recover every abandoned checkout. Recover the right ones, using evidence and bounded policies.**

---

# 📌 Key Takeaway

Checkout Recovery Intelligence transforms checkout abandonment from a passive analytics problem into a decision-making problem.

Instead of:

```text
Customer abandoned checkout.
```

the system attempts to answer:

```text
Why did they abandon?
        ↓
How confident are we?
        ↓
Is recovery safe?
        ↓
What action is allowed?
        ↓
Did the action recover revenue?
```

This creates a closed-loop architecture:

```text
DETECT
  ↓
DIAGNOSE
  ↓
DECIDE
  ↓
RECOVER
  ↓
MEASURE
  ↺
```

---

# 📊 Current Prototype Results

```text
5,000 checkout sessions evaluated

₹10.75M value at risk

1,772 eligible recovery sessions

899 successful simulated recoveries

₹2.82M simulated recovered revenue

50.73% recovery rate

45.65% revenue recovery rate

68.22% ML accuracy

67.27% ML Macro F1

1,234 hybrid diagnosis agreements

112 fraud escalations

100 high-value escalations

0 automated fraud recoveries

76 tests passing
```

> Results are based on the project's synthetic simulation environment and should not be interpreted as production performance.

---

# 🏁 Status

**Prototype status: Functional end-to-end system**

Implemented:

- [x] Checkout data generation
- [x] Checkout risk detection
- [x] Explainable diagnosis
- [x] Random Forest diagnosis
- [x] Hybrid diagnosis
- [x] Bounded policy engine
- [x] Fraud escalation
- [x] High-value escalation
- [x] Simulated recovery execution
- [x] Audit logging
- [x] Revenue simulation
- [x] Streamlit dashboard
- [x] System evaluation
- [x] Automated tests

---

## License

This project is a prototype developed for demonstration and evaluation purposes.