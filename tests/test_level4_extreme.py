import unittest
import json
import os
from iagent_pay.agent_pay import AgentPay

class TestLevel4Extreme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AgentPay(chain_name="SEPOLIA")

    def test_replay_attack_prevention(self):
        print("\n[Level 4] Testing Replay Attack Prevention...")
        inv_id = "test_replay_a1"
        invoice = {
            "invoice_id": inv_id,
            "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "amount": 0.0001,
            "currency": "ETH",
            "chain": "SEPOLIA"
        }
        inv_json = json.dumps(invoice)
        
        # First payment (we won't actually send tx if we don't have funds, but the logic should trigger)
        # Let's mock _mark_invoice_paid to simulate a previous payment
        self.agent._mark_invoice_paid(inv_id, invoice['recipient'], invoice['amount'])
        
        # Attempt second payment
        result = self.agent.pay_invoice(inv_json)
        self.assertEqual(result, "ALREADY_PAID")
        print("✅ Replay Attack Blocked (AIP-1 Compliance)")

    def test_malformed_invoice_json(self):
        print("\n[Level 4] Testing Malformed JSON robustness...")
        malformed = "{ 'missing': 'quotes', 'broken' }"
        with self.assertRaises(ValueError) as cm:
            self.agent.pay_invoice(malformed)
        self.assertIn("Invalid Invoice JSON", str(cm.exception))
        
        missing_fields = json.dumps({"invoice_id": "123", "amount": 1.0})
        with self.assertRaises(ValueError) as cm:
            self.agent.pay_invoice(missing_fields)
        self.assertIn("Missing required field", str(cm.exception))
        print("✅ Malformed JSON Handled Gracefully")

    def test_network_failure_handling(self):
        print("\n[Level 4] Testing Network Failure Resilience...")
        # Point to a dead/invalid RPC
        agent_dead = AgentPay(chain_name="ETH")
        # Mocking the RPC to a dead one manually
        from web3 import Web3
        agent_dead.w3 = Web3(Web3.HTTPProvider("http://localhost:1234")) # Dead port
        
        with self.assertRaises(Exception):
            agent_dead.pay_agent("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 0.0001)
        print("✅ Graceful Fail on RPC Connection Issue")

if __name__ == "__main__":
    unittest.main()
