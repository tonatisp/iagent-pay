import time
import os
from iagent_pay import WalletManager, AgentPay

def connect_to_testnet():
    print("🌍 Connecting to Sepolia Testnet (Real Blockchain)...")
    
    # Public RPC Endpoint for Sepolia (Free to use)
    SEPOLIA_RPC = "https://1rpc.io/sepolia"
    
    wm = WalletManager()
    
    # ---------------------------------------------------------
    # IMPORTANT: Use the persisted wallet so the address stays the same!
    # ---------------------------------------------------------
    wallet = wm.get_or_create_wallet()
    
    print(f"🔑 Using Wallet Address: {wallet.address}")
    
    try:
        # Initialize AgentPay
        agent = AgentPay(wallet, provider_url=SEPOLIA_RPC)
        
        if agent.w3.is_connected():
            latest_block = agent.w3.eth.block_number
            print(f"✅ SUCCESS: Connected to Sepolia! (Block: {latest_block})")
            
            # Check Balance
            balance = agent.get_balance()
            print(f"💰 Current Balance: {balance} SepoliaETH")
            
            if balance > 0:
                print("\n🚀 Wallet FUNDED! Attempting Transaction...")
                # Create a random recipient to pay (Simulating another agent)
                recipient = wm.create_wallet().address
                amount_to_send = 0.0001
                
                print(f"   Sending {amount_to_send} ETH to {recipient}...")
                tx_hash = agent.pay_agent(recipient, amount_to_send)
                print(f"✅ Transaction Sent! Hash: {tx_hash}")
                print(f"🔗 View on Etherscan: https://sepolia.etherscan.io/tx/{tx_hash}")
            else:
                print("\n⚠️  Balance is 0.")
                print("   Please send Sepolia ETH to this PERSISTENT address:")
                print(f"   👉 {wallet.address}")
                print("   (This address is now saved in .env, so it won't change!)")
            
        else:
            print("❌ ERROR: Could not connect to Sepolia.")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    connect_to_testnet()
