# ScamShield AI: How I Built a Payment Scam Detector with Strands Decider 2B and Amazon Bedrock

By Kalaiyarasi

Digital payment fraud is rising fast across India and the world. UPI scams, lottery fraud, impersonation calls, fake KYC requests -- people lose money every day because they could not tell a legitimate request from a scam in time. I wanted to build something simple: describe a payment request in plain chat, get a risk verdict before you act.

The headline result: Strands Decider 2B classifies the risk in about 3 seconds -- 6.9x faster than asking the LLM the same questions -- and does it with calibrated per-signal probabilities that let the agent explain exactly which red flag fired.

## The project

ScamShield AI is a chatbot that takes any payment transaction description and returns one of three verdicts: LOW RISK, HIGH RISK, or NEEDS REVIEW. It is aimed at anyone making or receiving digital payments -- UPI transfers, bank requests, online purchases -- who wants a second opinion before confirming.

Here is a real conversation with the agent:

User: I received a payment request from an unknown person asking me to transfer Rs.15,000 urgently.

ScamShield AI: HIGH RISK [warning] - Do not transfer money yet!

Red Flags: This transaction shows high risk because it involves an unknown recipient, uses urgency as a manipulation tactic (a common scam pattern), and requests a large amount.

What to do next: Verify the person's identity directly through a known phone number or official contact. Never transfer funds based solely on a digital message without independent confirmation.

---

User: My friend Priya asked me to pay her Rs.500 for lunch via UPI.

ScamShield AI: LOW RISK [safe] - This looks like a normal payment between known contacts. Always double-check the UPI ID before confirming.

The agent has three tools: `analyze_transaction` (extracts risk indicators from the text), `lookup_scam_patterns` (matches against a library of 10 known scam types -- KYC fraud, lottery scams, impersonation calls, OTP sharing, job offer scams and more), and `get_safety_tips` (returns the most relevant advice for the flags found).

Features:
- instant risk verdict from a plain-language description
- three calibrated risk signals with per-signal probabilities
- Needs Review cases ask a follow-up question instead of guessing
- tailored safety tips for each flag type
- deployed on Amazon Bedrock AgentCore Runtime

## How I built it

The stack is Strands Agents SDK, Amazon Bedrock (Amazon Nova Pro by default), and Strands Decider 2B for the risk classification decision. I used the AWS User Group Madurai Strands Decider hackathon kit and Kiro to write the spec and scaffold the agent.

The three tools are pure Python with synthetic scam pattern data, so the demo and tests run anywhere without an external API. The agent is deployed on Amazon Bedrock AgentCore Runtime; the decision runs on the AWS User Group Madurai hosted Strands Decider 2B API, which the deployed agent can reach from AWS.

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## The decision I handed to Strands Decider 2B

Risk classification is exactly the kind of decision Strands Decider 2B is built for. The signal is language: you need to read the words of a payment request and judge what they mean. Code cannot do that -- you cannot write an if-statement for "urgency pressure" or "unknown recipient". An LLM could, but it is slow and its confidence is not calibrated: it does not tell you how sure it is.

Strands Decider 2B reads the transaction description and answers three typed questions in a single forward pass, returning a calibrated probability for each:

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

The wiring is simple: `ScamPolicyCheck.check(message)` runs before the LLM sees the message and adds the verdict and per-signal scores to the context. The thresholds are plain Python constants: above 0.60 on any signal is HIGH RISK; above 0.40 is NEEDS REVIEW; below 0.40 on all three is LOW RISK.

When the decider is below 0.70 confidence on a signal, it counts as "unsure" -- the agent still gives a verdict but the NEEDS REVIEW path asks the user for more information rather than committing to a strong warning.

## Measured

The benchmark ran on 17 labelled tune cases (30 total; 13 held out for the test split) using the AWS User Group Madurai hosted Strands Decider 2B API (strands-decider-2b-hobson-v19) and qwen3.5-4b as the LLM baseline, both running on the user group's cloud infrastructure.

| | Strands Decider 2B | qwen3.5-4b LLM |
|---|---|---|
| Latency p50 per decision | 2,990 ms | 20,727 ms |
| Latency p95 | 3,090 ms | 36,488 ms |
| Cost per 1,000 decisions | $0.035 | $0.000 |
| Answered alone at confidence >= 0.7 | 57% | 100% |

At the median the decider was 6.9x faster than the LLM.

The 57% confident share is the honest number to watch. When confidence is below 0.70 on any signal, the agent routes to NEEDS REVIEW and asks the user a clarifying question rather than committing to a verdict. That is by design -- ambiguous requests should not get a strong High Risk label that could block a legitimate payment.

The accuracy figures from this run were 0% because the benchmark ran against the old eval case format (Python booleans instead of string labels). The corrected eval cases use "yes"/"no" string labels and will produce accurate accuracy numbers on the next run. The latency and speedup numbers are real and unaffected.

< FIGURE 2 of 5: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the LLM baseline on the labelled cases

< FIGURE 3 of 5: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision: Strands Decider 2B vs the LLM

< FIGURE 4 of 5: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both systems

< FIGURE 5 of 5: upload submission/article/img/bench-confidence.png here >
Alt text: Confident share vs accuracy as the confidence threshold moves

## The reusable decision pattern

The pattern lives in `agent/decision.py`. The three noul questions, the `HIGH_RISK_THRESHOLD` and `REVIEW_THRESHOLD` constants, and the `ScamPolicyCheck` class are all you need to drop this into another agent.

To reuse it: copy `decision.py`, reword the three question descriptions for your domain (phishing email screening, loan application fraud, fake job offer detection), and adjust the thresholds. The wiring in `agent.py` is six lines: instantiate `ScamPolicyCheck`, call `.check(message)` before the LLM, inject the verdict hint into the augmented message.

This pattern works anywhere you need to classify language-based risk signals before an LLM composes a response. The key insight: the decider reads the intent in the words; your code acts on the probabilities.

## What I learned and what is next

The most useful thing Strands Decider 2B gave me was not the verdict -- it was the per-signal probability. Knowing that `unknown_recipient` is 0.95 and `urgency_pressure` is 0.54 lets the agent explain specifically what it found, rather than just saying "this looks suspicious".

The 57% confident share points to the next improvement: better option descriptions for the ambiguous middle cases. Requests from strangers for legitimate-looking amounts (an online seller, a freelancer) sit near the threshold. Sharpening the "true" description with more examples of those borderline cases should push confident share above 70%.

Next steps: connect to a live UPI fraud database via AgentCore Gateway, add image support for QR code scans, and tune on the held-out test split once the eval format is confirmed correct.

---

Code: (repo link added after publishing) . Video: (video link added after recording) . Tags: #strands-decider-2b #policy

Built with the AWS User Group Madurai Strands Decider hackathon kit
