import unittest
import os
import json
from iagent_pay.agent_pay import AgentPay

class TestLevel6Hardening(unittest.TestCase):
    def setUp(self):
        # Cleanup
        for db in ["agent_reputation.db", "agent_history.db", "agent_marketplace.db", "test_export.json"]:
            if os.path.exists(db):
                try: os.remove(db)
                except: pass
        self.agent = AgentPay(chain_name="SEPOLIA")

    def test_rpc_fallback_trigger(self):
        """Verifies that rotate_rpc works without crashing."""
        print("\n[Level 6] 📡 Testing RPC Rotation...")
        old_rpc = self.agent.rpc_pool[self.agent.current_rpc_index]
        self.agent.rotate_rpc()
        new_rpc = self.agent.rpc_pool[self.agent.current_rpc_index]
        self.assertNotEqual(old_rpc, new_rpc)
        print(f"✅ RPC Rotated successfully: {new_rpc}")

    def test_state_portability(self):
        """Verifies Export -> Import flow."""
        print("\n[Level 6] 📦 Testing State Portability...")
        # 1. Create mock data
        self.agent.rate_agent("0xTEST", 4.5)
        
        # 2. Export
        export_file = self.agent.export_state("test_export.json")
        self.assertTrue(os.path.exists(export_file))
        
        # 3. Create fresh agent and import
        os.remove("agent_reputation.db") # Simulate loss
        fresh_agent = AgentPay(chain_name="SEPOLIA")
        self.assertEqual(fresh_agent.get_trust_score("0xTEST"), 3.0) # Confirm loss (Neutral)
        
        fresh_agent.import_state(export_file)
        
        # 4. Verify
        self.assertEqual(fresh_agent.get_trust_score("0xTEST"), 4.5)
        print("✅ State Portability Verified (Export/Import Works).")

    def test_defi_safety_check(self):
        """Verifies that DeFi safety check runs."""
        print("\n[Level 6] 🏦 Testing DeFi Safety Guard...")
        # We simulate a "dead" provider/network by breaking w3 temporarily 
        original_w3 = self.agent.w3
        self.agent.w3 = None # Force failure
        
        # Should catch exception and return False in _check_protocol_health
        is_safe = self.agent.yield_manager._check_protocol_health()
        self.assertFalse(is_safe)
        
        self.agent.w3 = original_w3 # Restore
        print("✅ DeFi Safety Guard correctly blocked unsafe environment.")

if __name__ == "__main__":
    unittest.main()
