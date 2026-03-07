import os
import time
from iagent_pay.agent_pay import AgentPay

def run_v3_demo():
    print("🚀 [iAgentPay v3.0] Starting Disruptive Features Demo")
    print("-" * 50)

    # 1. Initialization (Using Base for DeFi features)
    agent = AgentPay(chain_name="BASE")
    print(f"✅ Agent Active: {agent.my_address}")

    # 2. FEATURE: AI-Bank (Auto-Yield)
    print("\n🏦 Step 1: Enabling Autonomous Banking")
    agent.enable_auto_yield(protocol="aave")
    # Simulate a deposit (Requires USDC balance in real scenario)
    # agent.yield_manager.deposit("USDC", 1.0) 
    agent.harvest_yield() # Show current treasury status

    # 3. FEATURE: autonomous Reputation System (ART)
    print("\n⭐ Step 2: Inter-Agent Trust Layer")
    peer_agent = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    print(f"Checking trust score for peer {peer_agent}...")
    score = agent.get_trust_score(peer_agent)
    print(f"Current Trust Score: {score}/5.0")
    
    print(f"Rating peer {peer_agent} after successful service...")
    agent.rate_agent(peer_agent, 5.0)

    # 4. FEATURE: Agent-to-Human Bridge (A2H)
    print("\n🤝 Step 3: Hiring a Human (A2H)")
    bounty_title = "Solve CAPTCHA for Agent Registration"
    bounty_id = agent.post_bounty(bounty_title, 2.50) # $2.50 Bounty
    
    print("Simulating human completion...")
    human_wallet = "0x1234567890123456789012345678901234567890" # Mock Human
    
    # In a real scenario, the agent would verify the result before releasing
    # agent.release_bounty(bounty_id, human_wallet)
    print(f"Manual check: Use agent.release_bounty('{bounty_id}', '{human_wallet}') to pay the human.")

    print("\n" + "-" * 50)
    print("🎯 Demo Complete: iAgentPay is now a full Economic Infrastructure.")

if __name__ == "__main__":
    run_v3_demo()
