import time
from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solders.keypair import Keypair
from solders.pubkey import Pubkey

def main():
    print("☀️ Solana Probe: Starting...")

    # 1. Connect to Testnet (Devnet often rate-limited)
    client = Client("https://api.testnet.solana.com")
    print("✅ Connected to Testnet.")

    # 2. Generate a fresh Keypair
    sender = Keypair()
    receiver = Keypair()
    print(f"🔑 Sender: {sender.pubkey()}")
    
    # 3. Request Airdrop (1 SOL)
    print("💧 Requesting Airdrop...")
    try:
        # Note: API might return an object or dict depending on version
        resp = client.request_airdrop(sender.pubkey(), 1_000_000_000)
        airdrop_sig = resp.value if hasattr(resp, 'value') else resp
        print(f"   Sig: {airdrop_sig}")
        
        print("⏳ Waiting for confirmation...")
        time.sleep(10)
        client.confirm_transaction(airdrop_sig)
        print("✅ Airdrop Confirmed.")
    except Exception as e:
        print(f"❌ Airdrop Failed: {e}")
        return

    # 4. Send Transaction
    print("🚀 Sending 0.1 SOL...")
    try:
        # Latest 'solders' often uses 'transfer' function that returns Instruction
        ix = transfer(
            TransferParams(
                from_pubkey=sender.pubkey(),
                to_pubkey=receiver.pubkey(),
                lamports=100_000_000
            )
        )
        
        recent_blockhash = client.get_latest_blockhash().value.blockhash
        tx = Transaction()
        tx.add(ix)
        tx.recent_blockhash = recent_blockhash
        
        # New Signing Pattern
        tx.sign_partial(sender) 
        
        # Send
        sig = client.send_transaction(tx, sender).value
        print(f"✅ Transaction Sent! Signature: {sig}")
        print(f"🔗 Explorer: https://explorer.solana.com/tx/{sig}?cluster=devnet")

    except Exception as e:
        print(f"❌ Transaction Failed (API Mismatch likely): {e}")
        # Debugging help
        import solders.system_program
        print(f"DEBUG: Available in solders.system_program: {dir(solders.system_program)}")

if __name__ == "__main__":
    main()
