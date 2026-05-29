import asyncio
import time
import json
from concurrent.futures import ThreadPoolExecutor
from iagent_pay.agent_pay import AgentPay

import random

def simulate_agent_flow(agent_id, results):
    start_time = time.time()
    try:
        # Add random jitter between 0 and 2 seconds to simulate realistic traffic and prevent instant SQLite locks
        time.sleep(random.uniform(0, 2))
        
        agent = AgentPay(enable_auto_swap=False)
        
        t0 = time.time()
        invoice = agent.invoices.create_invoice(
            amount=50.0 + agent_id,
            currency="USDC",
            description=f"Invoice Agent-{agent_id}",
            chain="EVM"
        )
        t_invoice = time.time() - t0
        
        t0 = time.time()
        quote = agent.swap_engine.get_quote(
            input_token="USDC",
            output_token="ETH",
            amount=50.0 + agent_id
        )
        t_quote = time.time() - t0
        
        t0 = time.time()
        tx = agent.swap_engine.execute_swap(
            input_token="USDC",
            output_token="ETH",
            amount=50.0 + agent_id
        )
        t_exec = time.time() - t0
        
        results.append({
            "agent_id": agent_id,
            "success": True,
            "t_invoice": t_invoice,
            "t_quote": t_quote,
            "t_exec": t_exec,
            "total_time": time.time() - start_time
        })
    except Exception as e:
        results.append({
            "agent_id": agent_id,
            "success": False,
            "error": str(e),
            "total_time": time.time() - start_time
        })

async def run_stress_test_async(num_agents, max_workers):
    print(f"Iniciando prueba de estrés con {num_agents} agentes concurrentes...")
    results = []
    
    t_start = time.time()
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, simulate_agent_flow, i, results)
            for i in range(num_agents)
        ]
        await asyncio.gather(*tasks)
        
    total_time = time.time() - t_start
    
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    print("\n" + "="*50)
    print("=== REPORTE DE DESEMPEÑO (STRESS TEST) ===")
    print("="*50)
    print(f"Total Agentes Simulados: {num_agents}")
    print(f"Concurrencia (Workers): {max_workers}")
    print(f"Tiempo Total de Prueba: {total_time:.2f} segundos")
    print(f"Transacciones Exitosas: {len(successes)}")
    print(f"Transacciones Fallidas: {len(failures)}")
    
    if len(successes) > 0:
        avg_invoice = sum(r["t_invoice"] for r in successes) / len(successes)
        avg_quote = sum(r["t_quote"] for r in successes) / len(successes)
        avg_exec = sum(r["t_exec"] for r in successes) / len(successes)
        avg_total = sum(r["total_time"] for r in successes) / len(successes)
        
        print(f"\n--- Tiempos Promedio ---")
        print(f"Generación de Factura: {avg_invoice*1000:.2f} ms")
        print(f"Cotización de Oráculo: {avg_quote*1000:.2f} ms")
        print(f"Ejecución de Swap/Firma: {avg_exec*1000:.2f} ms")
        print(f"Ciclo Completo por Agente: {avg_total*1000:.2f} ms")
        
        print(f"\n--- Capacidad ---")
        print(f"RPS (Transacciones/segundo): {len(successes)/total_time:.2f} tx/s")
        
    if len(failures) > 0:
        print(f"\n--- Errores Encontrados ---")
        for i, f in enumerate(failures[:5]):
            print(f"Agent {f['agent_id']}: {f['error']}")
        if len(failures) > 5:
            print(f"... y {len(failures) - 5} más.")

if __name__ == "__main__":
    async def main():
        await run_stress_test_async(num_agents=20, max_workers=5)
        print("\n\nEspere 5 segundos para estabilización de base de datos...\n")
        time.sleep(5)
        await run_stress_test_async(num_agents=50, max_workers=10)
        
    asyncio.run(main())
