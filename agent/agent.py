"""ScamShield AI - payment scam risk classifier.

Strands Decider 2B classifies every transaction description as Low Risk, High Risk, or
Needs Review (#policy) before the LLM composes the reply.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("Someone asked me to transfer Rs.20,000 urgently.")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, strip_thinking

from .decision import ScamPolicyCheck
from .tools import TOOLS

NAME = "ScamShield AI"

SYSTEM_PROMPT = """You are ScamShield AI, a payment scam detection assistant.

When a user describes a payment request or transaction:
1. Use analyze_transaction to extract risk indicators from the description.
2. Use lookup_scam_patterns to check for known scam types.
3. Use get_safety_tips with the relevant risk flags.
4. Give a clear verdict: LOW RISK [safe], HIGH RISK [warning], or NEEDS REVIEW [check]
5. Explain the red flags you found in 2-3 sentences.
6. Share the most relevant safety tips.

Be direct, helpful and concise. Never alarm the user unnecessarily for low-risk transactions.
For Needs Review cases, ask one specific follow-up question to clarify the risk."""


class HackathonAgent:
    """ScamShield AI: policy-pattern decider + Strands LLM agent."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None, eager: bool | None = None):
        self.decider  = decider or Decider()
        self.model_id = model_id or default_model_id()
        self.policy   = ScamPolicyCheck(self.decider)
        self.sessions: dict[str, Agent] = {}

    def _session(self, session_id: str) -> Agent:
        if session_id not in self.sessions:
            self.sessions[session_id] = Agent(
                model=agent_model(self.model_id),
                system_prompt=SYSTEM_PROMPT,
                tools=TOOLS,
                callback_handler=None,
            )
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """Classify the transaction, then let the LLM compose a human-friendly reply."""
        # 1. Run the policy check BEFORE the LLM sees the message
        before_count = len(self.policy.log)
        decision = self.policy.check(message)

        # 2. Inject the verdict as context so the LLM reply stays consistent
        verdict_hint = {
            "high_risk":    "[HIGH RISK] - scam indicators detected.",
            "needs_review": "[NEEDS REVIEW] - some risk signals present; ask for more detail.",
            "low_risk":     "[LOW RISK] - no major scam indicators found.",
        }[decision["verdict"]]

        augmented = (
            f"{message}\n\n"
            f"[ScamShield policy check: {verdict_hint} "
            f"Signals: unknown_recipient={decision['unknown_recipient']:.2f}, "
            f"urgency={decision['urgency_pressure']:.2f}, "
            f"unusual={decision['unusual_payment']:.2f}]"
        )

        agent = self._session(session_id)
        t0 = time.perf_counter()
        result = agent(augmented)
        reply  = strip_thinking(str(result))
        latency_ms = round((time.perf_counter() - t0) * 1000)

        return {
            "reply":      reply,
            "decisions":  self.policy.log[before_count:],
            "model_id":   self.model_id,
            "latency_ms": latency_ms,
            "agent":      NAME,
        }


if __name__ == "__main__":
    import json, sys
    a = HackathonAgent()
    demos = [
        "I received a payment request from an unknown person asking me to transfer Rs.15,000 urgently.",
        "My friend Priya asked me to pay her Rs.500 for lunch via UPI.",
        "Someone claiming to be from the Income Tax department asked me to pay Rs.50,000 immediately or face arrest.",
    ]
    for msg in sys.argv[1:] or demos:
        print(f"\n>>> {msg}")
        print(json.dumps(a.chat(msg), indent=2, ensure_ascii=False))
