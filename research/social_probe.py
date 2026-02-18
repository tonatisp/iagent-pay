from web3 import Web3
# For Solana, we might need a specific library or RPC call
try:
    from solana.rpc.api import Client
    from solders.pubkey import Pubkey
except ImportError:
    print("Skipping Solana imports")

def test_ens_resolution():
    print("--- 🔹 Testing ENS Resolution ---")
    # ENS requires Mainnet Connection usually
    url = "https://rpc.ankr.com/eth" 
    w3 = Web3(Web3.HTTPProvider(url))
    
    if not w3.is_connected():
        print("❌ Could not connect to Mainnet RPC for ENS.")
        return

    target = "vitalik.eth"
    try:
        address = w3.ens.address(target)
        print(f"✅ Resolved {target} -> {address}")
    except Exception as e:
        print(f"❌ ENS Failed: {e}")

def test_sns_resolution():
    print("\n--- ☀️ Testing SNS Resolution ---")
    # SNS resolution is trickier without a dedicated lib, usually involves querying the Name Registry program
    # For MVP, we might need to check if 'spl-name-service' is available or use raw RPC
    print("TODO: Determine best way to resolve .sol names with pure python.")

if __name__ == "__main__":
    test_ens_resolution()
    test_sns_resolution()
