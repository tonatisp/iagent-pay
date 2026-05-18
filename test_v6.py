import time
import logging
from typing import Callable
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format="%(message)s")

def run_test(name: str, test_func: Callable):
    try:
        test_func()
        print(f"  [PASS] {name}")
    except AssertionError as e:
        print(f"  [FAIL] {name}: Assertion Failed: {e}")
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__}: {e}")

print("\nStarting iAgentPay v6.0 Phase 6 Tests...\n")
print("============================================================")
print("  iAgentPay v6.0 TEST SUITE RESULTS")
print("============================================================")

def test_data_marketplace():
    from iagent_pay.data_marketplace import get_marketplace, DataProvider
    
    marketplace = get_marketplace()
    # It should have 3 seeded providers
    assert len(marketplace.list_all()) >= 3, "Seed providers missing"
    
    provider = marketplace.find_best_provider("weather")
    assert provider is not None, "Weather provider not found"
    assert provider.name == "CheapWeather", f"Expected CheapWeather, got {provider.name}"
    
    none_provider = marketplace.find_best_provider("nonexistent")
    assert none_provider is None, "Found provider for nonexistent type"

run_test("Data Marketplace: Registry and Discovery", test_data_marketplace)


def test_cross_chain():
    from iagent_pay.cross_chain import CrossChainRouter
    
    router = CrossChainRouter(fee_percentage=1.0)
    quote = router.quote("SOLANA_MAINNET", "BASE_MAINNET", 10.0)
    
    assert quote["bridge_fee_usd"] == 0.1, "Fee calculation wrong"
    assert quote["total_source_usd"] == 10.1, "Total calculation wrong"
    
    result = router.pay_cross_chain("0x123", "SOLANA_MAINNET", "BASE_MAINNET", "0xabc", 10.0)
    assert result["status"] == "success", "Cross chain failed"
    assert "cross_chain_tx_id" in result, "No tx id"

run_test("Cross-Chain: Routing and Fee Calculation", test_cross_chain)


def test_paymaster():
    from iagent_pay.usdc_driver import USDCDriver
    
    driver = USDCDriver(network="BASE_SEPOLIA")
    # Simulate a gasless transaction
    result = driver.sponsor_gas("0x" + "a"*64, "0xRecipient", 5.0)
    
    assert result["status"] == "success", "Sponsored tx failed"
    assert "sponsored" in result["tx_hash"], "Not a sponsored tx hash"
    assert result["gas_paid_by"] == "iAgentPay_Paymaster", "Paymaster not credited"

run_test("USDC Driver: Gasless Paymaster Support", test_paymaster)


def test_onchain_kya():
    from iagent_pay.kya import AgentIdentity, KYARegistry, TrustLevel
    
    reg = KYARegistry()
    id1 = AgentIdentity.create('EliteBot', '0xOwner', ['trading'])
    reg.register(id1)
    
    # Push agent to ELITE
    for _ in range(55):
        reg.update_after_payment(id1.did, True, 20.0)
        
    assert reg.get_trust_level(id1.did) == TrustLevel.ELITE, "Did not reach ELITE"
    
    # Check if SBT credential was issued
    agent = reg.resolve(id1.did)
    creds = agent.get_valid_credentials()
    
    sbt_cred = next((c for c in creds if c.credential_type == "OnChainIdentitySBT"), None)
    assert sbt_cred is not None, "SBT Credential not issued"
    assert "tx_hash" in sbt_cred.claims, "SBT missing tx_hash"

run_test("KYA: On-Chain SBT Minting for ELITE", test_onchain_kya)


def test_x402_marketplace_client():
    from iagent_pay.x402_client import X402Client
    
    client = X402Client(private_key="0xabc", max_amount_usdc=5.0)
    
    # We mock the internal requests to avoid actual HTTP calls during unit test
    import requests
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.HTTPError()

    def mock_get(url, **kwargs):
        return MockResponse({"data": "weather is nice", "from": url})
        
    client.get = mock_get
    
    data = client.fetch_data("weather")
    assert data["data"] == "weather is nice", "Data fetch failed"
    assert "api.cheapweather.net" in data["from"], "Did not use the marketplace url"

run_test("x402 Client: Data Marketplace autonomous fetch", test_x402_marketplace_client)

print("============================================================")
