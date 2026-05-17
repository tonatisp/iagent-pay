from iagent_pay.agent_pay import AgentPay
import os

def test_xrp_integration():
    print("🌊 Testing iAgentPay XRP Ledger Integration (v4.0)...")
    
    # Initialize for XRP Testnet
    agent = AgentPay(chain_name="XRP_TESTNET")
    
    # Check if we have an XRP seed
    # For initial run, we might need a faucet or existing seed
    xrp_seed = os.getenv("XRP_TESTNET_SEED")
    
    if not xrp_seed:
        print("⚠️ No XRP_TESTNET_SEED found in environment.")
        print("💡 In a real scenario, we'd use a faucet or prompt for one.")
        print("Creating an ephemeral wallet for testing...")
        from xrpl.wallet import generate_faucet_wallet
        from xrpl.clients import JsonRpcClient
        
        client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
        test_wallet = generate_faucet_wallet(client, debug=True)
        xrp_seed = test_wallet.seed
        print(f"✅ Generated Test Wallet: {test_wallet.address}")

    # Load into the agent
    agent.xrpl.load_wallet(xrp_seed)
    agent.my_address = agent.xrpl.get_address()
    
    print(f"📋 Agent XRP Address: {agent.my_address}")
    
    # Check Balance
    balance = agent.get_balance()
    print(f"💰 Agent XRP Balance: {balance} XRP")
    
    # Test internal transfer logic (Simulated recipient)
    recipient = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzgpEyc" # Random testnet address
    print(f"🚀 Attempting to send 10 XRP to {recipient}...")
    
    try:
        tx_hash = agent.pay_agent(recipient, 10.0)
        print(f"✨ Success! Tx Hash: {tx_hash}")
    except Exception as e:
        print(f"❌ Transfer Failed: {e}")

if __name__ == "__main__":
    test_xrp_integration()
