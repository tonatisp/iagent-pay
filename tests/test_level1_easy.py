import os
import unittest
from iagent_pay.agent_pay import AgentPay

class TestLevel1Easy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(f"\nDEBUG: Importing AgentPay from {AgentPay.__module__}")
        print(f"DEBUG: Attributes: {[m for m in dir(AgentPay) if not m.startswith('__')]}")
        # Clear existing DBs for clean test state
        for db in ["agent_reputation.db", "agent_history.db", "agent_marketplace.db"]:
            if os.path.exists(db):
                os.remove(db)
        
        # We use SEPOLIA for EVM tests as it's a testnet
        cls.agent_evm = AgentPay(chain_name="SEPOLIA")
        # We use SOL_DEVNET for Solana tests
        cls.agent_sol = AgentPay(chain_name="SOL_DEVNET")

    def test_wallet_generation(self):
        print("\n[Level 1] Testing Wallet Generation...")
        self.assertIsNotNone(self.agent_evm.my_address)
        self.assertTrue(self.agent_evm.my_address.startswith("0x"))
        self.assertIsNotNone(self.agent_sol.my_address)
        print(f"✅ EVM: {self.agent_evm.my_address}")
        print(f"✅ SOL: {self.agent_sol.my_address}")

    def test_invoice_system(self):
        print("\n[Level 1] Testing Invoice System...")
        invoice_json = self.agent_evm.create_invoice(
            amount=0.001,
            currency="ETH",
            chain="SEPOLIA",
            description="Test Invoice"
        )
        import json
        invoice = json.loads(invoice_json)
        self.assertIn("invoice_id", invoice)
        self.assertIn("amount", invoice)
        print(f"✅ Invoice Created: {invoice['invoice_id']}")

    def test_reputation_system(self):
        print("\n[Level 1] Testing Reputation System...")
        peer = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.agent_evm.rate_agent(peer, 5.0)
        score = self.agent_evm.get_trust_score(peer)
        self.assertEqual(score, 5.0)
        print(f"✅ Peer {peer} Rated 5.0")

    def test_marketplace_bridge(self):
        print("\n[Level 1] Testing Marketplace Bridge...")
        bounty_id = self.agent_evm.post_bounty("Easy Task", 1.0)
        self.assertIsNotNone(bounty_id)
        bounties = self.agent_evm.marketplace.list_my_bounties()
        found = any(b['id'] == bounty_id for b in bounties)
        self.assertTrue(found)
        print(f"✅ Bounty {bounty_id} Posted and Listed")

    def test_defi_enable(self):
        print("\n[Level 1] Testing DeFi Integration Enablement...")
        # Aave is Base-specific in our current impl
        agent_base = AgentPay(chain_name="BASE")
        agent_base.enable_auto_yield(protocol="aave")
        self.assertTrue(agent_base.yield_manager.active)
        self.assertEqual(agent_base.yield_manager.protocol, "aave")
        print("✅ DeFi Auto-Yield Enabled")

if __name__ == "__main__":
    unittest.main()
