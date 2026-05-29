from iagent_pay.agent_pay import AgentPay
import os
from unittest.mock import MagicMock

def test_xrp_integration():
    print("🌊 Testing iAgentPay XRP Ledger Integration (v4.0)...")
    
    # Initialize for XRP Testnet
    agent = AgentPay(chain_name="XRP_TESTNET")
    
    # Adjust safety config limits to avoid capping test payments
    agent.safety_config.max_tx_usd = 1000000.0
    agent.safety_config.session_limit_usd = 1000000.0
    agent.safety_config.daily_limit_usd = 1000000.0
    agent.safety_config.weekly_limit_usd = 1000000.0
    agent.safety_config.human_approval_threshold_usd = 1000000.0
    
    # Mock XRPLDriver methods to run completely offline
    agent.xrpl.load_wallet = MagicMock(return_value="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzgpEyc")
    agent.xrpl.get_address = MagicMock(return_value="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzgpEyc")
    agent.xrpl.get_balance = MagicMock(return_value=100.0)
    agent.xrpl.transfer = MagicMock(return_value="ABC123MOCKHASH")
    
    # Load into the agent
    agent.xrpl.load_wallet("mock_seed")
    agent.my_address = agent.xrpl.get_address()
    
    assert agent.my_address == "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzgpEyc"
    print(f"📋 Agent XRP Address: {agent.my_address}")
    
    # Check Balance
    balance = agent.get_balance()
    assert balance == 100.0
    print(f"💰 Agent XRP Balance: {balance} XRP")
    
    # Test internal transfer logic (Simulated recipient)
    recipient = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzgpEyc"
    print(f"🚀 Attempting to send 10 XRP to {recipient}...")
    
    tx_hash = agent.pay_agent(recipient, 10.0)
    assert tx_hash == "ABC123MOCKHASH"
    print(f"✨ Success! Tx Hash: {tx_hash}")

if __name__ == "__main__":
    test_xrp_integration()

