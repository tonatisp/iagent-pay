"""
🚀 iAgentPay v5.0 — The Ultimate Banking Infrastructure for AI Agents.
Demo Script for X/Twitter.

Features showcased:
1. Sub-Agent Fleet Management
2. Atomic Safety Kernel (Budget & Rate Limits)
3. Know Your Agent (KYA) Decentralized Reputation
4. Real-time Observability & Anomaly Detection
"""
import time
from iagent_pay.sub_agents import SubAgentManager
from iagent_pay.kya import KYARegistry, AgentIdentity
from iagent_pay.observability import get_observer, ObservabilityConfig

print(">>> INITIALIZING iAgentPay v5.0 INFRASTRUCTURE...")
time.sleep(1)

# 1. Start Observability
observer = get_observer()
observer.config = ObservabilityConfig(enable_anomaly_detection=True)

# 2. Setup Fleet Manager
manager = SubAgentManager(master_budget_usd=100.0)
researcher = manager.create(
    name="ResearcherBot-7", 
    daily_limit_usd=20.0, 
    max_tx_usd=5.0
)
print(f"\n[OK] Created Sub-Agent: {researcher.name}")
print(f"[API] Key: {researcher.api_key[:15]}...")

# 3. Register Decentralized Identity (KYA)
registry = KYARegistry()
identity = AgentIdentity.create(researcher.name, "0xAgentOwner123")
registry.register(identity)
print(f"\n[SEC] KYA Identity Registered: {identity.did}")
print(f"[STAT] Initial Trust Level: {registry.get_trust_level(identity.did).name}")

print("\n>>> SIMULATING AUTONOMOUS AGENT PAYMENTS...")
time.sleep(1)

# Agent pays for data APIs
payments = [
    (2.0, "Weather API"),
    (4.5, "Financial Data X402"),
    (1.5, "Search API"),
]

for amount, desc in payments:
    # 4. Atomic Safety Kernel Check
    try:
        researcher.kernel.check(amount, "0xVendor")
        researcher.spend(amount, "USDC", desc)
        observer.record_payment(amount, "USDC", "0xVendor", True)
        
        # Build Agent Reputation!
        registry.update_after_payment(identity.did, success=True, amount_usd=amount)
        print(f"  [SUCCESS] Paid ${amount} USDC for {desc}")
    except Exception as e:
        print(f"  [BLOCKED] ${amount} USDC for {desc} -> {e}")
    time.sleep(0.5)

print("\n>>> SIMULATING MALICIOUS HACK / ANOMALY...")
time.sleep(1)
try:
    anomaly_amount = 50.0
    print(f"  [WARN] Agent attempts to send ${anomaly_amount} to unknown wallet...")
    researcher.kernel.check(anomaly_amount, "0xHacker")
    researcher.spend(anomaly_amount, "USDC", "Ransom")
except Exception as e:
    observer.record_budget_block(str(e), anomaly_amount, "USDC")
    print(f"  [INTERVENTION] SAFETY KERNEL INTERVENED: {e}")

print("\n>>> FINAL OBSERVABILITY DASHBOARD:")
observer.print_dashboard()

print("\n>>> FINAL KYA REPUTATION REPORT:")
report = registry.get_full_report(identity.did)
print(f"  - DID: {report['did']}")
print(f"  - Trust Level: {report['trust_level']}")
print(f"  - ART Score: {report['art_score']}/100")
print(f"  - Successful Tx: {report['tx_count']}")

print("\n*** iAgentPay v5.0 - The Standard for Autonomous Economy. ***")
print("*** pip install iagent-pay ***")
