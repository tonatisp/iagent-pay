# 👾 Discord Announcement (for #showcase / #resources)

**Subject:** I built a Payment Standard for AI Agents (EVM + Solana)

Hey everyone! 👋

I've been working on a way to let my autonomous agents pay for their own API usage and server costs without me manually topping them up.

I just released **iAgentPay v2.1** (Open Source).

**What it does:**
*   It's a Python banking layer for AI.
*   **Dual-Chain:** Works on Ethereum (Base/Polygon) and Solana simultaneously.
*   **Safety First:** Has a built-in "Capital Guard" that limits daily spending (e.g., max $10/day) so a hallucinating model won't drain your wallet.
*   **Billing:** Agents can send invoices to each other using AIP-1 (Agent Invoice Protocol).

**Example:**
```python
agent = AgentPay(wallet, chain_name="base", daily_limit=5.0)
agent.pay_agent("vitalik.eth", 0.01) # Resolves ENS automatically
```

It's live on PyPI: `pip install iagent-pay`

Would love feedback on the security architecture if anyone here is building financial agents!

**GitHub:** [Link]
**Docs:** [Link]
