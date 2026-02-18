from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.client import Token

# Mock Setup
client = Client("https://api.devnet.solana.com")
payer = Keypair()
mint = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")

try:
    # Instantiate Token Client
    spl_client = Token(client, mint, TOKEN_PROGRAM_ID, payer)
    print("✅ Token Client Instantiated")
    
    # Check if methods exist
    print(f"Has transfer? {hasattr(spl_client, 'transfer')}")
    print(f"Has create_associated_token_account? {hasattr(spl_client, 'create_associated_token_account')}")
    print(f"Has get_accounts_by_owner? {hasattr(spl_client, 'get_accounts_by_owner')}")

except Exception as e:
    print(f"❌ Failed: {e}")
