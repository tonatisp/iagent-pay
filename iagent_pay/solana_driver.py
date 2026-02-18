import json
import os
from typing import Optional, Dict, Any, Union
from pathlib import Path

# External Libs (Rust/Python)
print("⚡ Loading SolanaDriver Module v2...")
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

class SolanaDriver:
    """
    Handles all interactions with the Solana Blockchain (SVM).
    """
    # USDC Mint Addresses (Standard)
    USDC_MINT_DEVNET = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    USDC_MINT_MAINNET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    # USDT (Tether)
    USDT_MINT_MAINNET = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
    USDT_MINT_DEVNET = "Qr8PRpM28tU4f6q3C8895b6X6136653842667439746" # Mock/Faucet Mint

    # MEME COINS (Culture Economy)
    BONK_MINT_MAINNET = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    WIF_MINT_MAINNET = "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
    POPCAT_MINT_MAINNET = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"


    def __init__(self, network: str = "devnet"):
        self.network = network.lower()
        
        # 1. Select RPC
        if self.network == "mainnet":
            self.rpc_url = "https://api.mainnet-beta.solana.com"
            self.usdc_mint = self.USDC_MINT_MAINNET
            self.usdt_mint = self.USDT_MINT_MAINNET
            # Memes
            self.bonk_mint = self.BONK_MINT_MAINNET
            self.wif_mint = self.WIF_MINT_MAINNET
            self.popcat_mint = self.POPCAT_MINT_MAINNET
            
        elif self.network == "testnet":
            self.rpc_url = "https://api.testnet.solana.com"
            self.usdc_mint = self.USDC_MINT_DEVNET 
            self.usdt_mint = self.USDT_MINT_DEVNET
        else: # devnet
            self.rpc_url = "https://api.devnet.solana.com"
            self.usdc_mint = self.USDC_MINT_DEVNET
            self.usdt_mint = self.USDT_MINT_DEVNET
            # Memes (Not available on Devnet usually, set to None or specific mock if created)
            self.bonk_mint = None 
            self.wif_mint = None
            self.popcat_mint = None
            
        self.client = Client(self.rpc_url)
        self.explorer_url = f"https://explorer.solana.com/tx/{{}}?cluster={self.network}"

        # 2. Setup Key Management
        self.wallet_path = Path.home() / ".iagent_pay_registry" / "solana_id.json"
        self.keypair: Optional[Keypair] = None
        self._load_or_create_wallet()

    def get_token_balance(self, mint_address: str = None) -> float:
        """Returns balance of a specific SPL Token."""
        # Clean the input string just in case
        val_raw = mint_address or self.usdc_mint
        if not val_raw:
             return 0.0
        val_to_use = val_raw.strip()
        
        try:
            target_mint = Pubkey.from_string(val_to_use)
            
            # Get Associated Token Account (Static helper)
            ata = get_associated_token_address(self.keypair.pubkey(), target_mint)
            
            resp = self.client.get_token_account_balance(ata)
            if hasattr(resp, 'value'):
                return float(resp.value.ui_amount or 0.0)
            return 0.0
        except Exception as e:
            # Likely ATA doesn't exist yet or invalid mint
            # print(f"⚠️ [Solana] Token Balance Error: {e}")
            return 0.0

    def transfer_token(self, to_address: str, amount: float, mint_address: str = None) -> str:
        """
        Sends SPL Tokens (default USDC).
        Auto-creates recipient ATA if needed.
        """
        val_raw = mint_address or self.usdc_mint
        try:
            target_mint = Pubkey.from_string(val_raw.strip())
        except Exception as e:
            raise ValueError(f"Invalid Mint Address: '{val_raw}' Error: {e}")

        try:
             recipient_pubkey = Pubkey.from_string(to_address.strip())
        except Exception as e:
             raise ValueError(f"Invalid Recipient Address: '{to_address}' Error: {e}")
        
        try:
            print(f"🔄 Initializing Token Transfer ({amount} units)...")
            spl_client = Token(self.client, target_mint, TOKEN_PROGRAM_ID, self.keypair)
            
            # 1. Get/Create Sender ATA (Should exist if we have funds)
            # Use static helper
            source_ata = get_associated_token_address(self.keypair.pubkey(), target_mint)
            
            # 2. Derive Recipient ATA
            dest_ata = get_associated_token_address(recipient_pubkey, target_mint)
            
            # 3. Check if Dest ATA exists
            print(f"DEBUG: RPC getAccountInfo {dest_ata}") # Added print before RPC call
            acc_info = self.client.get_account_info(dest_ata)
            
            # Note: Checking value property logic
            exists = False
            if hasattr(acc_info, 'value'):
                exists = acc_info.value is not None
            else:
                exists = acc_info is not None

            if not exists:
                print("✨ Creating Recipient ATA...")
                try:
                    spl_client.create_associated_token_account(recipient_pubkey)
                except Exception as e:
                     print(f"⚠️ ATA Create Warning (might exist): {e}")
            
            # 4. Transfer
            mint_info = spl_client.get_mint_info()
            decimals = mint_info.decimals
            amount_int = int(amount * (10 ** decimals))
            
            print(f"💸 Sending {amount_int} base units...")
            resp = spl_client.transfer(
                source=source_ata,
                dest=dest_ata,
                owner=self.keypair,
                amount=amount_int
            )
            
            sig = resp.value if hasattr(resp, 'value') else resp
            return str(sig)

        except Exception as e:
            raise Exception(f"[Solana] Token Transfer Failed: {e}")

    def request_airdrop(self, amount_sol: float = 1.0):
        """Request Testnet/Devnet SOL."""
        if self.network == "mainnet":
            print("❌ Cannot Airdrop on Mainnet.")
            return

        print(f"💧 Requesting {amount_sol} SOL Airdrop for {self.get_address()}...")
        try:
            lamports = int(amount_sol * 1_000_000_000)
            resp = self.client.request_airdrop(self.keypair.pubkey(), lamports)
            sig = resp.value if hasattr(resp, 'value') else resp
            
            import time
            print("⏳ Confirming Airdrop...")
            time.sleep(10)
            self.client.confirm_transaction(sig)
            print("✅ Airdrop Received!")
        except Exception as e:
            print(f"❌ Airdrop Failed: {e}")

    def _load_or_create_wallet(self):
        env_key = os.getenv("SOLANA_PRIVATE_KEY")
        if env_key:
            try:
                self.keypair = Keypair.from_base58_string(env_key)
                print(f"✅ [Solana] Wallet loaded from Environment: {self.get_address()}")
                return
            except Exception:
                pass

        if self.wallet_path.exists():
            try:
                with open(self.wallet_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.keypair = Keypair.from_bytes(data)
                        print(f"✅ [Solana] Wallet loaded from Disk: {self.get_address()}")
                        return
            except Exception:
                pass

        print("🆕 [Solana] Creating new Solana Wallet...")
        self.keypair = Keypair()
        self._save_wallet_to_disk()
        print(f"✅ [Solana] Generated new wallet: {self.get_address()}")

    def _save_wallet_to_disk(self):
        if not self.wallet_path.parent.exists():
            self.wallet_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.wallet_path, "w") as f:
            json.dump(list(bytes(self.keypair)), f)

    def get_address(self) -> str:
        return str(self.keypair.pubkey())

    def get_balance(self) -> float:
        try:
            resp = self.client.get_balance(self.keypair.pubkey())
            lamports = resp.value if hasattr(resp, 'value') else resp
            return lamports / 1_000_000_000.0
        except Exception as e:
            print(f"❌ [Solana] Failed to fetch balance: {e}")
            return 0.0

    def transfer(self, to_address: str, amount_sol: float) -> str:
        lamports = int(amount_sol * 1_000_000_000)
        try:
            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(to_address),
                    lamports=lamports
                )
            )
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            tx = Transaction()
            tx.add(ix)
            tx.recent_blockhash = recent_blockhash
            tx.sign_partial(self.keypair)
            resp = self.client.send_transaction(tx, self.keypair)
            signature = resp.value if hasattr(resp, 'value') else resp
            return str(signature)
        except Exception as e:
            raise Exception(f"[Solana] Transfer Failed: {e}")
