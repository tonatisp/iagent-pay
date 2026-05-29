import os
import sys
import getpass
from iagent_pay import WalletManager

def migrate():
    print("🔒 AgentPay Security Migration Tool")
    print("===================================")
    
    if os.path.exists("wallet_keystore.json"):
        print("✅ Secure Keystore already exists. No action needed.")
        return

    wm = WalletManager()
    
    # This loads from .env automatically
    try:
        wallet = wm.get_or_create_wallet()
    except Exception as e:
        print(f"❌ Could not load existing wallet: {e}")
        return

    print(f"🔑 Found Wallet Address: {wallet.address}")
    print("\nWe will now encrypt this private key with a password.")
    
    if os.environ.get("WALLET_DECRYPTION_PASSWORD"):
        password = os.environ.get("WALLET_DECRYPTION_PASSWORD")
        print("🔑 Loaded encryption password from WALLET_DECRYPTION_PASSWORD environment variable.")
    elif len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass(prompt="Enter a strong password: ")
        confirm = getpass.getpass(prompt="Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords do not match!")
            return
            
    if not password:
        print("❌ Password cannot be empty.")
        return

    print("\n🔄 Encrypting... (This may take a few seconds)")
    try:
        wm.save_keystore(wallet, password)
        print("\n✅ SUCCESS! Wallet encrypted and saved to 'wallet_keystore.json'")
        print("⚠️  IMPORTANT: You should now delete the '.env' file to remove the unencrypted key.")
        
        # Verify
        print("\n🔍 Verifying decryption...")
        wm.get_or_create_wallet(password=password)
        print("✅ Decryption successful.")
        
    except Exception as e:
        print(f"❌ Encryption failed: {e}")

if __name__ == "__main__":
    migrate()
