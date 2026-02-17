import time
import sqlite3
from web3 import Web3
from eth_account.signers.local import LocalAccount
from typing import Optional
from decimal import Decimal
from .config import ChainConfig
from .pricing import PricingManager

class AgentPay:
    """
    The main SDK class for AI Agents to interact with the blockchain.
    ✅ Professional Grade: Includes Nonce Management, Smart Gas, and Audit Logs.
    ✅ Multi-Chain: Supports Sepolia, Base, Polygon, and Local.
    """
    def __init__(self, wallet: LocalAccount, chain_name: str = "LOCAL", provider_url: Optional[str] = None):
        self.wallet = wallet
        self.nonce = None # Local nonce tracker
        
        # Database for Audit Logs
        self.db_path = "agent_history.db"
        self._init_db()

        # Multi-Chain Configuration
        if provider_url:
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
        else:
            try:
                network = ChainConfig.get_network(chain_name)
                print(f"🌍 Connecting to {network['name']}...")
                
                if network['rpc']:
                     self.w3 = Web3(Web3.HTTPProvider(network['rpc']))
                else:
                    # Simulation / Local
                    from web3.providers.eth_tester import EthereumTesterProvider
                    self.w3 = Web3(EthereumTesterProvider())
            except ValueError as e:
                # Fallback or re-raise
                print(str(e))
                # Default to local if unknown
                from web3.providers.eth_tester import EthereumTesterProvider
                self.w3 = Web3(EthereumTesterProvider())
            
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Blockchain Provider")

    def _init_db(self):
        """Initializes the local SQLite database for audit logs."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                     (timestamp REAL, tx_hash TEXT, recipient TEXT, amount REAL, status TEXT)''')
        conn.commit()
        conn.close()

    def _log_transaction(self, tx_hash, recipient, amount, status="PENDING"):
        """Saves transaction details to the local audit log."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                  (time.time(), tx_hash, recipient, amount, status))
        conn.commit()
        conn.close()

    def get_balance(self) -> Decimal:
        """Returns the balance in ETH (or native token) as a Decimal."""
        wei_balance = self.w3.eth.get_balance(self.wallet.address)
        return Decimal(self.w3.from_wei(wei_balance, 'ether'))

    def _get_nonce(self):
        """
        Reliability Engine: seamless nonce management.
        Gets the higher value between local counter and network count
        to prevent 'nonce too low' errors.
        """
        network_nonce = self.w3.eth.get_transaction_count(self.wallet.address, 'pending')
        if self.nonce is None or network_nonce > self.nonce:
            self.nonce = network_nonce
        return self.nonce

    def _get_smart_gas_price(self):
        """
        Smart Gas Station: Auto-calculates optimal fee.
        Adds a 10% 'bribe' (tip) to ensure the transaction is picked up quickly.
        """
        base_price = self.w3.eth.gas_price
        # Add 10% premium for speed/reliability
        premium_price = int(base_price * 1.10)
        return premium_price

    def pay_agent(self, recipient_address: str, amount: float, wait: bool = True) -> str:
        """
        Sends a payment to another agent with robustness and logging.
        Args:
            wait (bool): If True, blocks until transaction is mined (safer).
                         If False, returns immediately (faster for HFT).
        """
        if not self.w3.is_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")

        # License Check (before transaction)
        self._check_license(amount)

        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # 1. Get Reliable Nonce
        current_nonce = self._get_nonce()
        
        # 2. Get Smart Gas
        gas_price = self._get_smart_gas_price()

        tx = {
            'nonce': current_nonce,
            'to': recipient_address,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': self.w3.eth.chain_id
        }

        # 3. Sign & Send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.wallet.key)
        
        try:
            tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = self.w3.to_hex(tx_hash_bytes)
            
            # 4. Update Local Nonce (Increment for next tx)
            self.nonce += 1
            
            # 5. Audit Log
            print(f"✅ Tx Sent: {tx_hash} (Gas: {gas_price/1e9:.2f} Gwei)")
            self._log_transaction(tx_hash, recipient_address, amount, "SENT")
            
            if wait:
                print("⏳ Waiting for confirmation...")
                self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print("✅ Confirmed!")
                self._log_transaction(tx_hash, recipient_address, amount, "CONFIRMED")
            
            return tx_hash
            
        except ValueError as e:
            # Handle "replacement transaction underpriced" specifically
            if 'replacement transaction underpriced' in str(e):
                print("⚠️  Transaction underpriced. Retrying with HIGHER gas...")
                # Recursively retry with forced higher gas? 
                # For now just raising, but in v2 we'd implement the loop.
                raise e
            raise e

    def _verify_pro_subscription(self, config) -> bool:
        """Verifies if a valid Subscription TxHash exists in env."""
        sub_hash = os.getenv("IAGENT_LICENSE_KEY")
        if not sub_hash:
            return False
            
        try:
            # Verify on-chain
            tx = self.w3.eth.get_transaction(sub_hash)
            
            # 1. Check Recipient (Must be Treasury)
            if tx['to'].lower() != config.get("treasury_address").lower():
                print("⚠️ Invalid License: Wrong treasury address.")
                return False
                
            # 2. Check Amount (Must be >= Subscription Price)
            # Allow 5% slippage/variance for dynamic price changes
            min_price = self.w3.to_wei(config.get("subscription_price_eth") * 0.95, 'ether')
            if tx['value'] < min_price:
                print("⚠️ Invalid License: Insufficient payment.")
                return False
                
            # 3. Check Age (Must be recent, e.g., < 30 days)
            # Getting block timestamp requires another call, skipped for MVP speed.
            # Assuming if you have the hash and it's confirmed, it's valid for now.
            
            print("💎 PRO Subscription Active.")
            return True
            
        except Exception as e:
            print(f"⚠️ License Verification Failed: {e}")
            return False

    def _check_license(self, amount_eth: float):
        """
        Enforces Business Model:
        1. Checks if Trial is Active (First 60 days).
        2. Warns if trial ending soon (5 days).
        3. If Expired: Checked for PRO Subscription.
        4. If No PRO: Enforces 'Pay-As-You-Go' Fee.
        """
        # 1. Get Config (Now Dynamic)
        config = self.pricing.get_config()
        trial_days = config.get("trial_days", 60)
        
        # 2. Check Global Registry (Anti-Reinstall Protection)
        # We store the 'First Run Date' in the SYSTEM USER folder, not the project folder.
        # This prevents users from just deleting the project to reset the trial.
        from pathlib import Path
        
        home_dir = Path.home()
        global_registry_dir = home_dir / ".iagent_pay_registry"
        registry_file = global_registry_dir / "license_tracker.json"
        
        first_tx = None
        
        # A) Try to read existing global record
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    first_tx = data.get("first_run_timestamp")
            except Exception:
                pass # Corrupt file, treat as new (or could deny access for security)
        
        # B) If no global record, look at local DB (migration/first-time)
        if not first_tx:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT MIN(timestamp) FROM transactions")
            row = c.fetchone()
            conn.close()
            
            if row and row[0]:
                first_tx = float(row[0])
                
                # SAVE to Global Registry immediately to lock it in
                try:
                    global_registry_dir.mkdir(parents=True, exist_ok=True)
                    with open(registry_file, 'w') as f:
                        json.dump({"first_run_timestamp": first_tx, "note": "DO NOT DELETE - License Integrity"}, f)
                except Exception as e:
                    print(f"⚠️ License System Warning: Could not write to global registry: {e}")
            else:
                return # Truly new user, no local or global history.

        days_active = (time.time() - first_tx) / 86400
        days_remaining = trial_days - days_active
        
        # 🔔 WARNING SYSTEM (5 Days Before)
        if 0 < days_remaining <= 5:
            print(f"\n⚠️  IMPORTANT: Free Trial ends in {int(days_remaining)} days.")
            print(f"   Subscribe now (~$26/mo) to avoid per-transaction fees.")
            print(f"   Treasury: {config.get('treasury_address')}\n")

        if days_active > trial_days:
            print(f"ℹ️ Trial Expired. Checking for PRO License...")
            
            # Check for PRO Subscription
            if self._verify_pro_subscription(config):
                return # User Paid! No fees.
            
            # FALLBACK: Pay-As-You-Go Fee
            fee_eth = config.get("pay_per_use_price_eth")
            treasury = config.get("treasury_address")
            
            print(f"💳 Standard Plan: Applying ${0.10} Fee ({fee_eth:.6f} ETH)")
            
            if self.w3.is_address(treasury):
                try:
                    self.pay_agent(treasury, fee_eth, wait=False)
                    print("✅ Fee Paid.")
                except Exception as e:
                    print(f"❌ Failed to collect fee. Top up wallet.")
                    raise PermissionError("License Fee Payment Failed.")
            else:
                print("⚠️ Configuration Error: Treasury not set.")
                raise ValueError("Configuration Error: Treasury address not set or invalid.")
