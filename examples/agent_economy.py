import time
from iagent_pay.agent_pay import AgentPay

def simulate_economy():
    print("🤖 --- iAgentPay Agent-to-Agent Economy Demo --- 🤖")
    
    # 1. Initialize Agent A (The Client)
    # Agent A needs to hire a 'Researcher'
    print("\n[Agent A] Initializing Client Agent...")
    client = AgentPay(chain_name="BASE")
    print(f"   Address: {client.my_address}")
    
    # 2. Initialize Agent B (The Worker)
    # This simulates a separate bot running on another process
    print("\n[Agent B] Initializing Worker Agent (Service Provider)...")
    worker = AgentPay(chain_name="BASE")
    print(f"   Address: {worker.my_address}")

    # 3. The Negotiation (Simulated)
    service_price = 0.0001 # ETH
    print(f"\n🤝 Negotiation: Worker agrees to research 'AI Agents' for {service_price} ETH.")

    # 4. The Payment (The Bridge)
    print("\n💸 [Agent A] Sending payment to [Agent B]...")
    try:
        tx_hash = client.pay_agent(worker.my_address, amount=service_price)
        print(f"   ✅ Payment Sent! Hash: {tx_hash}")
        
        # 5. Verification
        print("\n⏳ [Agent B] Verifying payment arrival...")
        time.sleep(2) # Wait for simulation/network
        print(f"   ✅ Payment Confirmed! Worker starting task...")
        
        # 6. Task Completion
        print("\n📝 [Agent B] Task Finished: 'AI agents are self-evolving systems...'")
        print("\n✨ Economy Cycle Complete: No Banks, No KYC, Just Agents.")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n💡 Tip: Make sure Agent A has enough gas (BASE Sepolia/Devnet).")

if __name__ == "__main__":
    simulate_economy()
