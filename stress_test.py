import os
import time
import threading
import random
import json
import logging
from concurrent.futures import ThreadPoolExecutor

# Set testing environment so we don't accidentally burn real money if mainnet is default
os.environ["IAGENT_PAY_TESTING"] = "1"
os.environ["IAGENT_MOCK_WEB3"] = "1" # If supported
os.environ["ETH_PRIVATE_KEY"] = "0x0000000000000000000000000000000000000000000000000000000000000001"
os.environ["SOLANA_PRIVATE_KEY"] = "3" * 87

# Configure logging to only show critical to avoid terminal spam
logging.getLogger("iagentpay").setLevel(logging.CRITICAL)

try:
    from iagent_pay.agent_pay import AgentPay
    from iagent_pay.swap_engine import SwapEngine
    from iagent_pay.cross_chain import CrossChainRouter
    from iagent_pay.invoice_manager import InvoiceManager
    from iagent_pay.marketplace_bridge import MarketplaceBridge
    from iagent_pay.yield_protocols import YieldManager
except ImportError as e:
    print(f"Error importing iAgentPay modules: {e}")
    exit(1)

# Metrics global tracker
metrics = {
    "total_actions": 0,
    "success": 0,
    "errors_rpc_rate_limit": 0,
    "errors_logic": 0,
    "errors_timeout": 0,
    "duration_total": 0.0,
    "start_time": time.time(),
}
metrics_lock = threading.Lock()

def record_metric(status: str, duration: float, error_type: str = None):
    with metrics_lock:
        metrics["total_actions"] += 1
        metrics["duration_total"] += duration
        if status == "success":
            metrics["success"] += 1
        elif status == "error":
            if error_type == "rate_limit":
                metrics["errors_rpc_rate_limit"] += 1
            elif error_type == "timeout":
                metrics["errors_timeout"] += 1
            else:
                metrics["errors_logic"] += 1

class BotWorker:
    def __init__(self, bot_id: int, persona: str, end_time: float):
        self.bot_id = bot_id
        self.persona = persona
        self.end_time = end_time
        
        # Instantiate agent instances per thread (Thread-safe usage)
        self.agent = AgentPay(chain_name="SEPOLIA")
        self.swap = SwapEngine(self.agent)
        self.cross = CrossChainRouter()
        self.invoice = InvoiceManager(self.agent)
        self.marketplace = MarketplaceBridge(self.agent)
        self.yield_mgr = YieldManager(self.agent)

    def run(self):
        while time.time() < self.end_time:
            # Spread load: Random sleep between 10 to 60 seconds
            time.sleep(random.uniform(10.0, 60.0))
            
            if time.time() >= self.end_time:
                break
                
            start_t = time.time()
            try:
                self.perform_action()
                record_metric("success", time.time() - start_t)
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg:
                    record_metric("error", time.time() - start_t, "rate_limit")
                elif "timeout" in err_msg:
                    record_metric("error", time.time() - start_t, "timeout")
                else:
                    # Treat generic exceptions (like connection drops, etc) as logic/network
                    record_metric("error", time.time() - start_t, "logic")
                
                # Exponential backoff on rate limits
                time.sleep(random.uniform(5.0, 15.0))

    def perform_action(self):
        # Choose action based on persona
        if self.persona == "Passive":
            # Just check balance and price
            self.agent.get_balance()
            self.agent.pricing.get_eth_price()
        
        elif self.persona == "DeFi":
            # Auto-invest / Yield
            self.yield_mgr.enable("aave")
            self.yield_mgr.auto_invest("USDC", 100.0, 20.0)
            # Swap
            if random.random() > 0.5:
                self.swap.get_quote("ETH", "USDC", 0.01)
                
        elif self.persona == "Escrow":
            # Escrows & Bounties
            bounty_id = self.marketplace.post_bounty(f"Task from bot {self.bot_id}", 15.0)
            self.marketplace.list_my_bounties()
            
        elif self.persona == "CrossChain":
            # Cross-chain quoting and intents
            self.cross.quote("SOLANA_DEVNET", "BASE_SEPOLIA", 10.0)
            
        elif self.persona == "Invoice":
            # AIP-1 Invoice parsing
            inv_str = self.invoice.create_invoice(5.0, "USDC", "BASE", "Test Invoice")
            self.invoice.parse_invoice(inv_str)
            
        elif self.persona == "Chaos_Mix":
            # Combine everything in one massive sequence
            self.agent.get_balance()
            if random.random() > 0.5:
                self.yield_mgr.enable("aave")
                self.yield_mgr.auto_invest("USDC", 10.0, 5.0)
            if random.random() > 0.5:
                self.swap.get_quote("ETH", "USDC", 0.01)
            b_id = self.marketplace.post_bounty(f"Chaos Task {self.bot_id}", 5.0)
            self.cross.quote("SOL_DEVNET", "SEPOLIA", 5.0)
            self.invoice.create_invoice(1.0, "USDC", "BASE", "Chaos")

def status_printer(end_time: float):
    """Prints status every 60 seconds."""
    while time.time() < end_time:
        with metrics_lock:
            act = metrics["total_actions"]
            succ = metrics["success"]
            rl = metrics["errors_rpc_rate_limit"]
            log = metrics["errors_logic"]
            avg_time = (metrics["duration_total"] / act) if act > 0 else 0
            
            elapsed = time.time() - metrics["start_time"]
            print(f"[{elapsed:.0f}s elapsed] Actions: {act} | Success: {succ} | RateLimits: {rl} | LogicErrs: {log} | AvgResp: {avg_time:.3f}s")
        time.sleep(60.0)

def main():
    DURATION = 7200 # 2 hours
    NUM_BOTS = 300
    
    print(f"🚀 Starting Stress Test: {NUM_BOTS} bots for {DURATION} seconds.")
    end_time = time.time() + DURATION
    
    personas = ["Passive", "DeFi", "Escrow", "CrossChain", "Invoice", "Chaos_Mix"]
    
    # Start status thread
    threading.Thread(target=status_printer, args=(end_time,), daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=NUM_BOTS) as executor:
        for i in range(NUM_BOTS):
            persona = random.choice(personas)
            worker = BotWorker(i, persona, end_time)
            executor.submit(worker.run)
            
            # Stagger startup to avoid instant RPC nuke
            time.sleep(0.1)
            
    print("\n✅ Stress Test Completed!")
    with metrics_lock:
        print(json.dumps(metrics, indent=4))
        with open("stress_metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)

if __name__ == "__main__":
    main()
