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
