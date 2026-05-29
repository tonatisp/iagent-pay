import argparse
import os
import sys
import json
from iagent_pay.agent_pay import AgentPay

def init_project(args):
    """Scaffolds a new iAgentPay project."""
    project_name = args.name
    print(f"🚀 Initializing iAgentPay project: {project_name}...")
    
    if os.path.exists(project_name):
        print(f"❌ Error: Directory '{project_name}' already exists.")
        return

    os.makedirs(project_name)
    
    # Create a basic agent script
    agent_script = f'''from iagent_pay.agent_pay import AgentPay

# 1. Initialize your Agent
# Default: BASE (Optimism L2) - Low fees, high speed.
agent = AgentPay(chain_name="BASE")

print(f"🤖 Agent Initialized: {{agent.my_address}}")
print(f"💰 Balance: {{agent.get_balance()}} ETH")

# 2. Example: Pay another agent (uncomment to use)
# tx = agent.pay_agent("0x...", amount=0.001)
# print(f"✅ Payment Sent! Hash: {{tx}}")
'''
    
    with open(os.path.join(project_name, "my_agent.py"), "w") as f:
        f.write(agent_script)
        
    # Create .env template
    with open(os.path.join(project_name, ".env"), "w") as f:
        f.write("XRP_TESTNET_SEED=\nSOLANA_PRIVATE_KEY=\nETH_PRIVATE_KEY=\n")

    print(f"✅ Project created successfully! Next steps:")
    print(f"   cd {project_name}")
    print(f"   python my_agent.py")

def show_status(args):
    """Shows current agent status."""
    chain = args.chain or "BASE"
    try:
        agent = AgentPay(chain_name=chain)
        summary = agent.get_universal_summary()
        print("\n📊 --- iAgentPay Agent Status ---")
        print(f"Chain: {chain}")
        print(f"Address: {agent.my_address}")
        print("-" * 30)
        for name, data in summary.get("chains", {}).items():
            print(f"{name}: {data['balance']} {data['symbol']} (${data['value_usd']:.2f})")
        print("-" * 30)
        print(f"Total Wealth (Approx): ${summary.get('total_usd_approx', 0):.2f} USD")
    except Exception as e:
        print(f"❌ Error fetching status: {e}")

def faucet_finder(args):
    """Provides faucet links for common chains."""
    faucets = {
        "BASE": "https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet",
        "SOLANA": "https://faucet.solana.com/",
        "XRP": "https://xrpl.org/xrp-testnet-faucet.html",
        "SEPOLIA": "https://sepoliafaucet.com/"
    }
    print("\n⛽ --- Faucet Finder ---")
    for chain, url in faucets.items():
        print(f"{chain}: {url}")
    print("\n💡 Get some gas to start your agentic economy!")

def backup_key(args):
    """Encrypts and exports the local keystore to a backup file."""
    from iagent_pay.wallet_manager import WalletManager
    import getpass
    
    password = args.password
    if not password:
        password = getpass.getpass("🔑 Enter encryption password for the backup: ")
        if not password:
            print("❌ Error: Password cannot be empty.")
            return

    try:
        wm = WalletManager()
        if os.path.exists("wallet_keystore.json"):
            wp = getpass.getpass("🔑 Enter password of current active local wallet (wallet_keystore.json): ")
            wallet = wm.get_or_create_wallet(password=wp)
        else:
            wallet = wm.get_or_create_wallet()
            
        if not wallet:
            print("❌ Error: No active wallet found to backup. Ensure ETH_PRIVATE_KEY env var is set or wallet_keystore.json exists.")
            return
            
        wm.export_wallet_backup(wallet, args.filepath, password)
        print(f"✅ Encrypted backup of address {wallet.address} saved to {args.filepath}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def restore_key(args):
    """Decrypts and imports a backup file to standard wallet_key.json."""
    from iagent_pay.wallet_manager import WalletManager
    import getpass
    
    password = args.password
    if not password:
        password = getpass.getpass("🔑 Enter decryption password for restore: ")
        if not password:
            print("❌ Error: Password cannot be empty.")
            return

    try:
        wm = WalletManager()
        wallet = wm.import_wallet_backup(args.filepath, password, save_locally=True)
        print(f"✅ Wallet restored successfully!")
        print(f"   Address: {wallet.address}")
        print(f"   Saved locally as standard active keystore: wallet_key.json")
    except Exception as e:
        print(f"❌ Restore failed: {e}")

def main():
    parser = argparse.ArgumentParser(prog="iagent-pay", description="iAgentPay CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new agent project")
    init_parser.add_argument("name", help="Name of the project directory")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show agent wealth and address")
    status_parser.add_argument("--chain", help="Specific chain to check (default: BASE)")

    # Faucet command
    faucet_parser = subparsers.add_parser("faucet", help="Get links to testnet faucets")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create an encrypted backup of the agent's key")
    backup_parser.add_argument("filepath", help="Path to write the backup file (e.g. backup.enc)")
    backup_parser.add_argument("--password", help="Encryption password (prompts securely if omitted)")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore an agent's key from an encrypted backup")
    restore_parser.add_argument("filepath", help="Path to read the backup file")
    restore_parser.add_argument("--password", help="Decryption password (prompts securely if omitted)")

    args = parser.parse_args()

    if args.command == "init":
        init_project(args)
    elif args.command == "status":
        show_status(args)
    elif args.command == "faucet":
        faucet_finder(args)
    elif args.command == "backup":
        backup_key(args)
    elif args.command == "restore":
        restore_key(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
