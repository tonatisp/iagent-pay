import json
import os
from eth_account import Account
from eth_account.signers.local import LocalAccount
from typing import Optional

# File to store the private key locally (Simulating a secure vault)
KEY_FILE_ENV = ".env"
KEY_FILE_JSON = "wallet_key.json"

class WalletManager:
    """
    Manages the creation and loading of wallets for AI Agents.
    Supports both legacy .env (text) and secure Keystore (JSON).
    """
    def __init__(self):
        # Enable unaudited HD wallet features for MVP ease of use
        Account.enable_unaudited_hdwallet_features()

    def get_or_create_wallet(self, password: Optional[str] = None) -> LocalAccount:
        """
        Loads the existing wallet.
        Prioritizes Encrypted Keystore if password is provided.
        Falls back to .env for legacy support.
        Creates new if nothing exists.
        """
        # 1. Try to load from Strong Keystore (JSON)
        if password and os.path.exists(KEY_FILE_JSON):
            print("🔐 Loading from Secure Keystore...")
            try:
                with open(KEY_FILE_JSON, "r") as f:
                    encrypted_json = f.read()
                    return Account.from_key(Account.decrypt(encrypted_json, password))
            except Exception as e:
                print(f"❌ Failed to decrypt keystore: {e}")
                # Don't fallback to .env if password was provided but failed, that's a security risk
                raise e

        # 2. Try to load from Weak File (.env)
        if os.path.exists(KEY_FILE_ENV):
            with open(KEY_FILE_ENV, "r") as f:
                content = f.read().strip()
                if content.startswith("TESTNET_PRIVATE_KEY="):
                    private_key = content.split("=")[1]
                    # print("⚠️  Loaded from INSECURE .env file. Consider migrating to Keystore.")
                    return Account.from_key(private_key)
        
        # 3. Create new if not exists
        print("⚠️  No existing wallet found. creating NEW one...")
        account = Account.create()
        
        # If password provided, save as Encrypted Keystore
        if password:
            self.save_keystore(account, password)
        else:
            # Fallback to .env
            self.save_to_env(account)
            
        return account

    def save_keystore(self, account: LocalAccount, password: str):
        """Encrypts and saves the wallet to a JSON file."""
        print("🔒 Encrypting wallet...")
        encrypted = Account.encrypt(account.key, password)
        with open(KEY_FILE_JSON, "w") as f:
            json.dump(encrypted, f)
        print(f"✅ Saved Encrypted Keystore to {KEY_FILE_JSON}")

    def save_to_env(self, account: LocalAccount):
        """Saves raw key to .env (Legacy/Insecure)."""
        with open(KEY_FILE_ENV, "w") as f:
            f.write(f"TESTNET_PRIVATE_KEY={account.key.hex()}")
        print(f"⚠️  Saved raw private key to {KEY_FILE_ENV}")

    def create_wallet(self) -> LocalAccount:
        """Generates a brand new random wallet (Ephemeral)."""
        account = Account.create()
        return account

    def load_wallet(self, private_key: str) -> LocalAccount:
        """Loads a wallet from a private key string."""
        account = Account.from_key(private_key)
        return account

    def get_address(self, account: LocalAccount) -> str:
        """Returns the public address of the wallet."""
        return account.address

if __name__ == "__main__":
    wm = WalletManager()
    # Test legacy load
    try:
        wallet = wm.get_or_create_wallet()
        print(f"Managed Wallet Address: {wallet.address}")
    except Exception as e:
        print(f"Error loading wallet: {e}")
