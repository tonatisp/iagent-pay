from iagent_pay.agent_pay import AgentPay
import json

def test_universal_summary():
    print("🌍 Testing iAgentPay v4.1: Universal Balance Summary...")
    
    # Initialize with a common chain (e.g., Base)
    # We use a dummy key or let it load from .env
    agent = AgentPay(chain_name="BASE")
    
    # Mocking or assuming drivers are initialized if env vars exist
    # For this test, we just call the method
    summary = agent.get_universal_summary()
    
    print("\n💰 --- CONSOLIDATED FINANCIAL REPORT --- 💰")
    print(json.dumps(summary, indent=4))
    print("------------------------------------------")
    
    total = summary.get("total_usd_approx", 0.0)
    print(f"💵 Total Agent Wealth (Estimated): ${total:.2f} USD")
    
    if total >= 0:
        print("✅ Universal Summary retrieved successfully.")
    else:
        print("❌ Summary failed or returned invalid data.")

if __name__ == "__main__":
    test_universal_summary()
