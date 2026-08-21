# Checkout Recovery Intelligence --- System Evaluation {#checkout-recovery-intelligence--system-evaluation}

## 1. Executive Summary {#1-executive-summary}

Checkout Recovery Intelligence is an agentic checkout recovery system
designed to identify abandoned checkout sessions, diagnose likely
abandonment causes, apply bounded recovery policies, simulate recovery
actions, and measure potential revenue impact.

The system combines:

-   Checkout risk detection
-   Explainable rule-based diagnosis
-   Random Forest machine-learning diagnosis
-   Hybrid rule + ML diagnosis
-   Bounded recovery policy evaluation
-   Simulated recovery execution
-   Decision audit logging
-   Revenue recovery simulation
-   Streamlit dashboard visualization

This evaluation measures the complete pipeline on a synthetic dataset
containing 5,000 checkout sessions.

> **Important:** All revenue and recovery figures in this report are
> simulated results on synthetic data. They do not represent live
> Razorpay production performance.

## 2. Evaluation Objectives {#2-evaluation-objectives}

The evaluation answers five questions:

1.  Can the system distinguish abandoned and completed checkout
    sessions?
2.  How accurately can the ML component diagnose abandonment causes?
3.  Does the hybrid diagnosis layer provide useful agreement and
    fallback behavior?
4.  Does the policy engine prevent unsafe or unjustified automated
    recovery?
5.  What simulated revenue impact could bounded recovery produce on the
    evaluation dataset?

## 3. Dataset {#3-dataset}

The evaluation uses a synthetic checkout dataset containing 5,000
sessions.

  Metric                 Result
  -------------------- --------
  Total sessions          5,000
  Abandoned sessions      2,470
  Completed sessions      2,530

The dataset contains observable checkout attributes including cart
value, payment method, device, checkout duration, and session status.

The dataset also contains `true_cause` for supervised ML training.

### Training-target separation

The hidden `true_cause` field is used only as the supervised learning
target. It is not provided to the model as an input feature.

The ML feature set consists of:

``` text
cart_value
payment_method
device
checkout_duration_minutes
```

This separation prevents direct target leakage during model inference.

## 4. End-to-End System {#4-end-to-end-system}

``` text
Checkout Session
       |
       v
Risk Detection
       |
       v
+----------------------------+
|      Hybrid Diagnosis      |
|                            |
| Rule-based Diagnosis       |
|            +               |
| Machine Learning Diagnosis |
+----------------------------+
       |
       v
Bounded Policy Engine
       |
       +-------------------+
       |                   |
       v                   v
   Recovery            Escalation
       |                   |
       v                   v
Simulated Action       Manual Review
       |
       v
Audit Trail
       |
       v
Revenue Measurement
```

The important architectural principle is that diagnosis does not
directly authorize an action. The policy engine remains the safety
boundary.

## 5. ML Diagnosis Performance {#5-ml-diagnosis-performance}

The machine-learning component uses a Random Forest classifier.
Categorical features are one-hot encoded before classification, while
numeric features are passed directly to the classifier.

The model is evaluated using a stratified 80/20 train-test split.

  Metric               Result
  ------------------ --------
  Training samples      1,976
  Test samples            494
  Accuracy             68.22%
  Macro Precision      66.11%
  Macro Recall         69.21%
  Macro F1             67.27%

The ML model provides a learned diagnostic signal from observable
checkout behavior.

The model should not be interpreted as a fully autonomous
decision-maker. Instead, the ML prediction is combined with the
explainable rule-based diagnosis inside the hybrid diagnosis layer.

## 6. Hybrid Diagnosis {#6-hybrid-diagnosis}

The hybrid diagnosis layer combines:

1.  Explainable rule-based diagnosis
2.  Machine-learning diagnosis

It evaluates the rule-based cause and confidence, ML predicted cause and
confidence, and agreement between the two systems.

  Hybrid outcome            Sessions
  ----------------------- ----------
  Hybrid agreement             1,234
  Rule fallback                  130
  ML fallback                    554
  Rule preferred                 193
  ML preferred                    51
  Insufficient evidence          308

### Hybrid agreement

When both systems produce the same actionable diagnosis, the shared
diagnosis is retained.

The final confidence uses the weaker of the two confidence signals
rather than simply adding or averaging them.

### Rule fallback

When the rule-based diagnosis is actionable but the ML result is not
sufficiently confident, the explainable rule-based diagnosis is
retained.

### ML fallback

When the ML diagnosis is actionable but the rule-based diagnosis is not,
the ML result can contribute as a fallback.

### Disagreement

When both systems are actionable but disagree, the system applies
explicit confidence-based preference logic.

The hybrid layer itself does not authorize recovery.

## 7. Policy Outcomes {#7-policy-outcomes}

After diagnosis, every abandoned session is passed through the bounded
policy engine.

The policy engine considers diagnosis confidence, diagnosis cause, fraud
suspicion, transaction value, and availability of an approved recovery
action.

  Decision              Sessions
  ------------------- ----------
  Recover                  1,772
  No action                3,016
  Escalate                   212
  Simulated actions        1,984

The system therefore does not automatically intervene in every abandoned
checkout.

## 8. Bounded Recovery Policy {#8-bounded-recovery-policy}

The system supports a limited set of recovery actions.

  Diagnosis           Example bounded action
  ------------------- ------------------------
  OTP timeout         Payment retry prompt
  Bank page timeout   Payment retry prompt
  Network drop        Checkout resume prompt
  Price shock         Cart reminder
  Distraction exit    Checkout resume prompt

The actions are simulated. No real payment is initiated and no real
customer communication is performed by the evaluation environment.

## 9. Safety Controls {#9-safety-controls}

Safety is implemented as an explicit policy layer rather than being left
entirely to the diagnosis model.

### Confidence gate

A diagnosis below the minimum confidence threshold does not
automatically trigger recovery.

The current rule-based confidence threshold is:

``` text
0.50
```

The ML component also requires a minimum confidence before independently
contributing an actionable result.

### Unknown diagnosis

If the system does not have sufficient evidence for a reliable cause, it
returns an unknown/insufficient-evidence outcome rather than forcing an
intervention.

### Fraud protection

Suspected fraud is not eligible for automated recovery. Fraud cases are
escalated for manual review.

### High-value protection

Transactions above the configured automatic recovery value limit are
escalated rather than automatically recovered.

### Completed sessions

Completed checkout sessions are never subjected to recovery actions.

## 10. Safety Evaluation Results {#10-safety-evaluation-results}

  Safety metric                  Result
  ---------------------------- --------
  Fraud cases escalated             112
  High-value escalations            100
  Automated fraud recoveries          0

The most important safety result is:

``` text
Automated fraud recoveries = 0
```

This demonstrates that suspected fraud remains outside the automated
recovery path in the current policy configuration.

## 11. Revenue Impact Simulation {#11-revenue-impact-simulation}

The revenue simulator estimates potential recovery impact from the
policy decisions.

  Metric                            Result
  ----------------------- ----------------
  Value at risk             ₹10,754,115.34
  Eligible sessions                  1,772
  Eligible value             ₹6,187,205.63
  Successful recoveries                899
  Recovered revenue          ₹2,824,402.06
  Recovery rate                     50.73%
  Revenue recovery rate             45.65%

The system identified ₹10,754,115.34 of checkout value at risk in the
synthetic evaluation set.

Of the sessions considered eligible for automated recovery, 1,772
sessions, the simulator produced 899 successful recoveries,
corresponding to a simulated recovery rate of 50.73%.

The simulated recovered revenue was ₹2,824,402.06, with a revenue
recovery rate of 45.65%.

These are simulation results, not production measurements.

## 12. Business Interpretation {#12-business-interpretation}

The system is designed around a simple business problem:

> A checkout abandonment event does not necessarily mean a lost
> customer.

Different abandonment patterns may require different responses.

For example:

-   A short UPI session may indicate an OTP-related issue.
-   A longer netbanking session may indicate a bank-page timeout.
-   A high-value cart with a moderate checkout duration may indicate
    price sensitivity.
-   A rapid mobile checkout termination may indicate a possible network
    interruption.
-   Suspicious high-value rapid abandonment should not receive an
    automated recovery incentive.

The system therefore attempts to replace a generic:

``` text
"Customer abandoned -> send reminder"
```

strategy with:

``` text
"Customer abandoned
        |
Understand likely cause
        |
Assess confidence
        |
Apply policy
        |
Recover, ignore, or escalate"
```

## 13. Explainability {#13-explainability}

The rule-based component provides human-readable reasoning for its
diagnosis.

The hybrid layer also exposes:

``` text
rule_cause
rule_confidence
ml_cause
ml_confidence
agreement
diagnosis_source
ml_probabilities
```

This makes the diagnosis inspectable rather than producing only a
black-box label.

The dashboard exposes these decisions through the session explorer and
decision audit trail.

## 14. Auditability {#14-auditability}

Every processed session generates an audit record containing decision
information such as:

-   Session ID
-   Diagnosis
-   Confidence
-   Policy decision
-   Action
-   Execution status
-   Reason
-   Execution message
-   Timestamp

This enables the system to answer:

> What did the agent decide, why did it decide it, and what action was
> executed?

The current implementation only simulates recovery actions.

## 15. Dashboard {#15-dashboard}

The Streamlit dashboard provides visibility into:

### Business impact

-   Checkout sessions
-   Abandoned checkouts
-   Value at risk
-   Eligible value
-   Successful recoveries
-   Recovered revenue
-   Revenue recovery rate

### Agent intelligence

-   Abandonment causes
-   Policy decisions
-   Recovery behavior

### Checkout behavior

-   Abandonments by payment method
-   Abandonments by device

### Recovery performance

-   Eligible sessions by cause
-   Recovered sessions by cause
-   Eligible value by cause
-   Recovered revenue by cause
-   Recovery rate by cause
-   Revenue recovery rate by cause

### Session explorer

Individual checkout sessions can be inspected using filters for status,
decision, and diagnosis.

### Decision audit trail

The dashboard also exposes recent audit records so the agent\'s
decisions can be inspected.

## 16. Reproducibility {#16-reproducibility}

The complete evaluation can be reproduced using:

``` bash
python -m scripts.evaluate_system
```

The ML model can be independently evaluated using:

``` bash
python -m src.ml_diagnoser
```

The complete automated test suite can be executed using:

``` bash
pytest -q
```

Current test result:

``` text
76 passed
```

## 17. Automated Test Coverage {#17-automated-test-coverage}

The project currently contains automated tests covering:

-   Risk detection
-   Checkout diagnosis
-   Policy decisions
-   Recovery agent behavior
-   Revenue simulation
-   ML diagnosis
-   Hybrid diagnosis

The current full test suite result is:

``` text
76 passed
```

This provides regression protection across the main system components.

## 18. Key System Results {#18-key-system-results}

  Category                                   Result
  --------------------------------- ---------------
  Sessions evaluated                          5,000
  ML accuracy                                68.22%
  ML macro F1                                67.27%
  Hybrid agreements                           1,234
  Recovery decisions                          1,772
  Escalations                                   212
  Successful simulated recoveries               899
  Simulated recovered revenue         ₹2,824,402.06
  Recovery rate                              50.73%
  Revenue recovery rate                      45.65%
  Fraud escalations                             112
  Automated fraud recoveries                      0
  Automated tests                         76 passed

## 19. What Makes the System Different {#19-what-makes-the-system-different}

The system is not simply a machine-learning classifier.

Its architecture combines:

### Detection

Identify checkout sessions that represent potential revenue risk.

### Diagnosis

Use explainable rules and machine learning to estimate the likely
abandonment cause.

### Hybrid reasoning

Compare independent diagnostic signals and apply conservative fallback
logic.

### Decision policy

Determine whether automated recovery is actually permitted.

### Bounded action

Execute only approved simulated recovery actions.

### Safety

Prevent automated recovery for suspicious and high-value cases.

### Audit

Record what the system decided and why.

### Measurement

Estimate the resulting recovery and revenue impact.

This creates a complete:

``` text
DETECT -> DIAGNOSE -> DECIDE -> RECOVER -> MEASURE
```

loop.

## 20. Limitations {#20-limitations}

### Synthetic data

The current evaluation uses synthetic checkout sessions rather than live
production traffic.

### Simulated revenue

Recovered revenue is produced by a deterministic simulation and should
not be presented as actual business revenue.

### ML performance

The Random Forest model achieves 68.22% held-out accuracy and 67.27%
macro F1.

Therefore, the ML model should not be represented as a perfect or fully
autonomous diagnosis system.

### Feature limitations

The current model uses a small set of checkout features:

-   Cart value
-   Payment method
-   Device
-   Checkout duration

Production deployment would require richer behavioral and transactional
signals.

### Production integrations

The current system does not execute real payment operations or real
customer communications.

Those integrations would require additional production controls,
authentication, observability, consent, rate limiting, and risk
management.

## 21. Future Work {#21-future-work}

Potential future improvements include:

1.  Evaluation using real anonymized checkout telemetry.
2.  Calibration of ML confidence probabilities.
3.  More behavioral features for diagnosis.
4.  Time-aware validation on future checkout traffic.
5.  A/B testing of recovery policies.
6.  Real-time event ingestion.
7.  Production monitoring and drift detection.
8.  Customer-level frequency limits for recovery messages.
9.  More granular fraud and risk signals.
10. Integration with payment and messaging infrastructure under
    appropriate controls.

These are future extensions rather than claims about the current
prototype.

## 22. Conclusion {#22-conclusion}

Checkout Recovery Intelligence demonstrates a bounded agentic approach
to checkout recovery.

Instead of treating every abandoned checkout identically, the system:

``` text
Detects risk
    |
    v
Diagnoses the likely cause
    |
    v
Cross-checks rule and ML signals
    |
    v
Applies safety-aware policy
    |
    v
Executes only bounded simulated actions
    |
    v
Records the decision
    |
    v
Measures revenue impact
```

On the current synthetic evaluation dataset, the system processed 5,000
sessions, identified ₹10.75 million of value at risk, produced 899
successful simulated recoveries, and simulated ₹2.82 million in
recovered revenue.

At the same time, the policy layer escalated 112 fraud cases and
produced zero automated fraud recoveries.

The key design principle is:

> **AI proposes the diagnosis; policy controls the action.**

This keeps the system explainable, measurable, auditable, and bounded
while demonstrating a clear business objective: recovering checkout
value without blindly automating risky interventions.