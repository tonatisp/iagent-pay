import unittest
import os
import sqlite3
from iagent_pay.agent_pay import AgentPay

class TestV3_6Expansion(unittest.TestCase):
    def setUp(self):
        # Cleanup
        for db in ["agent_reputation.db", "agent_history.db", "agent_marketplace.db"]:
            if os.path.exists(db):
                try: os.remove(db)
                except: pass
        self.agent = AgentPay(chain_name="SEPOLIA")
        self.trusted_peer = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    def test_trust_based_discount(self):
        """
        Tests if the Trust-Based Pricing applies a discount correctly.
        """
        print("\n[v3.6] 💎 Testing Trust-Based Discounts...")
        
        # 1. Rate the peer highly (5.0)
        self.agent.rate_agent(self.trusted_peer, 5.0)
        self.assertEqual(self.agent.get_trust_score(self.trusted_peer), 5.0)
        
        # 2. Create an invoice to this peer
        invoice = {
            "invoice_id": "INV_TRUST_001",
            "recipient": self.trusted_peer,
            "amount": 1.0,
            "currency": "ETH",
            "chain": "SEPOLIA"
        }
        
        # We mock pay_agent to avoid real network call but check the amount passed
        original_pay = self.agent.pay_agent
        intercepted_amount = 0
        def mock_pay(recipient, amount):
            nonlocal intercepted_amount
            intercepted_amount = amount
            return "0xMOCK_TX"
        
        self.agent.pay_agent = mock_pay
        
        # 3. Process invoice
        import json
        self.agent.pay_invoice(json.dumps(invoice))
        
        # 4. Verify discount (1.0 ETH -> 0.9 ETH due to 10% discount for score 5.0)
        self.assertAlmostEqual(intercepted_amount, 0.9)
        print(f"✅ Trust-Based Discount applied: 1.0 ETH -> {intercepted_amount} ETH")
        self.agent.pay_agent = original_pay

    def test_self_healing_pricing_trigger(self):
        """
        Tests if the PricingManager uses the on-chain fallback when REST APIs are broken.
        """
        print("\n[v3.6] ⚠️ Testing Self-Healing Pricing Fallback...")
        
        # We simulate rest failure by breaking urllib.request.urlopen
        import urllib.request
        original_open = urllib.request.urlopen
        
        def mock_open(url, timeout=None):
            raise Exception("Network Timeout (Simulated)")
            
        urllib.request.urlopen = mock_open
        
        # Fetch price
        price = self.agent.pricing.get_eth_price()
        
        # Verify it used the fallback (2500.0 from _fetch_onchain_fallback)
        self.assertEqual(price, 2500.0)
        print(f"✅ Self-Healing Pricing Fallback used: {price} USD")
        
        urllib.request.urlopen = original_open

if __name__ == "__main__":
    unittest.main()
