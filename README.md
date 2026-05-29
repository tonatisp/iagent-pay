<div align="center">
  <img src="https://img.shields.io/badge/iAgentPay-v8.5.0-blue?style=for-the-badge&logo=python" alt="iAgentPay Version" />
  <img src="https://img.shields.io/badge/Modules-25-purple?style=for-the-badge" alt="25 Modules" />
  <img src="https://img.shields.io/badge/Chains-6-orange?style=for-the-badge" alt="6 Chains" />
  <a href="docs/MANUAL_iAgentPay_v8.pdf"><img src="https://img.shields.io/badge/Manual-PDF_Download-red?style=for-the-badge&logo=adobeacrobatreader" alt="Manual PDF" /></a>
  <img src="https://img.shields.io/badge/Languages-ES%20%7C%20EN%20%7C%20ZH%20%7C%20HI-green?style=for-the-badge" alt="4 Languages" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Security-Hardened_v4.0-red?style=for-the-badge" alt="Security" />

  <h1>🤖💸 iAgentPay</h1>
  <p><b>The Universal Banking Layer for Autonomous AI Agents.</b></p>
  <p>25 modules · 6 blockchains · Stripe/ACH · MCP · CrewAI · LangChain · Claude</p>
</div>

iAgentPay gives any AI system (CrewAI, LangChain, Claude, Cursor, AutoGPT) its own wallet, budget control, and the ability to send payments in **Crypto (USDC, ETH, SOL, XRP)** and **Fiat (Stripe/ACH)** — all protected by an atomic Safety Kernel.

---

## ⚡ Quick Install

```bash
pip install "iagent-pay"            # Core SDK
pip install "iagent-pay[fastapi]"   # x402 Server middleware
pip install "iagent-pay[crewai]"    # CrewAI integration
pip install "iagent-pay[langchain]" # LangChain integration
pip install "iagent-pay[fiat]"      # Stripe/ACH Fiat Bridge
pip install "iagent-pay[all]"       # Everything
```

```bash
iagent-pay init my-ai-project   # Scaffold a new agent project
iagent-pay status               # Check agent balance
iagent-pay faucet               # Get testnet faucet links
iagent-pay mcp-server           # Start MCP server for Claude/Cursor
```

---

## 🌟 Why iAgentPay? (vs Competition)

| Feature | iAgentPay v8.5 | Coinbase AgentKit | Stripe Agent Toolkit | OmniAgentPay |
| :--- | :---: | :---: | :---: | :---: |
| **True Multi-Chain** | ✅ (6 chains) | ❌ (EVM only) | ❌ (No crypto) | ✅ |
| **Fiat Bridge (Stripe/ACH)** | ✅ Smart Router | ❌ | ✅ | ❌ |
| **Atomic Safety Kernel** | ✅ (4 layers) | ⚠️ Basic | ❌ | ✅ |
| **Sub-Agent Fleet Mgmt** | ✅ Isolated budgets | ❌ | ❌ | ❌ |
| **HTTP 402 Autopay (x402)** | ✅ | ❌ | ❌ | ❌ |
| **MCP Server (Claude/Cursor)** | ✅ | ❌ | ❌ | ❌ |
| **Human-in-the-Loop** | ✅ Telegram/Slack | ❌ | ❌ | ❌ |
| **Data Marketplace** | ✅ | ❌ | ❌ | ❌ |
| **Reputation System** | ✅ On-chain | ❌ | ❌ | ❌ |
| **LangChain + CrewAI tools** | ✅ Native | ⚠️ Partial | ❌ | ❌ |
| **25 Hardened Modules** | ✅ | ❌ | ❌ | ❌ |

---

## 📚 Complete Module Reference (25 Modules)

| # | Module | Description |
|----|-----------------------------------------------|-------------|
| 1  | 🌎 **Multi-Chain Core** (`agent_pay`)         | ETH, Base, Polygon, Arbitrum, BNB, Solana, XRP |
| 2  | ⚡ **x402 Autopay Client** (`x402_client`)    | Pay-per-use APIs: autonomous HTTP 402 payments |
| 3  | 🛡️ **Safety Kernel** (`safety_kernel`)       | 4-layer protection: daily/weekly/session/tx caps |
| 4  | 📈 **DeFi Treasury** (`yield_protocols`)      | Autonomous Aave v3 yield on idle balances |
| 5  | 🏦 **Fiat Bridge** (`fiat_bridge`)            | Stripe + ACH + Smart Router (crypto vs bank) |
| 6  | 🌉 **Cross-Chain Router** (`cross_chain`)     | Automatic bridge selection between 6 networks |
| 7  | 🤖 **Fleet Manager** (`sub_agents`)           | Sub-agent teams with isolated budgets |
| 8  | 🌐 **Token Dictionary** (`tokens`)            | 6 chains, 20+ tokens (Yuan, Yen, Peso, Euro…) |
| 9  | ⚙️ **Advanced Safety** (`safety_kernel`)     | Rate limiting, whitelist, human approval threshold |
| 10 | 💳 **Wallet Manager** (`wallet_manager`)      | AES-128 encrypted keystores, OS env var support |
| 11 | 🔤 **Social Resolver** (`social_resolver`)    | Pay by ENS name or Solana domain (.eth, .sol) |
| 12 | 🔔 **Webhooks** (`webhooks`)                  | HMAC-SHA256 signed events (Stripe standard) |
| 13 | 👤 **Human-in-the-Loop** (`human_loop`)       | Telegram/Slack approval for large payments |
| 14 | 🔄 **Swap Engine** (`swap_engine`)            | Real quotes: Jupiter (Solana) + 0x Protocol (EVM) |
| 15 | 🛒 **Data Marketplace** (`data_marketplace`)  | Decentralized registry of x402-enabled API providers |
| 16 | 🤝 **Reputation System** (`reputation_manager`) | 0-5 star peer ratings, exportable, tamper-proof |
| 17 | 🤖 **MCP Server** (`mcp_server`)              | Claude/Cursor/Windsurf native integration |
| 18 | 💻 **CLI** (`cli`)                            | `init`, `status`, `faucet`, `mcp-server` commands |
| 19 | 🌐 **x402 Server** (`x402_server`)            | FastAPI + Flask middleware to sell data for USDC |
| 20 | 📊 **Observability** (`observability`)        | Prometheus metrics, anomaly detection, JSON logs |
| 21 | 💵 **Pricing Engine** (`pricing`)             | Live ETH/SOL/XRP prices from 3 sources + fallback |
| 22 | 🌊 **XRP Ledger Driver** (`xrpl_driver`)      | 3-5s confirmation, <$0.001/tx, destination tags |
| 23 | 🎯 **Bounty Marketplace** (`marketplace_bridge`) | Post tasks for humans, auto-release payment |
| 24 | 🦾 **CrewAI Integration** (`integrations/crewai`) | Native payment tool for CrewAI agent teams |
| 25 | 🔗 **LangChain Integration** (`integrations/langchain`) | Native payment tool for LangChain chains |

📖 **[Read the Full Interactive Manual →](https://github.com/tonatisp/iagent-pay/blob/main/manual.html)** *(ES · EN · 中文 · हिन्दी)*

---

## 🚀 Quickstart (60 seconds)

### 1. Safety Kernel — Atomic spend limits

```python
from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig

kernel = SafetyKernel(SafetyConfig(
    daily_limit_usd=50.0,
    max_tx_usd=10.0,
    enable_whitelist=True,
    allowed_recipients=["0xTrustedVendor..."]
))

kernel.check(amount=5.0, recipient="0xTrustedVendor...")  # ✅ Approved
kernel.check(amount=100.0, recipient="0xHacker...")       # ❌ Blocked
```

### 2. Fiat Bridge — Smart routing crypto vs bank

```python
from iagent_pay.fiat_bridge import FiatBridge

bridge = FiatBridge(stripe_key="sk_live_...")
bridge.smart_send(10.0, recipient="0xAlice...")          # → USDC on Base
bridge.smart_send(10.0, recipient="user@gmail.com")      # → Stripe invoice
```

### 3. x402 Autopay — Pay APIs automatically

```python
from iagent_pay.x402_client import X402Client

client = X402Client(private_key="0x...", max_amount_usdc=0.10)
response = client.request("GET", "https://premium-api.com/data")
print(response.json())  # Paid and received automatically
```

### 4. CrewAI + LangChain Native Integration

```python
from iagent_pay.integrations.crewai import iAgentPayCrewTool
from crewai import Agent

agent = Agent(
    role="Treasurer",
    goal="Manage team payments autonomously",
    tools=[iAgentPayCrewTool(chain="BASE", max_amount_usdc=5.0)],
)
```

### 5. Sell your own data with x402 Server

```python
from fastapi import FastAPI
from iagent_pay.x402_server import X402Middleware

app = FastAPI()
app.add_middleware(X402Middleware,
    payment_address="0xYourAddress...",
    amount_usdc=0.05,
    protected_paths=["/api/premium"]
)
```

### 6. Connect Claude / Cursor (MCP)

```bash
iagent-pay mcp-server
# Add to claude_desktop_config.json — Claude can now send payments natively
```

---

## 🔐 Security (Hardened v4.0)

| Layer | Protection |
|-------|------------|
| Keys | AES-128 encrypted keystore · OS env vars · Zero plaintext storage |
| Payments | 4-cap Safety Kernel (session/daily/weekly/per-tx) |
| x402 | SQLite-persisted receipts (restart-safe, anti-double-spend) |
| Webhooks | HMAC-SHA256 signatures with nonce expiry |
| Reputation | SHA-256 checksum chain (tamper detection) |
| Audit | Full transaction log with forensic export |

---

## 🌍 Supported Networks & Tokens

| Network | Tokens |
|---------|--------|
| **Ethereum** | USDC, USDT, DAI, EURC, CNHC (Yuan), GYEN (Yen), XSGD, MXNT |
| **Base** | USDC, USDT, DAI, EURC, WETH |
| **Polygon** | USDC, USDT, DAI, WETH |
| **Arbitrum** | USDC, USDT, DAI, WETH |
| **BNB Chain** | USDC, USDT, BUSD, DAI |
| **Solana** | USDC (native), SOL |
| **XRP Ledger** | XRP (native) |

---

## 🌐 Open Source & Community

iAgentPay is 100% Open Source (MIT). Built for the next generation of the autonomous economy.

1. Fork the project
2. Create your branch: `git checkout -b feature/AmazingFeature`
3. Commit: `git commit -m 'Add some AmazingFeature'`
4. Push: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

<div align="center">
  <sub>Built with ❤️ by the iAgent Team · MIT License · v8.5.0</sub>
</div>
