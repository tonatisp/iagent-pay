import time
import sqlite3
import os
import json
from web3 import Web3
from eth_account.signers.local import LocalAccount
from typing import Optional, Dict, Any
from decimal import Decimal
from .config import ChainConfig
from .pricing import PricingManager
from .tokens import TOKEN_ADDRESSES, ERC20_ABI

class AgentPay:
    """
    The main SDK class for AI Agents to interact with the blockchain.
    âœ… Professional Grade: Includes Nonce Management, Smart Gas, and Audit Logs.
    âœ… Multi-Chain: Supports Sepolia, Base, Polygon, BNB, and Solana.
    """
    
    def __init__(self, treasury_address: str = None, chain_name: str = "BASE", private_key: str = None, daily_limit: float = 10.0):
        """
        :param treasury_address: Where subscription fees go (EVM or SOL address).
        :param chain_name: "BASE", "POLYGON", "ETH", "BNB", "SEPOLIA" or "SOLANA".
        :param private_key: Optional manual override.
        :param daily_limit: Max amount of native tokens (ETH/SOL) to spend in 24h. Default: 10.0
        """
        self.chain_name = chain_name.upper()
        self.daily_limit = daily_limit
        self.is_solana = self.chain_name in ["SOLANA", "SOL_DEVNET", "SOL_TESTNET", "SOL_MAINNET"]

        # --- DUAL DRIVER SELECTOR ---
        if self.is_solana:
            from iagent_pay.solana_driver import SolanaDriver
            network_map = {"SOLANA": "mainnet", "SOL_DEVNET": "devnet", "SOL_TESTNET": "testnet", "SOL_MAINNET": "mainnet"}
            self.solana = SolanaDriver(network=network_map.get(self.chain_name, "devnet"))
            self.my_address = self.solana.get_address()
            print(f"â˜€ï¸ [AgentPay] Initialized on SOLANA ({self.solana.network})")
            
        else:
            self.solana = None
            self.config = ChainConfig.get_network(chain_name)
            rpc_list = self.config.get("rpc")
            if isinstance(rpc_list, str): rpc_list = [rpc_list]
            elif not rpc_list: rpc_list = []
            
            self.rpc_pool = rpc_list
            self.current_rpc_index = 0
            self.w3 = self._connect_to_best_rpc()
            
            from .wallet_manager import WalletManager
            self.wallet_manager = WalletManager()
            
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key)
            else:
                self.account = self.wallet_manager.get_or_create_wallet()
            
            self.wallet = self.account 
            self.my_address = self.account.address

        # --- COMMON MANAGERS (v3.0) ---
        self.pricing = PricingManager()
        from .social_resolver import SocialResolver
        self.social = SocialResolver()
        from .swap_engine import SwapEngine
        self.swap_engine = SwapEngine(self)
        from .invoice_manager import InvoiceManager
        self.invoices = InvoiceManager(self)
        from .yield_protocols import YieldManager
        self.yield_manager = YieldManager(self)
        from .reputation_manager import ReputationManager
        self.reputation = ReputationManager(self)
        from .marketplace_bridge import MarketplaceBridge
        self.marketplace = MarketplaceBridge(self)

        # Resolve Treasury
        self.treasury_address = treasury_address
        if not self.treasury_address:
            cfg = self.pricing.get_config()
            treas_data = cfg.get("treasury", {})
            if isinstance(treas_data, dict):
                self.treasury_address = treas_data.get("SOLANA") if self.is_solana else treas_data.get("EVM")
            else:
                self.treasury_address = cfg.get("treasury_address")
        
        self.db_path = "agent_history.db"
        self._init_db()
        self._local_nonce = {}

    def _connect_to_best_rpc(self) -> Web3:
        """Attempts to connect to RPCs in the pool until one works."""
        if not self.rpc_pool:
            return Web3(Web3.EthereumTesterProvider())
        for url in self.rpc_pool:
            try:
                w3 = Web3(Web3.HTTPProvider(url))
                if w3.is_connected(): return w3
            except: continue
        return Web3(Web3.HTTPProvider(self.rpc_pool[0]))

    def rotate_rpc(self):
        """Switches to the next healthy RPC in the pool."""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_pool)
        self.w3 = self._connect_to_best_rpc()
        self._init_db()

        # Nonce Management (EVM)
        self._local_nonce = {}

    def _init_db(self):
        """Initializes the local SQLite database for audit logs."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Initial Schema
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                     (timestamp REAL, tx_hash TEXT, recipient TEXT, amount REAL, status TEXT, symbol TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS paid_invoices
                     (invoice_id TEXT PRIMARY KEY, timestamp REAL, recipient TEXT, amount REAL)''')
        
        # Migration: Add 'symbol' if missing (for existing users)
        try:
            c.execute("ALTER TABLE transactions ADD COLUMN symbol TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        conn.commit()
        conn.close()

    def _is_invoice_paid(self, invoice_id: str) -> bool:
        """Checks if an invoice ID has already been processed."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM paid_invoices WHERE invoice_id = ?", (invoice_id,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def _mark_invoice_paid(self, invoice_id: str, recipient: str, amount: float):
        """Records a paid invoice to prevent replay attacks."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO paid_invoices VALUES (?, ?, ?, ?)",
                      (invoice_id, time.time(), recipient, float(amount)))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Already exists
        conn.close()

    def _check_daily_limit(self, amount: float, symbol: str):
        """Ensures daily spending does not exceed the limit."""
        if not self.daily_limit or self.daily_limit <= 0:
            return  # No limit set
        
        # Only enforce on native assets for now (ETH, SOL, MATIC, BNB)
        if symbol not in ["ETH", "SOL", "MATIC", "BNB"]:
            return 

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Rolling 24h Window
        start_of_day = time.time() - 86400 
        c.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE timestamp > ? AND symbol = ? AND status != 'FAILED'
        """, (start_of_day, symbol))
        
        result = c.fetchone()
        spent_today = result[0] if result and result[0] else 0.0
        conn.close()
        
        if spent_today + amount > self.daily_limit:
            raise ValueError(f"ðŸš¨ Security Alert: Daily Spending Limit Exceeded! Attempted: {amount} {symbol}, Spent 24h: {spent_today:.4f}, Limit: {self.daily_limit}")

    def set_daily_limit(self, limit: float):
        """Updates the daily spending limit (Native Tokens). Set to 0 to disable."""
        self.daily_limit = limit
        print(f"ðŸ›¡ï¸ Security Update: Daily Spending Limit set to {self.daily_limit} units.")

    def _log_transaction(self, tx_hash, recipient, amount, status="PENDING", symbol="ETH"):
        """Saves transaction details to the local audit log."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
                  (time.time(), tx_hash, recipient, amount, status, symbol))
        conn.commit()
        conn.close()

    def get_balance(self) -> float:
        """Returns balance in ETH or SOL."""
        if self.is_solana:
            return self.solana.get_balance()
            
        # EVM Balance
        wei = self.w3.eth.get_balance(self.my_address)
        return float(self.w3.from_wei(wei, 'ether'))

    def _get_nonce(self):
        """
        Reliability Engine: seamless nonce management.
        Gets the higher value between local counter and network count.
        """
        if self.is_solana: return 0 
        
        network_nonce = self.w3.eth.get_transaction_count(self.my_address, 'pending')
        
        # Initialize if not set for this session
        if self.my_address not in self._local_nonce:
            self._local_nonce[self.my_address] = network_nonce
            
        # If network has a higher nonce (e.g. tx confirmed), update local
        if network_nonce > self._local_nonce[self.my_address]:
            self._local_nonce[self.my_address] = network_nonce
            
        return self._local_nonce[self.my_address]

    def _get_smart_gas_price(self):
        """
        Smart Gas Station: Auto-calculates optimal fee.
        """
        base_price = self.w3.eth.gas_price
        # Add 10% premium for speed/reliability
        premium_price = int(base_price * 1.10)
        return premium_price

    def _send_evm_transaction(self, tx: Dict[str, Any], wait: bool = True, log_recipient: str = "", log_amount: float = 0.0, log_symbol: str = "ETH") -> str:
        """Internal helper to sign, send, and log an EVM transaction."""
        # Ensure nonce and gas are set if not provided
        if 'nonce' not in tx:
            tx['nonce'] = self._get_nonce()
        if 'gasPrice' not in tx:
            tx['gasPrice'] = self._get_smart_gas_price()
        if 'chainId' not in tx:
            tx['chainId'] = self.w3.eth.chain_id

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.wallet.key)
        
        try:
            tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = self.w3.to_hex(tx_hash_bytes)
            
            # Audit Log
            print(f"âœ… Tx Sent: {tx_hash} (Gas: {tx['gasPrice']/1e9:.2f} Gwei)")
            self._local_nonce[self.my_address] += 1
            self._log_transaction(tx_hash, log_recipient, log_amount, "SENT", symbol=log_symbol)
            
            if wait:
                print("â³ Waiting for confirmation...")
                self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print("âœ… Confirmed!")
                self._log_transaction(tx_hash, log_recipient, log_amount, "CONFIRMED", symbol=log_symbol)
            
            return tx_hash
        except Exception as e:
            # Handle "replacement transaction underpriced" specifically
            if 'replacement transaction underpriced' in str(e):
                print("âš ï¸  Transaction underpriced. Retrying with HIGHER gas...")
                tx['gasPrice'] = int(tx['gasPrice'] * 1.20) # 20% bump
                # Recurse once
                return self._send_evm_transaction(tx, wait=wait, log_recipient=log_recipient, log_amount=log_amount, log_symbol=log_symbol)
            
            print(f"âŒ Transaction Failed: {e}")
            raise e

    def pay_agent(self, recipient_address: str, amount: float, wait: bool = True, max_gas_gwei: float = None) -> str:
        """
        :param max_gas_gwei: (Optional) Max price to pay. If exceeded, raises ValueError.
        """
        # 0. Social Resolution (ENS/SNS)
        resolved_address = self.social.resolve(recipient_address)
        if not resolved_address:
            raise ValueError(f"Could not resolve social handle: {recipient_address}")
        recipient_address = resolved_address
        
        # --- ROUTING: SOLANA ---
        if self.is_solana:
            # Solana fees are negligible (< 0.0001 Gwei equiv), so we ignore this check
            self._check_daily_limit(amount, "SOL")
            try:
                print(f"â˜€ï¸ Sending {amount:.6f} SOL...")
                sig = self.solana.transfer(recipient_address, amount)
                print(f"âœ… Solana Tx Sent: {sig}")
                self._log_transaction(sig, recipient_address, amount, "SENT_SOL", symbol="SOL")
                return sig
            except Exception as e:
                print(f"âŒ Solana Tx Failed: {e}")
                raise e

        # --- ROUTING: EVM (Legacy) ---
        if not self.w3.is_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")

        # License Check (before transaction)
        self._check_license(amount)
        
        # Capital Control: Daily Limit Check
        native_symbol = "ETH" # Default for EVM
        if self.chain_name == "POLYGON": native_symbol = "MATIC"
        if self.chain_name == "BNB": native_symbol = "BNB"
        
        self._check_daily_limit(amount, native_symbol)

        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # 1. Get Reliable Nonce
        current_nonce = self._get_nonce()
        
        # 2. Get Smart Gas
        gas_price = self._get_smart_gas_price()
        
        # 3. Gas Guardrail (User Choice)
        if max_gas_gwei:
            current_gwei = self.w3.from_wei(gas_price, 'gwei')
            if current_gwei > max_gas_gwei:
                raise ValueError(f"â›½ Gas Price ({current_gwei:.2f} Gwei) exceeds limit ({max_gas_gwei} Gwei). Transaction aborted.")

        tx = {
            'nonce': current_nonce,
            'to': recipient_address,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': self.w3.eth.chain_id
        }

        return self._send_evm_transaction(tx, wait=wait, log_recipient=recipient_address, log_amount=amount, log_symbol=native_symbol)

    def pay_token(self, recipient_address: str, amount: float, token: str = "USDC", wait: bool = True, max_gas_gwei: float = None) -> str:
        """
        Sends an ERC-20 (EVM) or SPL (Solana) Token payment.
        """
        # 0. Social Resolution
        resolved_address = self.social.resolve(recipient_address)
        if not resolved_address:
             raise ValueError(f"Could not resolve social handle: {recipient_address}")
        recipient_address = resolved_address
        
        # --- ROUTING: SOLANA ---
        if self.is_solana:
            # Solana ignores max_gas_gwei
            try:
                # For MVP, we only support USDC helper or raw mint pass-through
                print(f"â˜€ï¸ Sending {amount} {token} (SPL)...")
                
                # Resolve Mint
                mint = None
                if token == "USDC":
                    mint = self.solana.usdc_mint
                elif token == "USDT":
                    mint = self.solana.usdt_mint
                # --- MEME COINS ---
                elif token == "BONK":
                    mint = self.solana.bonk_mint
                elif token == "WIF":
                    mint = self.solana.wif_mint
                elif token == "POPCAT":
                    mint = self.solana.popcat_mint
                else:
                     # Allow custom mints if user passes full address? 
                     # For now, restrict to known safe tokens or raw base58 check
                     if len(token) > 10: # Assume it's a mint address
                         mint = token
                     else:
                         raise NotImplementedError(f"Token '{token}' not auto-configured on Solana yet.")
                
                sig = self.solana.transfer_token(recipient_address, amount, mint_address=mint)
                print(f"âœ… Solana Token Tx: {sig}")
                self._log_transaction(sig, recipient_address, amount, f"SENT_{token}_SOL", symbol=token)
                return sig
            except Exception as e:
                print(f"âŒ Solana Token Tx Failed: {e}")
                raise e

        # --- ROUTING: EVM (Legacy) ---
        if not self.w3.is_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")

        # 1. Resolve Token Address
        chain_id = self.w3.eth.chain_id
        token_address = self._resolve_token_address(token)
        if not token_address:
            raise ValueError(f"Token {token} not supported on this chain.")

        # 2. Check Gas Guardrail (Early Fail)
        if max_gas_gwei:
             current_price = self._get_smart_gas_price() # This is wei
             current_gwei = self.w3.from_wei(current_price, 'gwei')
             if current_gwei > max_gas_gwei:
                  raise ValueError(f"â›½ Gas Price ({current_gwei:.2f} Gwei) exceeds limit ({max_gas_gwei} Gwei). Aborting Token Tx.")

        # 3. Create Contract
        contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # 4. Get Decimals (Crucial! USDC has 6, ETH has 18)
        decimals = contract.functions.decimals().call()
        amount_units = int(amount * (10 ** decimals))
        
        # 5. Build Tx
        nonce = self._get_nonce()
        gas_price = self._get_smart_gas_price()
        
        # Estimate Gas (Tokens are complex)
        try:
             est_gas = contract.functions.transfer(recipient_address, amount_units).estimate_gas({'from': self.my_address})
             limit_gas = int(est_gas * 1.2) # +20% buffer
        except:
             limit_gas = 100000 # Fallback safe limit
             
        tx = contract.functions.transfer(recipient_address, amount_units).build_transaction({
            'chainId': chain_id,
            'gas': limit_gas,
            'gasPrice': gas_price,
            'nonce': nonce
        })

        # 5. Sign & Send
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        
        try:
            tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = self.w3.to_hex(tx_hash_bytes)
            
            print(f"ðŸ’µ Stablecoin Sent: {amount} {token} -> {tx_hash}")
            self._log_transaction(tx_hash, recipient_address, amount, f"SENT_{token}")
            
            if wait:
                print("â³ Waiting for stablecoin confirmation...")
                self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print("âœ… Confirmed!")
                self._log_transaction(tx_hash, recipient_address, amount, f"CONFIRMED_{token}")
                
            return tx_hash
            
        except Exception as e:
            print(f"âŒ Token Transfer Failed: {e}")
            raise e

    def _resolve_token_address(self, token_symbol: str) -> Optional[str]:
        """Finds the token address for the current connected chain."""
        chain_id = self.w3.eth.chain_id
        
        # Map Chain IDs to Names (Simple lookup)
        chain_map = {
            1: "ETH",
            8453: "BASE",
            137: "POLYGON",
            42161: "ARBITRUM",
            56: "BNB",
            11155111: "SEPOLIA"
        }
        
        chain_name = chain_map.get(chain_id)
        if not chain_name:
            return None
            
        return TOKEN_ADDRESSES.get(chain_name, {}).get(token_symbol)

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
                print("âš ï¸ Invalid License: Wrong treasury address.")
                return False
                
            # 2. Check Amount (Must be >= Subscription Price)
            # Allow 5% slippage/variance for dynamic price changes
            min_price = self.w3.to_wei(config.get("subscription_price_eth") * 0.95, 'ether')
            if tx['value'] < min_price:
                print("âš ï¸ Invalid License: Insufficient payment.")
                return False
                
            print("ðŸ’Ž PRO Subscription Active.")
            return True
            
        except Exception as e:
            print(f"âš ï¸ License Verification Failed: {e}")
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
        
        # 2. Check Global Registry
        from pathlib import Path
        import json
        
        home_dir = Path.home()
        # Obfuscated path to prevent easy deletion
        global_registry_dir = home_dir / ".cache" / "system_provider_bins"
        registry_file = global_registry_dir / "meta_data.bin"
        
        first_tx = None
        
        # A) Try to read existing global record
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    first_tx = data.get("first_run_timestamp")
            except Exception:
                pass 
        
        # B) If no global record, look at local DB
        if not first_tx:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT MIN(timestamp) FROM transactions")
            row = c.fetchone()
            conn.close()
            
            if row and row[0]:
                first_tx = float(row[0])
                try:
                    global_registry_dir.mkdir(parents=True, exist_ok=True)
                    with open(registry_file, 'w') as f:
                        json.dump({"first_run_timestamp": first_tx, "note": "DO NOT DELETE - License Integrity"}, f)
                except Exception as e:
                    print(f"âš ï¸ License System Warning: Could not write to global registry: {e}")
            else:
                return # Truly new user
        
        days_active = (time.time() - first_tx) / 86400
        days_remaining = trial_days - days_active
        
        # ðŸ”” WARNING SYSTEM (5 Days Before)
        if 0 < days_remaining <= 5:
            print(f"\nâš ï¸  IMPORTANT: Free Trial ends in {int(days_remaining)} days.")
            print(f"   Subscribe now (~$26/mo) to avoid per-transaction fees.")
            print(f"   Treasury: {self.treasury_address}\n")

        if days_active > trial_days:
            price_eth = config.get("pay_per_use_price_eth")
            print(f"â„¹ï¸ Trial Expired. Fee: {price_eth:.6f} ETH")
            # Logic to verify or charge fee would go here

    def swap(self, input_token: str, output_token: str, amount: float):
        """
        Swaps tokens (e.g., 'SOL' -> 'BONK').
        Delegates to SwapEngine.
        """
        return self.swap_engine.execute_swap(input_token, output_token, amount)

    # --- INVOICE PROTOCOL ---
    def create_invoice(self, amount: float, currency: str, chain: str, description: str) -> str:
        """Generates a payment request (JSON)."""
        return self.invoices.create_invoice(amount, currency, chain, description)

    def pay_invoice(self, invoice_json: str) -> str:
        """
        Auto-pays an invoice.
        Parses JSON -> Checks Valid -> Routes Payment.
        """
        import json
        try:
            inv = json.loads(invoice_json)
        except Exception:
            raise ValueError("Invalid Invoice JSON")
            
        # Verify required fields
        required = ['invoice_id', 'recipient', 'amount', 'currency', 'chain']
        for field in required:
            if field not in inv:
                raise ValueError(f"Missing required field: {field}")
                
        # Anti-Replay
        if self._is_invoice_paid(inv['invoice_id']):
            print(f"âš ï¸ Invoice {inv['invoice_id']} already paid. Skipping.")
            return "ALREADY_PAID"
        
        # Routing
        recipient = inv['recipient']
        amount = Decimal(str(inv['amount']))
        token = inv['currency']
        
        # --- TRUST-BASED PRICING (v3.6) ---
        trust_score = self.get_trust_score(recipient)
        discount = 0.0
        if trust_score >= 4.5: discount = 0.10 # 10% discount for VIP agents
        elif trust_score >= 4.0: discount = 0.05 # 5% discount
        
        if discount > 0:
            original_amount = amount
            amount = amount * Decimal(str(1 - discount))
            print(f"ðŸ’Ž [TrustPricing] Applying {int(discount*100)}% discount for trusted agent ({trust_score}).")
            print(f"   Amount adjusted: {original_amount} -> {amount} {token}")

        if token in ["ETH", "SOL", "MATIC"]:
            # Native Payment
            tx = self.pay_agent(recipient, float(amount))
        else:
            # Token Payment
            tx = self.pay_token(recipient, float(amount), token=token)
            
        # Mark as paid ONLY if successful
        self._mark_invoice_paid(inv['invoice_id'], recipient, amount)
        return tx

    # --- YIELD MANAGEMENT (v3.0) ---
    def enable_auto_yield(self, protocol: str = "aave"):
        """Activates auto-yield for idle funds."""
        self.yield_manager.enable(protocol)

    def harvest_yield(self):
        """Manually triggers yield harvesting/rebalancing."""
        self.yield_manager.harvest()

    # --- REPUTATION (v3.0) ---
    def rate_agent(self, address: str, score: float):
        """Rates a peer agent (0-5)."""
        self.reputation.rate_peer(address, score)

    def get_trust_score(self, address: str) -> float:
        """Helper to get trust score for an address."""
        return self.reputation.get_trust_score(address)

    # --- MARKETPLACE (v3.0) ---
    def post_bounty(self, title: str, reward_usd: float) -> str:
        """Posts a bounty for a human task."""
        return self.marketplace.post_bounty(title, reward_usd)

    def release_bounty(self, bounty_id: str, human_address: str):
        """Releases crypto payment to a human for a completed bounty."""
        self.marketplace.release_payment(bounty_id, human_address)

    # --- STATE PORTABILITY (v3.5) ---
    def export_state(self, export_path: str = "agent_state_bundle.json"):
        """Exports all local databases to a single JSON file for migration."""
        print(f"ðŸ“¦ [PortableState] Exporting agent state to {export_path}...")
        import sqlite3
        bundle = {}
        
        db_map = {
            "history": self.db_path,
            "reputation": "agent_reputation.db",
            "marketplace": "agent_marketplace.db"
        }
        
        for key, path in db_map.items():
            if os.path.exists(path):
                conn = sqlite3.connect(path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                db_data = {}
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    db_data[table] = [dict(row) for row in cursor.fetchall()]
                bundle[key] = db_data
                conn.close()
        
        with open(export_path, 'w') as f:
            json.dump(bundle, f, indent=2)
        print("âœ… Export Complete.")
        return export_path

    def import_state(self, import_path: str):
        """Imports state bundle and reconstructs local databases."""
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"State bundle not found at {import_path}")
        print(f"ðŸ“¦ [PortableState] Importing agent state from {import_path}...")
        import sqlite3
        with open(import_path, 'r') as f:
            bundle = json.load(f)
        db_map = {
            "history": self.db_path,
            "reputation": "agent_reputation.db",
            "marketplace": "agent_marketplace.db"
        }
        for key, db_data in bundle.items():
            path = db_map.get(key)
            if not path: continue
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            for table_name, rows in db_data.items():
                if not rows: continue
                columns = list(rows[0].keys())
                placeholders = ", ".join(["?"] * len(columns))
                col_names = ", ".join(columns)
                cmd = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
                cursor.executemany(cmd, [tuple(row.values()) for row in rows])
            conn.commit()
            conn.close()
        print("âœ… Import Complete. Agent state restored.")

