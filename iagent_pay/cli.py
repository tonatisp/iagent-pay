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

    args = parser.parse_args()

    if args.command == "init":
        init_project(args)
    elif args.command == "status":
        show_status(args)
    elif args.command == "faucet":
        faucet_finder(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
