import time
import json
from iagent_pay.agent_pay import AgentPay

def run_benchmark():
    print("⚡ iAgentPay Speed Benchmark v1.0 ⚡")
    print("Measuring latency across the 'Global Bridge'...\n")
    
    chains = ["BASE", "SOLANA", "XRP_TESTNET"]
    results = {}

    for chain in chains:
        print(f"🔗 Testing {chain}...")
        try:
            start_time = time.time()
            agent = AgentPay(chain_name=chain)
            
            # Measure 1: Connection Latency (RPC Ping)
            conn_start = time.time()
            if chain == "SOLANA":
                # Using a generic call to test RPC ping
                agent.solana.client.is_connected()
            elif "XRP" in chain:
                from xrpl.models.requests import Ping
                agent.xrpl.client.request(Ping())
            else:
                agent.w3.eth.get_block('latest')
            conn_end = time.time()
            
            conn_latency = (conn_end - conn_start) * 1000 # ms
            
            results[chain] = {
                "rpc_latency_ms": round(conn_latency, 2),
                "status": "✅ Online"
            }
            print(f"   ⏱️ RPC Latency: {conn_latency:.2f}ms")
            
        except Exception as e:
            results[chain] = {"status": f"⚠️ Error", "error": str(e)[:40]}
            print(f"   ⚠️ Error: {str(e)[:50]}...")

    print("\n📊 --- iAgentPay Latency Benchmark --- 📊")
    print("-" * 50)
    print("{:<15} | {:<15} | {:<10}".format("Chain", "RPC Latency", "Status"))
    print("-" * 50)
    for chain, data in results.items():
        latency = f"{data.get('rpc_latency_ms', '---')} ms"
        status = data['status']
        if "Error" in status:
             status += f" ({data.get('error', '')})"
        print("{:<15} | {:<15} | {:<10}".format(chain, latency, status))
    print("-" * 50)
    
    print("\n💡 Factores que afectan esta velocidad:")
    print("1. Block Time: El 'latido' de la red (Solana < 1s, Base 2s, XRP 3s).")
    print("2. Finalidad: Qué tan rápido el pago se vuelve irreversible.")
    print("3. Calidad del RPC: Tu puerta de entrada a la blockchain.")

if __name__ == "__main__":
    run_benchmark()
