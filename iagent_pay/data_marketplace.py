"""
iAgentPay — Data Marketplace
Decentralized registry of premium data providers for AI agents.
Integrates with x402 protocol for automatic negotiation and payment.

Usage:
    from iagent_pay.data_marketplace import DataMarketplace, DataProvider

    marketplace = DataMarketplace()
    
    # Providers register their endpoints
    marketplace.register(DataProvider(
        name="WeatherPro",
        data_type="weather",
        url="https://api.weatherpro.com/v1/data",
        price_usdc=0.05,
        trust_score=98.5
    ))

    # Agents search for data
    provider = marketplace.find_best_provider("weather")
    print(provider.url)
"""
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger("iagentpay.marketplace")

@dataclass
class DataProvider:
    name: str
    data_type: str              # e.g., "weather", "crypto_price", "news"
    url: str                    # Endpoint that supports HTTP 402
    price_usdc: float           # Advertised price per request
    trust_score: float = 50.0   # 0 to 100
    latency_ms: int = 200       # Average response time
    wallet_address: str = ""    # Optional: directly known wallet address

    def get_value_score(self) -> float:
        """Calculate a value score based on trust, price, and latency (higher is better)."""
        if self.price_usdc <= 0:
            return 0.0
        # Formula: (Trust / Price) - penalty for latency
        return (self.trust_score / self.price_usdc) - (self.latency_ms * 0.01)

class DataMarketplace:
    """
    On-memory registry of x402-enabled API providers.
    In production, this could be backed by a Smart Contract registry.
    """
    def __init__(self):
        self._providers: List[DataProvider] = []

    def register(self, provider: DataProvider):
        """Register a new API provider in the marketplace."""
        self._providers.append(provider)
        logger.info(f"[Marketplace] Registered provider '{provider.name}' for type '{provider.data_type}' at ${provider.price_usdc}")

    def find_best_provider(self, data_type: str, max_price_usd: float = 1.0) -> Optional[DataProvider]:
        """
        Find the best provider for a specific data type based on the value score.
        Filters out providers exceeding the max_price_usd.
        """
        candidates = [
            p for p in self._providers 
            if p.data_type.lower() == data_type.lower() and p.price_usdc <= max_price_usd
        ]
        
        if not candidates:
            logger.warning(f"[Marketplace] No providers found for '{data_type}' under ${max_price_usd}")
            return None

        # Sort by value score descending
        candidates.sort(key=lambda p: p.get_value_score(), reverse=True)
        best = candidates[0]
        
        logger.info(f"[Marketplace] Selected best provider: {best.name} (Score: {best.get_value_score():.2f})")
        return best

    def search(self, query: str) -> List[DataProvider]:
        """Simple text search across provider names and data types."""
        q = query.lower()
        return [
            p for p in self._providers 
            if q in p.name.lower() or q in p.data_type.lower()
        ]

    def list_all(self) -> List[dict]:
        """Returns all providers in a dictionary format."""
        return [
            {
                "name": p.name,
                "data_type": p.data_type,
                "url": p.url,
                "price_usdc": p.price_usdc,
                "trust_score": p.trust_score
            } for p in self._providers
        ]

# Global singleton
_global_marketplace: Optional[DataMarketplace] = None

def get_marketplace() -> DataMarketplace:
    global _global_marketplace
    if _global_marketplace is None:
        _global_marketplace = DataMarketplace()
        # Seed with some mock providers
        _global_marketplace.register(DataProvider("WeatherPro", "weather", "https://api.weatherpro.com/v1", 0.05, 95.0))
        _global_marketplace.register(DataProvider("CheapWeather", "weather", "https://api.cheapweather.net", 0.01, 60.0, 800))
        _global_marketplace.register(DataProvider("FinData", "crypto", "https://api.findata.io/v2", 0.10, 99.0))
    return _global_marketplace
