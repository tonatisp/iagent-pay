import time
from iagent_pay import WalletManager
from iagent_pay import AgentPay

def check_status():
    print("🔍 Checking Wallet Status on Sepolia...")
    # Using 1rpc.io as it seemed to connect
    SEPOLIA_RPC = "https://1rpc.io/sepolia"
    
    wm = WalletManager()
    wallet = wm.get_or_create_wallet()
    print(f"🔑 Wallet: {wallet.address}")

    try:
        agent = AgentPay(wallet, provider_url=SEPOLIA_RPC)
        if agent.w3.is_connected():
            print(f"✅ Connected to Sepolia (Block: {agent.w3.eth.block_number})")
            
            # Check Confirmed Balance
            balance = agent.get_balance()
            print(f"💰 Confirmed Balance: {balance} ETH")
            
            # Check Pending Balance (might be higher if tx is incoming)
            pending_balance_wei = agent.w3.eth.get_balance(wallet.address, 'pending')
            pending_balance = agent.w3.from_wei(pending_balance_wei, 'ether')
            print(f"⏳ Pending Balance:   {pending_balance} ETH")
            
            # Check Nonce (Transaction Count)
            nonce = agent.w3.eth.get_transaction_count(wallet.address)
            pending_nonce = agent.w3.eth.get_transaction_count(wallet.address, 'pending')
            print(f"🔢 Confirmed Nonce: {nonce}")
            print(f"🔢 Pending Nonce:   {pending_nonce}")
            
            if pending_nonce > nonce:
                print("\n⚠️  WARNING: There are pending transactions stuck in the mempool!")
                print("   This explains the 'replacement transaction underpriced' error.")
                print("   We just need to wait for them to confirm.")
            
            if balance > 0:
                print("\n🎉 FUNDS DETECTED! Use 'python testnet_demo.py' to spend them.")
            else:
                print("\n❌ Still waiting for funds to arrive.")
                
        else:
            print("❌ Start Failed: formatting error")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_status()
