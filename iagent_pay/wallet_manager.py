import json
import os
import sqlite3
import logging
from eth_account import Account
from eth_account.signers.local import LocalAccount
from typing import Optional
from abc import ABC, abstractmethod

class KeyVaultProvider(ABC):
    """
    Abstract interface for enterprise Key Custody providers (e.g. AWS KMS, Fireblocks).
    Allows signing transactions without exposing the raw private key in memory or disk.
    """
    @abstractmethod
    def get_address(self) -> str:
        pass

    @abstractmethod
    def sign_transaction(self, tx_dict: dict) -> bytes:
        """Signs a transaction and returns the signed raw bytes."""
        pass

logger = logging.getLogger("iagentpay.wallet")

KEY_FILE_JSON = "wallet_keystore.json"

# ─────────────────────────────────────────────────────────────────────────────
# SECURITY NOTE (v4.0):
#   Private keys are NEVER stored in plain text .env files.
#   Priority order for key loading:
#     1. Encrypted Keystore (wallet_keystore.json) — RECOMMENDED
#     2. OS Environment Variable (ETH_PRIVATE_KEY) — Acceptable for CI/CD
#     3. Create new wallet if nothing exists (saves as keystore)
#   
#   Never commit .env or wallet_keystore.json to version control.
#   Add them to .gitignore immediately.
# ─────────────────────────────────────────────────────────────────────────────

class WalletSecurityError(Exception):
    """Raised when an insecure wallet operation is attempted."""
    pass


class WalletManager:
    """
    Manages the creation and loading of wallets for AI Agents.
    Hardened v4.0: Plain-text .env storage REMOVED.
    Keys are now loaded ONLY from encrypted keystores or OS env vars.
    """

    def __init__(self, provider_type: str = "LOCAL"):
        Account.enable_unaudited_hdwallet_features()
        self.provider_type = provider_type.upper()

    def get_or_create_wallet(self, password: Optional[str] = None) -> LocalAccount:
        """
        Loads the existing wallet using a secure priority chain.

        Priority:
          1. Encrypted keystore (wallet_keystore.json) — requires password
          2. OS environment variable ETH_PRIVATE_KEY — no file needed
          3. Create a NEW encrypted keystore (requires password)

        Args:
            password: Password for the encrypted keystore. REQUIRED for keystore operations.

        Returns:
            LocalAccount ready to sign transactions.
        """
        if self.provider_type != "LOCAL":
            raise NotImplementedError(f"Provider '{self.provider_type}' coming in v5.0.")

        return self._load_local_wallet(password)

    def _load_local_wallet(self, password: Optional[str] = None) -> LocalAccount:
        if not password:
            password = os.environ.get("WALLET_DECRYPTION_PASSWORD")

        # 1. Encrypted Keystore (most secure)
        if os.path.exists(KEY_FILE_JSON):
            if not password:
                raise WalletSecurityError(
                    "Encrypted keystore found but no password provided.\n"
                    "  Usage: WalletManager().get_or_create_wallet(password='YourPassword')\n"
                    "  Alternatively, set ETH_PRIVATE_KEY environment variable."
                )
            logger.info("[WalletManager] Loading from encrypted keystore...")
            try:
                with open(KEY_FILE_JSON, "r") as f:
                    encrypted_json = f.read()
                return Account.from_key(Account.decrypt(encrypted_json, password))
            except Exception as e:
                raise WalletSecurityError(f"Failed to decrypt keystore: {e}") from e

        # 2. OS Environment Variable (safe for CI/CD, no file needed)
        env_key = os.environ.get("ETH_PRIVATE_KEY", "").strip()
        if env_key:
            if env_key.startswith("0x"):
                env_key = env_key[2:]
            logger.info("[WalletManager] Loaded from OS environment variable ETH_PRIVATE_KEY.")
            return Account.from_key(env_key)

        # 3. No wallet found — create a new encrypted one
        logger.warning("[WalletManager] No wallet found. Creating a new encrypted keystore...")
        account = Account.create()

        if password:
            self.save_keystore(account, password)
            logger.info(f"[WalletManager] New wallet saved to {KEY_FILE_JSON}. Address: {account.address}")
        else:
            # Print the key ONCE to stdout so the user can store it safely
            # Do NOT write it to any file
            print("\n" + "="*60)
            print("[KEY] NEW WALLET CREATED - SECURELY CONFIGURED")
            print("="*60)
            print(f"  Address    : {account.address}")
            print(f"  Private Key: {account.key.hex()}")
            print("="*60)
            print("  [WARNING] This key will NOT be saved to disk.")
            print("  Set it as an OS environment variable (ETH_PRIVATE_KEY).")
            print("  Or re-run with a password to save an encrypted keystore.")
            print("="*60 + "\n")

        return account

    def save_keystore(self, account: LocalAccount, password: str) -> str:
        """Encrypts and saves the wallet to an AES-128 encrypted JSON keystore."""
        logger.info("[WalletManager] Encrypting wallet with AES-128...")
        encrypted = Account.encrypt(account.key, password)
        with open(KEY_FILE_JSON, "w") as f:
            json.dump(encrypted, f, indent=2)
        logger.info(f"[WalletManager] ✅ Encrypted keystore saved to {KEY_FILE_JSON}")
        return KEY_FILE_JSON

    def create_wallet(self) -> LocalAccount:
        """Generates a brand new random wallet (ephemeral, not saved)."""
        return Account.create()

    def load_wallet(self, private_key: str) -> LocalAccount:
        """Loads a wallet from a private key string (use only in secure environments)."""
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        return Account.from_key(private_key)

    def get_address(self, account: LocalAccount) -> str:
        """Returns the public address of the wallet."""
        return account.address

    def export_wallet_backup(self, account: LocalAccount, backup_filepath: str, password: str) -> None:
        """Encrypts and exports the private key to a designated backup file."""
        logger.info(f"[WalletManager] Encrypting and exporting wallet backup to {backup_filepath}...")
        encrypted = Account.encrypt(account.key, password)
        with open(backup_filepath, "w") as f:
            json.dump(encrypted, f, indent=2)
        logger.info(f"[WalletManager] ✅ Encrypted backup successfully saved to {backup_filepath}")

    def import_wallet_backup(self, backup_filepath: str, password: str, save_locally: bool = True) -> LocalAccount:
        """Decrypts a backup file and optionally sets it as the active local keystore."""
        logger.info(f"[WalletManager] Decrypting wallet backup from {backup_filepath}...")
        if not os.path.exists(backup_filepath):
            raise FileNotFoundError(f"Backup file not found: {backup_filepath}")
        
        try:
            with open(backup_filepath, "r") as f:
                encrypted_json = f.read()
            decrypted_key = Account.decrypt(encrypted_json, password)
            account = Account.from_key(decrypted_key)
        except Exception as e:
            raise WalletSecurityError(f"Failed to decrypt backup keystore: {e}") from e

        if save_locally:
            self.save_keystore(account, password)
            logger.info(f"[WalletManager] ✅ Restored wallet saved locally as active keystore {KEY_FILE_JSON}")
        
        return account

    @staticmethod
    def check_gitignore():
        """Warns if sensitive files are not in .gitignore."""
        gitignore_path = ".gitignore"
        dangerous_files = ["wallet_keystore.json", ".env", "*.key"]
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                content = f.read()
            missing = [f for f in dangerous_files if f not in content]
            if missing:
                logger.warning(
                    f"[WalletManager] ⚠️ These files should be in .gitignore: {missing}"
                )
        else:
            logger.warning("[WalletManager] ⚠️ No .gitignore found. Create one and add wallet_keystore.json and .env")


if __name__ == "__main__":
    wm = WalletManager()
    wm.check_gitignore()
    try:
        wallet = wm.get_or_create_wallet()
        print(f"Agent Address: {wallet.address}")
    except Exception as e:
        print(f"Error: {e}")
