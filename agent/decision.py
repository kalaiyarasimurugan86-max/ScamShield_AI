"""REUSABLE DECISION PATTERN: payment scam risk classifier  (#policy)

What it does
    Before the agent responds to a payment-related message, Strands Decider 2B reads the
    transaction description and answers three risk questions:
    - Is the recipient unknown or unverified?
    - Is there urgency pressure ("act now", "urgent", "limited time")?
    - Is the amount or payment method unusual or suspicious?
    The answers are combined into a verdict: Low Risk, High Risk, or Needs Review.
    High Risk blocks the action with a warning; Needs Review asks the user for more detail;
    Low Risk lets the conversation continue normally.

Typed questions and options
    unknown_recipient (noul): P(yes) = probability the recipient is unknown/unverified.
    urgency_pressure  (noul): P(yes) = probability urgency is being used to rush the user.
    unusual_payment   (noul): P(yes) = probability the amount or method is suspicious.
    See QUESTIONS below for full descriptions.

Wiring
    `ScamPolicyCheck` is instantiated in agent/agent.py and called before the LLM replies.
    The state is the raw user message (the transaction description).
    The verdict and per-signal probabilities are stored in the agent's decision log.

How to reuse it
    Copy this file, keep the three noul questions, and reword the option descriptions for your
    domain (e.g. phishing email classification, loan application fraud screening).
    Adjust the HIGH_RISK_THRESHOLD and REVIEW_THRESHOLD constants to tune sensitivity.
"""

from __future__ import annotations

from decider_kit import Decider

PATTERN_TAG = "#policy"

# Tune these on the bench --split tune run; report numbers from --split test
HIGH_RISK_THRESHOLD = 0.60   # any signal above this -> High Risk
REVIEW_THRESHOLD    = 0.40   # any signal above this (but below HIGH) -> Needs Review

QUESTIONS = {
    "unknown_recipient": Decider.noul(
        "Is the recipient of this payment unknown, unverified, or not personally known to the sender?",
        {
            "true":  "the person or entity requesting payment is a stranger, has an unfamiliar name, "
                     "or cannot be verified through a known contact or official channel",
            "false": "the recipient is a known contact, a recognized business, or a verified official entity",
        },
    ),
    "urgency_pressure": Decider.noul(
        "Does the message use urgency, time pressure, or emotional pressure to push the sender to act immediately?",
        {
            "true":  "phrases like 'act now', 'urgent', 'last chance', 'emergency', 'or your account will be closed', "
                     "or emotional appeals that discourage taking time to verify",
            "false": "no time pressure; the sender is free to verify before acting",
        },
    ),
    "unusual_payment": Decider.noul(
        "Is the payment amount, method, or reason unusual or suspicious for a legitimate transaction?",
        {
            "true":  "very large or round amounts with no clear reason, requests for gift cards, "
                     "wire transfers to unknown accounts, requests to share OTPs or PINs, "
                     "or a reason that does not match the payment method",
            "false": "normal amount for the stated purpose, standard payment method, no request for sensitive info",
        },
    ),
}


class ScamPolicyCheck:
    """Runs the three-question policy check and returns a structured verdict."""

    def __init__(self, decider: Decider):
        self.decider = decider
        self.log: list[dict] = []

    def check(self, transaction_description: str) -> dict:
        """Check a transaction description and return verdict + per-signal details."""
        a = self.decider.ask(transaction_description, QUESTIONS)

        p_unknown  = a["unknown_recipient"].p_yes or 0.0
        p_urgency  = a["urgency_pressure"].p_yes or 0.0
        p_unusual  = a["unusual_payment"].p_yes or 0.0
        max_signal = max(p_unknown, p_urgency, p_unusual)
        decider_ms = round(self.decider.last_latency_ms or 0)

        if max_signal >= HIGH_RISK_THRESHOLD:
            verdict = "high_risk"
        elif max_signal >= REVIEW_THRESHOLD:
            verdict = "needs_review"
        else:
            verdict = "low_risk"

        # flag any signal that crossed the review threshold
        flags = []
        if p_unknown  >= REVIEW_THRESHOLD: flags.append("unknown_recipient")
        if p_urgency  >= REVIEW_THRESHOLD: flags.append("urgency_pressure")
        if p_unusual  >= REVIEW_THRESHOLD: flags.append("unusual_payment")

        record = {
            "pattern":          PATTERN_TAG,
            "verdict":          verdict,
            "flags":            flags,
            "unknown_recipient": round(p_unknown,  3),
            "urgency_pressure":  round(p_urgency,  3),
            "unusual_payment":   round(p_unusual,  3),
            "confidence":        round(max_signal, 3),
            "decider_ms":        decider_ms,
            # fields the demo panel and bench expect
            "probabilities": {
                "unknown_recipient": round(p_unknown,  3),
                "urgency_pressure":  round(p_urgency,  3),
                "unusual_payment":   round(p_unusual,  3),
            },
        }
        self.log.append(record)
        return record
