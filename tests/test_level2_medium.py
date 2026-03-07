import unittest
import os
from iagent_pay.agent_pay import AgentPay

class TestLevel2Medium(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We use SEPOLIA for EVM tests
        cls.agent = AgentPay(chain_name="SEPOLIA")

    def test_gas_guardrail(self):
        print("\n[Level 2] Testing Gas Guardrail...")
        # Set a ridiculously low gas price limit (0.01 Gwei)
        with self.assertRaises(ValueError) as cm:
            self.agent.pay_agent("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 0.0001, max_gas_gwei=0.01)
        self.assertIn("exceeds limit", str(cm.exception))
        print("✅ Gas Guardrail Blocked Underpriced Tx")

    def test_daily_limit_native(self):
        print("\n[Level 2] Testing Daily Limit (Circuit Breaker)...")
        # Set limit to a tiny amount
        self.agent.set_daily_limit(0.0000001)
        try:
            with self.assertRaises(ValueError) as cm:
                self.agent.pay_agent("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 0.1)
            self.assertIn("Daily Spending Limit Exceeded", str(cm.exception))
            print("✅ Daily Limit Circuit Breaker Active")
        finally:
            # Reset limit
            self.agent.set_daily_limit(10.0)

    def test_invalid_recipient_address(self):
        print("\n[Level 2] Testing Invalid Recipient...")
        with self.assertRaises(ValueError) as cm:
            self.agent.pay_agent("invalid_address", 0.1)
        # Check for either social resolver fail or web3 address fail
        error_msg = str(cm.exception)
        self.assertTrue("Could not resolve social handle" in error_msg or "Invalid recipient address" in error_msg)
        print("✅ Invalid Recipient Detected")

    def test_insufficient_funds(self):
        print("\n[Level 2] Testing Insufficient Funds (EVM)...")
        # Attempt to send 1,000,000 ETH on Sepolia
        with self.assertRaises(Exception): # Web3 raises various errors for balance
            self.agent.pay_agent("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 1000000.0)
        print("✅ Insufficient Funds Handled")

    def test_yield_harvest_error_handling(self):
        print("\n[Level 2] Testing Yield Harvest Error Handling...")
        # Enable but simulate a failure or just check it doesn't crash
        self.agent.enable_auto_yield(protocol="aave")
        # harvest_yield has a try/except, it should just print a warning if RPC fails
        # but in our test it might actually "succeed" if RPC is fine but contract isn't there
        self.agent.harvest_yield()
        print("✅ Yield Harvest Graceful Error Handling")

if __name__ == "__main__":
    unittest.main()
