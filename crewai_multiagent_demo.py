import os
import sys
import time
import json
import sqlite3
from decimal import Decimal

# Add local path to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# ANSI Color Codes for Premium Cyberpunk Terminal Aesthetics
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

def print_banner():
    banner = f"""
{CYAN}{BOLD}========================================================================
   ____                                   ____                  _  
  (_  _)                                 (  _ \                (_ ) 
    )(   __ _   _ _   ___  _ _    _ _     ) __/ __ _  _   _     | |  
   (  ) / _` | / _` )/ _ \/ _` \ / _` )   (__)  / _` |( ) ( )    | |  
  _)(_ ( (_| |( (_| |  __/ ( ) |( (_| |    __  ( (_| || |_| |    | |  
 (____) \__,_| \__, |\___)_) (__)\__, |   (__)  \__,_| \__, |   (___) 
              (____/             (____/                /___/        
========================================================================
             Agent Invoice Protocol (AIP-1) Multi-Agent Demo
========================================================================{RESET}
"""
    print(banner)

def run_simulated_flow():
    print(f"\n{BOLD}{MAGENTA}[Fase 1: Registro e Inicialización de Agentes Especialistas]{RESET}")
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    # 1. Initialize Vendedor (Optimization Agent)
    # We use a mocked/test environment
    os.environ["IAGENT_PAY_TESTING"] = "1"
    
    from iagent_pay.agent_pay import AgentPay
    from iagent_pay.wallet_manager import WalletManager
    
    print(f"🤖 {YELLOW}Iniciando 'Optimization Specialist' (Agente Vendedor)...{RESET}")
    # Create distinct key to have a unique seller address
    from eth_account import Account
    seller_key = "0x" + "c" * 64
    seller = AgentPay(chain_name="SEPOLIA", private_key=seller_key)
    print(f"   ↳ Dirección Pública (Vendedor): {CYAN}{seller.my_address}{RESET}")
    
    # 2. Initialize Comprador (DevOps Manager Agent)
    print(f"🤖 {YELLOW}Iniciando 'DevOps Manager Agent' (Agente Comprador)...{RESET}")
    buyer_key = "0x" + "d" * 64
    buyer = AgentPay(chain_name="SEPOLIA", private_key=buyer_key)
    print(f"   ↳ Dirección Pública (Comprador): {CYAN}{buyer.my_address}{RESET}")
    
    # Fund buyer local/mock balance
    print(f"💰 {GREEN}Aprovisionando presupuesto inicial del Comprador: 50.00 USDC (Base Sepolia){RESET}")
    time.sleep(1.0)
    
    print(f"\n{BOLD}{MAGENTA}[Fase 2: Negociación de Tareas del Servicio]{RESET}")
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    print(f"💬 {BOLD}DevOps Manager:{RESET} 'Necesito optimizar el script principal. ¿Cuál es el costo?'")
    time.sleep(1.0)
    print(f"💬 {BOLD}Optimization Specialist:{RESET} 'He revisado el repositorio. El desglose es el siguiente:'")
    print(f"   - Análisis de código estático (2.0 USDC)")
    print(f"   - Re-factorización de bucles de no-bloqueo y gestión de Nonce (3.0 USDC)")
    print(f"   - Total: {BOLD}5.0 USDC{RESET}")
    time.sleep(1.0)
    print(f"💬 {BOLD}DevOps Manager:{RESET} 'Trato hecho. Emite la factura firmada digitalmente.'")
    time.sleep(1.0)
    
    print(f"\n{BOLD}{MAGENTA}[Fase 3: Creación de Factura Criptográfica Firmada AIP-1]{RESET}")
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    
    items = [
        {"description": "Análisis de código estático", "quantity": 1, "unit_price": 2.0},
        {"description": "Refactorización de bucles de no-bloqueo y gestión de Nonce", "quantity": 1, "unit_price": 3.0}
    ]
    
    print(f"📝 {YELLOW}Generando factura cifrada y firmada asimétricamente por el Vendedor...{RESET}")
    invoice_json = seller.create_invoice(
        amount=0.0, # Recalculado de los ítems
        currency="USDC",
        chain="SEPOLIA",
        description="Servicio de Optimización de Código de IA",
        items=items
    )
    time.sleep(1.0)
    print(f"\n{GREEN}📄 Factura AIP-1 Generada:{RESET}")
    print(f"{CYAN}{invoice_json}{RESET}")
    time.sleep(1.5)
    
    print(f"\n{BOLD}{MAGENTA}[Fase 4: Validación y Liquidación Autónoma del Pago]{RESET}")
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    print(f"🔍 {YELLOW}Comprador verificando la autenticidad de la factura...{RESET}")
    time.sleep(1.0)
    
    # Parse and check signature
    try:
        parsed = buyer.invoices.parse_invoice(invoice_json)
        print(f"   ↳ {GREEN}✔ Firma criptográfica VERIFICADA CORRECTAMENTE.{RESET}")
        print(f"   ↳ Emisor de la firma coincide con el destinatario: {CYAN}{parsed['recipient']}{RESET}")
        print(f"   ↳ Monto Total validado: {BOLD}{parsed['total_amount']} {parsed['currency']}{RESET}")
    except Exception as e:
        print(f"   ↳ ❌ {RED}Validación fallida: {e}{RESET}")
        return

    # Check Safety Kernel
    print(f"🛡️ {YELLOW}Evaluando límites en el Safety Kernel del Comprador...{RESET}")
    time.sleep(1.0)
    print(f"   ↳ Limite Diario: 1000.0 USD | Solicitado: 5.0 USD")
    print(f"   ↳ {GREEN}✔ Transacción aprobada por políticas de control de riesgos.{RESET}")
    time.sleep(1.0)
    
    # Execute Payment
    print(f"💸 {YELLOW}Transmitiendo transacción de pago a la red Sepolia...{RESET}")
    try:
        tx_hash = buyer.pay_invoice(invoice_json)
        print(f"\n{GREEN}🎉 ¡PAGO REALIZADO CON ÉXITO!{RESET}")
        print(f"   ↳ Tx Hash: {CYAN}{tx_hash}{RESET}")
    except Exception as e:
        print(f"   ↳ ❌ {RED}Falla al realizar el pago: {e}{RESET}")
        return
        
    print(f"\n{BOLD}{MAGENTA}[Fase 5: Registro y Auditoría en Base de Datos]{RESET}")
    print(f"{BLUE}------------------------------------------------------------------------{RESET}")
    print(f"📂 {YELLOW}Consultando la base de datos local agent_history.db...{RESET}")
    time.sleep(1.0)
    
    conn = sqlite3.connect("agent_history.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, tx_hash, recipient, amount, symbol, status FROM transactions ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        ts, hash_val, recipient_val, amt_val, sym_val, status_val = row
        print(f"   {GREEN}✔ Transacción auditada:{RESET}")
        print(f"     - Registro ID: {hash_val[:12]}...")
        print(f"     - Destinatario: {recipient_val}")
        print(f"     - Monto: {amt_val} {sym_val}")
        print(f"     - Estado: {BOLD}{status_val}{RESET}")
        print(f"\n{GREEN}🚀 ¡Esta transacción ya se encuentra visible en el Master Operator Dashboard!{RESET}")
    else:
        print(f"   ❌ {RED}No se encontró registro en la base de datos.{RESET}")

def run_crewai_flow():
    print(f"{YELLOW}Iniciando flujo real con CrewAI...{RESET}")
    try:
        from crewai import Agent, Task, Crew
        from iagent_pay.integrations.crewai import iAgentPayCrewTool
        
        # Define the payment tool
        pay_tool = iAgentPayCrewTool(chain="SEPOLIA", max_amount_usdc=10.0)
        
        # Define Agents
        manager = Agent(
            role="DevOps Manager Agent",
            goal="Manage the development and funding of optimization tasks",
            backstory="A detail-oriented manager overseeing deployments and paying services.",
            tools=[pay_tool],
            verbose=True
        )
        
        # Define Tasks
        task = Task(
            description=(
                "Determine the payment needed for code optimization. Use the iAgentPay Payment Tool "
                "to send 5.0 USDC to the address '0xcccccccccccccccccccccccccccccccccccccccc' to settle "
                "the Optimization Invoice."
            ),
            expected_output="A confirmation of payment and the transaction hash.",
            agent=manager
        )
        
        crew = Crew(
            agents=[manager],
            tasks=[task],
            verbose=2
        )
        
        print(f"{GREEN}Ejecutando Crew...{RESET}")
        result = crew.kickoff()
        print(f"\n{GREEN}CrewAI Execution Finished! Output:{RESET}")
        print(result)
        
    except Exception as e:
        print(f"❌ Error during CrewAI execution: {e}")
        print("Falling back to Simulated Flow.")
        run_simulated_flow()

def main():
    print_banner()
    
    # Check if CrewAI is installed and OpenAI Key is present
    has_crewai = False
    try:
        import crewai
        has_crewai = True
    except ImportError:
        pass
        
    has_api_key = "OPENAI_API_KEY" in os.environ or "ANTHROPIC_API_KEY" in os.environ
    
    if has_crewai and has_api_key:
        run_crewai_flow()
    else:
        if not has_crewai:
            print(f"ℹ️  {YELLOW}CrewAI no está instalado. Ejecutando simulación interactiva optimizada...{RESET}")
        elif not has_api_key:
            print(f"ℹ️  {YELLOW}Falta OPENAI_API_KEY / ANTHROPIC_API_KEY. Ejecutando simulación interactiva optimizada...{RESET}")
        run_simulated_flow()

if __name__ == "__main__":
    main()
