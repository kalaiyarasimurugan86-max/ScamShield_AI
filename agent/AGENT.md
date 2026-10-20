# Use case

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
