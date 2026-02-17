# Security Upgrade: Encrypted Keystore Implementation

## Goal
Replace the insecure storage of private keys (plain text in `.env`) with industry-standard Encrypted JSON Keystore files (EIP-2335).

## Changes
1.  **Modify `WalletManager`**:
    *   Add `load_keystore(password)` method.
    *   Add `create_keystore(password)` method.
    *   Deprecate (but support for migration) `.env` loading.
2.  **Create Migration Script**:
    *   Read existing key from `.env`.
    *   Ask user for a password.
    *   Encrypt key and save to `wallet_keystore.json`.
    *   Delete key from `.env` (optional/prompted).

## Dependencies
*   `eth-keyfile` (or `eth-account` built-in features). `eth-account` has `Account.encrypt` and `Account.decrypt`.

## Verification
*   Run migration script.
*   Verify `wallet_key.json` exists and contains encrypted data (no plain key).
*   Run `testnet_demo.py` prompting for password instead of auto-loading.
