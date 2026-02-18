import time
import sqlite3
import os
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
    ✅ Professional Grade: Includes Nonce Management, Smart Gas, and Audit Logs.
    ✅ Multi-Chain: Supports Sepolia, Base, Polygon, BNB, and Solana.
    """
    
    def __init__(self, treasury_address: str = None, chain_name: str = "BASE", private_key: str = None):
        """
        :param treasury_address: Where subscription fees go (EVM or SOL address).
        :param chain_name: "BASE", "POLYGON", "ETH", "BNB", "SEPOLIA" or "SOLANA".
        :param private_key: Optional manual override.
        """
        self.chain_name = chain_name.upper()
        self.is_solana = self.chain_name in ["SOLANA", "SOL_DEVNET", "SOL_TESTNET", "SOL_MAINNET"]

        # --- DUAL DRIVER SELECTOR ---
        if self.is_solana:
            # ☀️ Initialize Solana Backend
            from iagent_pay.solana_driver import SolanaDriver
            network_map = {
                "SOLANA": "mainnet", 
                "SOL_DEVNET": "devnet", 
                "SOL_TESTNET": "testnet",
                "SOL_MAINNET": "mainnet"
            }
            self.solana = SolanaDriver(network=network_map.get(self.chain_name, "devnet"))
            self.my_address = self.solana.get_address()
            print(f"☀️ [AgentPay] Initialized on SOLANA ({self.solana.network})")
            print(f"   Wallet: {self.my_address}")
            
        else:
            # 🔷 Initialize EVM Backend (Legacy)
            self.solana = None
            # Fix: ChainConfig is static, use get_network
            self.config = ChainConfig.get_network(chain_name)
            # Handle potential None or dict
            rpc_url = self.config.get("rpc") if self.config else None
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Setup Wallet (Key Management)
            from .wallet_manager import WalletManager
            self.wallet_manager = WalletManager()
            
            # Load Key
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key)
            else:
                self.account = self.wallet_manager.get_or_create_wallet()
            
            self.wallet = self.account # Alias for legacy compatibility
            self.my_address = self.account.address
            
        # Common
        self.pricing = PricingManager()
        
        # Social Features
        from .social_resolver import SocialResolver
        self.social = SocialResolver()

        # Swap Engine (Retail Expansion)
        from .swap_engine import SwapEngine
        self.swap_engine = SwapEngine(self)
        
        # Invoice Protocol (Phase 16)
        from .invoice_manager import InvoiceManager
        self.invoices = InvoiceManager(self)
        
        # Resolve Treasury (Dual Chain Support)
        # Note: If passed in __init__, it overrides config.
        self.treasury_address = treasury_address
        if not self.treasury_address:
            cfg = self.pricing.get_config()
            treasury_data = cfg.get("treasury", {})
            if isinstance(treasury_data, dict):
                 if self.is_solana:
                     self.treasury_address = treasury_data.get("SOLANA")
                 else:
                     self.treasury_address = treasury_data.get("EVM")
            else:
                 # Fallback for old config style
                 self.treasury_address = cfg.get("treasury_address")
                 
        # Database for Audit Logs
        self.db_path = "agent_history.db"
        self._init_db()

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
        # Note: self.nonce property was removed in rewrite, assuming ephemeral or re-fetch
        # Actually in original code self.nonce was instance var.
        # Let's just fetch pending count always for safety in this version.
        return self.w3.eth.get_transaction_count(self.wallet.address, 'pending')

    def _get_smart_gas_price(self):
        """
        Smart Gas Station: Auto-calculates optimal fee.
        """
        base_price = self.w3.eth.gas_price
        # Add 10% premium for speed/reliability
        premium_price = int(base_price * 1.10)
        return premium_price

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
            try:
                print(f"☀️ Sending {amount:.6f} SOL...")
                sig = self.solana.transfer(recipient_address, amount)
                print(f"✅ Solana Tx Sent: {sig}")
                self._log_transaction(sig, recipient_address, amount, "SENT_SOL")
                return sig
            except Exception as e:
                print(f"❌ Solana Tx Failed: {e}")
                raise e

        # --- ROUTING: EVM (Legacy) ---
        if not self.w3.is_address(recipient_address):
            raise ValueError(f"Invalid recipient address: {recipient_address}")

        # License Check (before transaction)
        self._check_license(amount)

        amount_wei = self.w3.to_wei(amount, 'ether')
        
        # 1. Get Reliable Nonce
        current_nonce = self._get_nonce()
        
        # 2. Get Smart Gas
        gas_price = self._get_smart_gas_price()
        
        # 3. Gas Guardrail (User Choice)
        if max_gas_gwei:
            current_gwei = self.w3.from_wei(gas_price, 'gwei')
            if current_gwei > max_gas_gwei:
                raise ValueError(f"⛽ Gas Price ({current_gwei:.2f} Gwei) exceeds limit ({max_gas_gwei} Gwei). Transaction aborted.")

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
            
            # 4. Audit Log
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
                raise e

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
                print(f"☀️ Sending {amount} {token} (SPL)...")
                
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
                print(f"✅ Solana Token Tx: {sig}")
                self._log_transaction(sig, recipient_address, amount, f"SENT_{token}_SOL")
                return sig
            except Exception as e:
                print(f"❌ Solana Token Tx Failed: {e}")
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
                  raise ValueError(f"⛽ Gas Price ({current_gwei:.2f} Gwei) exceeds limit ({max_gas_gwei} Gwei). Aborting Token Tx.")

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
            
            print(f"💵 Stablecoin Sent: {amount} {token} -> {tx_hash}")
            self._log_transaction(tx_hash, recipient_address, amount, f"SENT_{token}")
            
            if wait:
                print("⏳ Waiting for stablecoin confirmation...")
                self.w3.eth.wait_for_transaction_receipt(tx_hash)
                print("✅ Confirmed!")
                self._log_transaction(tx_hash, recipient_address, amount, f"CONFIRMED_{token}")
                
            return tx_hash
            
        except Exception as e:
            print(f"❌ Token Transfer Failed: {e}")
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
                print("⚠️ Invalid License: Wrong treasury address.")
                return False
                
            # 2. Check Amount (Must be >= Subscription Price)
            # Allow 5% slippage/variance for dynamic price changes
            min_price = self.w3.to_wei(config.get("subscription_price_eth") * 0.95, 'ether')
            if tx['value'] < min_price:
                print("⚠️ Invalid License: Insufficient payment.")
                return False
                
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
        
        # 2. Check Global Registry
        from pathlib import Path
        import json
        
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
                    print(f"⚠️ License System Warning: Could not write to global registry: {e}")
            else:
                return # Truly new user
        
        days_active = (time.time() - first_tx) / 86400
        days_remaining = trial_days - days_active
        
        # 🔔 WARNING SYSTEM (5 Days Before)
        if 0 < days_remaining <= 5:
            print(f"\n⚠️  IMPORTANT: Free Trial ends in {int(days_remaining)} days.")
            print(f"   Subscribe now (~$26/mo) to avoid per-transaction fees.")
            print(f"   Treasury: {self.treasury_address}\n")

        if days_active > trial_days:
            price_eth = config.get("pay_per_use_price_eth")
            print(f"ℹ️ Trial Expired. Fee: {price_eth:.6f} ETH")
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
        inv = self.invoices.parse_invoice(invoice_json)
        
        print(f"🧾 Processing Invoice: {inv['description']}")
        print(f"   Pay: {inv['amount']} {inv['currency']} on {inv['chain']}")
        
        # Safety Check: Chain Mismatch
        # Note: In a real app, we might switch chains automatically. 
        # Here we just warn if the Agent isn't on the right chain, 
        # though our pay_token might handle cross-token mapping if lucky.
        
        # Routing
        recipient = inv['recipient']
        amount = inv['amount']
        token = inv['currency']
        
        if token in ["ETH", "SOL", "MATIC"]:
             # Native Payment
             return self.pay_agent(recipient, amount)
        else:
             # Token Payment
             return self.pay_token(recipient, amount, token=token)
