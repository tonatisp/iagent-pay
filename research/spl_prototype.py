from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

try:
    from spl.token.instructions import transfer_checked, create_associated_token_account, get_associated_token_address
    from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
    print("✅ SPL helper imports successful.")

    # Mock Data
    mint = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU") # USDC Devnet
    sender = Keypair()
    receiver = Keypair().pubkey()

    # 1. Calc ATA
    sender_ata = get_associated_token_address(sender.pubkey(), mint)
    receiver_ata = get_associated_token_address(receiver, mint)
    print(f"Sender ATA: {sender_ata}")

    # 2. Check if we can build instructions
    # Create ATA ix
    ix_create = create_associated_token_account(
        payer=sender.pubkey(),
        owner=receiver,
        mint=mint
    )
    print("✅ Created ATA Instruction")

    # Transfer ix (Checked is safer, requires decimals)
    ix_transfer = transfer_checked(
        source=sender_ata,
        mint=mint,
        dest=receiver_ata,
        owner=sender.pubkey(),
        amount=1000000, # 1 USDC
        decimals=6
    )
    print("✅ Created Transfer Instruction")

except ImportError as e:
    print(f"❌ Import Failed: {e}")
except Exception as e:
    print(f"❌ Logic Failed: {e}")
