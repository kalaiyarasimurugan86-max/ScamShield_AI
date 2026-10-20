"""ScamShield AI tools: transaction analysis, scam pattern lookup, safety tips.

All data is synthetic so the demo and tests run anywhere without an external API.
"""

from __future__ import annotations

from strands import tool

# ---------------------------------------------------------------------------
# Synthetic scam pattern library
# ---------------------------------------------------------------------------
SCAM_PATTERNS = [
    {"id": "SP001", "name": "KYC Update Scam",      "keywords": ["kyc", "update", "bank account", "verify", "blocked"],           "risk": "high"},
    {"id": "SP002", "name": "Lottery / Prize Scam",  "keywords": ["won", "prize", "lottery", "claim", "reward", "congratulations"], "risk": "high"},
    {"id": "SP003", "name": "Impersonation Scam",    "keywords": ["police", "cbi", "income tax", "irs", "officer", "arrest"],       "risk": "high"},
    {"id": "SP004", "name": "Urgent Transfer Scam",  "keywords": ["urgent", "emergency", "immediately", "right now", "asap"],       "risk": "high"},
    {"id": "SP005", "name": "OTP / PIN Sharing",     "keywords": ["otp", "pin", "password", "share", "send me", "tell me"],        "risk": "high"},
    {"id": "SP006", "name": "Job Offer Scam",        "keywords": ["job", "work from home", "part time", "earn", "registration fee"], "risk": "high"},
    {"id": "SP007", "name": "Advance Fee Scam",      "keywords": ["advance", "processing fee", "deposit first", "pay first"],       "risk": "high"},
    {"id": "SP008", "name": "Suspicious UPI ID",     "keywords": ["@ybl", "@okaxis", "random", "unknown upi"],                     "risk": "medium"},
    {"id": "SP009", "name": "Round Number Transfer", "keywords": ["50000", "1 lakh", "100000", "exact amount"],                    "risk": "medium"},
    {"id": "SP010", "name": "Normal Bill Payment",   "keywords": ["electricity", "water bill", "recharge", "dth"],                 "risk": "low"},
]

SAFETY_TIPS = {
    "unknown_recipient": [
        "Always verify the recipient's identity through an official channel before sending money.",
        "Call the person directly on a known number - do not use the number they provided.",
        "Check if the UPI ID or account belongs to a registered business.",
    ],
    "urgency_pressure": [
        "Legitimate requests never require you to act within minutes - take your time.",
        "Urgency is a classic pressure tactic used in scams; slow down and verify.",
        "If someone says 'act now or lose it', that is a red flag - hang up or stop the chat.",
    ],
    "unusual_payment": [
        "Never share your OTP, PIN or password with anyone - not even bank staff.",
        "No legitimate prize or lottery requires a fee before payout.",
        "Gift cards and wire transfers are irreversible - be extra cautious.",
    ],
    "low_risk": [
        "Always double-check the recipient's UPI ID or account number before confirming.",
        "Keep transaction records and screenshots for any disputes.",
    ],
}


@tool
def analyze_transaction(description: str) -> dict:
    """Extract key risk indicators from a payment transaction description."""
    text = description.lower()
    indicators = {
        "unknown_recipient": any(w in text for w in ["unknown", "stranger", "new contact", "never met", "random"]),
        "urgency_mentioned": any(w in text for w in ["urgent", "immediately", "right now", "asap", "emergency", "hurry"]),
        "large_amount":      any(c.isdigit() and int(''.join(filter(str.isdigit, text[:text.find(c)+5] if text.find(c) >= 0 else ''))) > 10000
                                 for c in text if c.isdigit()) if any(c.isdigit() for c in text) else False,
        "otp_pin_requested": any(w in text for w in ["otp", "pin", "password", "passcode"]),
        "gift_card":         any(w in text for w in ["gift card", "amazon card", "google play"]),
    }
    # simpler large-amount check
    import re
    amounts = re.findall(r'[\u20b9$]?\s*(\d[\d,]*)', text)
    large_amount = any(int(a.replace(',', '')) > 10000 for a in amounts if a.replace(',', '').isdigit())
    indicators["large_amount"] = large_amount

    risk_signals = [k for k, v in indicators.items() if v]
    return {
        "indicators": indicators,
        "risk_signals_found": risk_signals,
        "signal_count": len(risk_signals),
    }


@tool
def lookup_scam_patterns(description: str) -> dict:
    """Look up known scam patterns that match keywords in the transaction description."""
    text = description.lower()
    matched = []
    for pattern in SCAM_PATTERNS:
        hits = [kw for kw in pattern["keywords"] if kw in text]
        if hits:
            matched.append({
                "id":       pattern["id"],
                "name":     pattern["name"],
                "risk":     pattern["risk"],
                "matched_keywords": hits,
            })
    matched.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["risk"]])
    return {
        "patterns_matched": matched,
        "highest_risk": matched[0]["risk"] if matched else "unknown",
        "pattern_names": [m["name"] for m in matched],
    }


@tool
def get_safety_tips(flags: list[str]) -> dict:
    """Return safety tips relevant to the risk flags found in a transaction."""
    tips = []
    for flag in flags:
        tips.extend(SAFETY_TIPS.get(flag, []))
    if not tips:
        tips = SAFETY_TIPS["low_risk"]
    # deduplicate while preserving order
    seen, unique = set(), []
    for t in tips:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return {"tips": unique[:4]}  # return at most 4 tips


TOOLS = [analyze_transaction, lookup_scam_patterns, get_safety_tips]
