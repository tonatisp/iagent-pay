from iagent_pay.agent_pay import AgentPay

def main():
    print("--- 🎁 Social Tipping Demo ---")
    
    # 1. Test ENS (Ethereum)
    print("\n1️⃣  Resolving ENS (vitalik.eth)...")
    resolver = AgentPay(chain_name="ETH") # Just for the resolver logic
    try:
        addr = resolver.social.resolve("vitalik.eth")
        print(f"✅ Resolved to: {addr}")
    except Exception as e:
        print(f"❌ ENS Failed: {e}")

    # 2. Test SNS (Solana)
    print("\n2️⃣  Resolving SNS (tobby.sol)...")
    # tobby.sol is a common test handle or we can use another known one
    resolver_sol = AgentPay(chain_name="SOL_DEVNET")
    try:
        # Note: This might fail if the name doesn't exist, but the logic runs
        addr = resolver_sol.social.resolve("tobby.sol")
        if addr:
            print(f"✅ Resolved to: {addr}")
        else:
            print("⚠️ Name not found (Expected if random handle)")
    except Exception as e:
        print(f"❌ SNS Failed: {e}")

if __name__ == "__main__":
    main()
