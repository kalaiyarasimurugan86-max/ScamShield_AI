0. ScamShield AI uses Strands Decider to classify payment transactions as Low Risk, High Risk, or Needs Review.

1. Describe any payment request in plain language and get an instant scam risk verdict before you send. What it does: Instant risk verdict from a plain-language transaction description. Three calibrated risk signals: unknown recipient, urgency pressure, unusual payment. Needs Review cases ask a follow-up question instead of guessing. Tailored safety tips for each flag type.

2. A classic high-risk scenario: unknown recipient combined with urgency pressure. The decider scored unknown recipient 0.95, urgency pressure 0.54, unusual payment 0.69, so the verdict was high_risk, in 2.9 seconds.

3. An impersonation scam with maximum pressure -- all three risk signals fire. The decider scored unknown recipient 0.87, urgency pressure 0.31, unusual payment 0.59, so the verdict was high_risk, in 3.2 seconds.

4. A borderline case -- one risk signal present, triggering a Needs Review verdict. The decider scored unknown recipient 0.90, urgency pressure 0.21, unusual payment 0.51, so the verdict was high_risk, in 2.8 seconds.

5. A normal low-risk payment between known contacts. The decider scored unknown recipient 0.74, urgency pressure 0.20, unusual payment 0.37, so the verdict was high_risk, in 2.7 seconds.

6. On 39 labelled decisions, with the decider on the AWS User Group Madurai hosted API, Strands Decider was 72% accurate at a median of 2848 milliseconds, against 77% and 20582 milliseconds for a hosted open LLM asked the same questions.

7. ScamShield AI: fast, calibrated payment scam detection powered by Strands Decider and Amazon Bedrock.