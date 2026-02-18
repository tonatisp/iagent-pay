import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from iagent_pay.solana_driver import SolanaDriver
try:
    print("Initializing Driver...")
    driver = SolanaDriver(network="devnet")
    print(f"USDC Mint: '{driver.usdc_mint}'")
    
    print("Fetching Token Balance...")
    bal = driver.get_token_balance()
    print(f"Balance: {bal}")
except Exception as e:
    print(f"❌ Fatal Error: {e}")
