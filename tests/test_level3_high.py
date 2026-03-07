import unittest
import time
from iagent_pay.agent_pay import AgentPay

class TestLevel3High(unittest.TestCase):
    def setUp(self):
        import os
        if os.path.exists("agent_reputation.db"):
            os.remove("agent_reputation.db")

    def test_reputation_spam_protection(self):
        print("\n[Level 3] Testing Reputation Spam Resilience...")
        agent = AgentPay(chain_name="SEPOLIA")
        peer = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        
        # Rate same peer many times
        for i in range(10):
            agent.rate_agent(peer, 1.0 if i % 2 == 0 else 5.0)
            
        score = agent.get_trust_score(peer)
        # Result should be average (3.0)
        self.assertTrue(2.9 <= score <= 3.1, f"Expected ~3.0, got {score}")
        print(f"✅ Reputation Averaging Works: Final Score {score}")

    def test_rapid_chain_switching(self):
        print("\n[Level 3] Testing Rapid Chain Switching...")
        chains = ["BASE", "POLYGON", "SEPOLIA"]
        for c in chains:
            print(f"🔄 Switching to {c}...")
            agent = AgentPay(chain_name=c)
            self.assertEqual(agent.chain_name, c)
            self.assertIsNotNone(agent.w3)
        print("✅ Success: Multi-engine switching stable")

    def test_nonce_concurrency_safe(self):
        print("\n[Level 3] Testing Nonce Management Logic...")
        agent = AgentPay(chain_name="SEPOLIA")
        # We won't actually send transactions to avoid spending testnet ETH in a loop,
        # but we can verify that _get_nonce increments or stays consistent.
        n1 = agent._get_nonce()
        time.sleep(0.1)
        n2 = agent._get_nonce()
        self.assertEqual(n1, n2) # Should be same if no tx sent
        print(f"✅ Nonce consistency verified: {n1}")

if __name__ == "__main__":
    unittest.main()
