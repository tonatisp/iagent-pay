from iagent_pay import AgentPay, WalletManager, ChainConfig

def demo_multichain():
    print("🌍 Multi-Chain Agent Demo")
    print("=========================")
    
    wm = WalletManager()
    wallet = wm.get_or_create_wallet()
    print(f"🔑 Wallet: {wallet.address}")
    
    # 1. Connect to LOCAL
    print("\n--- Network: LOCAL ---")
    agent_local = AgentPay(wallet, chain_name="LOCAL")
    print(f"✅ Connected to Local Chain (ID: {agent_local.w3.eth.chain_id})")
    bal_local = agent_local.get_balance()
    print(f"💰 Balance: {bal_local} ETH")
    
    # 2. Connect to SEPOLIA
    print("\n--- Network: SEPOLIA ---")
    try:
        agent_sepolia = AgentPay(wallet, chain_name="SEPOLIA")
        print(f"✅ Connected to Sepolia (ID: {agent_sepolia.w3.eth.chain_id})")
        bal_sepolia = agent_sepolia.get_balance()
        print(f"💰 Balance: {bal_sepolia} SepoliaETH")
    except Exception as e:
        print(f"❌ Failed to connect to Sepolia: {e}")

    # 3. Connect to BASE (Example)
    print("\n--- Network: BASE (Mainnet) ---")
    try:
        agent_base = AgentPay(wallet, chain_name="BASE_MAINNET")
        print(f"✅ Connected to Base (ID: {agent_base.w3.eth.chain_id})")
        bal_base = agent_base.get_balance()
        print(f"💰 Balance: {bal_base} ETH")
    except Exception as e:
        print(f"❌ Failed to connect to Base: {e}")

if __name__ == "__main__":
    demo_multichain()
