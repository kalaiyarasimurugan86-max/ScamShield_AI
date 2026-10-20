# ScamShield AI

**ScamShield AI analyzes payment transaction descriptions and classifies them as Low Risk, High Risk, or Needs Review — before you send a single rupee.**

An agent on AWS that hands one decision to **Strands Decider 2B** and the conversation to **Amazon Bedrock**. Decision pattern: `#policy`. Tags: `#strands-decider-2b` `#policy`.

- Video: (add the YouTube/Vimeo link)
- Article: (add the AWS Builder Center link)
- Deployed: run `./kit deploy`

## The project

- **Pitch:** ScamShield AI analyzes payment transaction descriptions and classifies them as Low Risk, High Risk, or Needs Review — before you send a single rupee.
- **Who it is for:** anyone making or receiving digital payments (UPI, bank transfer, online requests) who wants a quick scam check before acting.
- **Features:**
  - describe any payment request in plain language and get an instant risk verdict;
  - Strands Decider 2B checks three risk signals: unknown recipient, urgency pressure, unusual amount or method;
  - red flag explanation with tailored safety tips;
  - Needs Review cases ask for more detail instead of guessing;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** given a transaction description, does it show signs of being a scam? (`#policy`)
- **Why a decision model:** risk classification must be fast, consistent and explainable — a calibrated probability per signal is far more useful than a freeform LLM guess.
- **Amazon Bedrock:** the conversation and tool use (Amazon Nova Pro by default).



## How it is built

Strands Agents with Amazon Bedrock for the generative part, the tools in `agent/tools.py`, deployed to Amazon Bedrock AgentCore Runtime, and one decision handed to Strands Decider 2B at a clear seam in the agent's path.

Every Amazon Bedrock model id is set in `.env` (`BEDROCK_MODEL_ID`, and `BEDROCK_SMALL/MEDIUM/LARGE_MODEL_ID` for routing), Amazon Nova by default.

![Architecture](submission/article/img/architecture.png)

## Reusable decision pattern: payment scam risk classifier  (#policy)

The pattern lives in [`agent/decision.py`](agent/decision.py), labelled `REUSABLE DECISION PATTERN`. It contains the typed questions and their options, the wiring that puts the decision in the agent's path, and a note on how to reuse it:

```text
REUSABLE DECISION PATTERN: payment scam risk classifier  (#policy)

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
```

Typed questions:

```python
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
```

## Measured

Decider: strands-decider-2b-hobson-v19 (ugmdu). 13 labelled cases, 39 decisions.

| | Strands Decider 2B | qwen3.5-4b |
|---|---|---|
| Accuracy | 71.8% | 76.9% |
| Latency p50 per decision | 2848 ms | 20582 ms |
| Latency p95 | 3092 ms | 21588 ms |
| Cost per 1,000 decisions | $0.0350 | $0.0000 |
| Answered alone at confidence >= 0.7 | 54% | 100% |
| Accuracy when confident | 76.2% | 76.9% |

At the median the decider was 7.2x faster than the LLM.

Reproduce with `./kit bench` (cases in `agent/eval_cases.jsonl`; charts in `submission/bench/`).

## Run it

```bash
./kit setup        # checks your machine and AWS, sets up Strands Decider 2B (local model or hosted API)
./kit demo         # web UI at http://localhost:8501
./kit bench        # the decision vs an Amazon Bedrock LLM
./kit deploy       # Amazon Bedrock AgentCore Runtime
```

Requirements: Python 3.10+, AWS credentials with Amazon Bedrock access, and for deploying, Node 20+ with the AgentCore CLI (`./kit agentcore-cli`).

## Credits

Built with the AWS User Group Madurai Strands Decider hackathon kit (https://github.com/awsugmdu). The kit's reusable library (`decider_kit/`, the demo UI, the video and article tooling, and the Kiro steering, skills and hooks) is the user group's; the agent in `agent/` is mine. Strands Decider: https://github.com/strands-labs/strands-decider (Apache-2.0).

Licence: Apache-2.0 (see LICENSE).
