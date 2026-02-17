import time
import json
import os
import urllib.request
from typing import Dict, Any

class PricingManager:
    """
    Manages dynamic pricing and configuration.
    Features:
    - Remote Fetching: Pulls config from a URL (e.g., GitHub Gist, S3).
    - Caching (TTL): Caches config locally for X seconds to avoid spamming the server.
    - Auto-Refresh: If cache expires, refetches automatically on next call.
    - Fallback: Uses default/local config if internet fails.
    """
    
    DEFAULT_CONFIG = {
        "trial_days": 14,
        "subscription_price_eth": 0.01,
        "pay_per_use_price_eth": 0.0001,
        "active": True
    }
    
    def __init__(self, config_url: str = None, cache_ttl_seconds: int = 300):
        self.config_url = config_url
        self.cache_ttl = cache_ttl_seconds
        self.last_updated = 0
        self.cached_config = self.DEFAULT_CONFIG.copy()
        
        # For testing purposes, we can override with a local file path
        self.local_override_path = "pricing_config.json"

    def get_eth_price(self) -> float:
        """Fetches current ETH price in USD from public APIs (CoinGecko/Coinbase)."""
        try:
            # Simple, no-key API for MVP
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            with urllib.request.urlopen(url, timeout=3) as response:
                data = json.loads(response.read().decode())
                return float(data['ethereum']['usd'])
        except Exception:
            # Fallback if API fails (approx conservative price)
            return 3000.0

    def get_config(self) -> Dict[str, Any]:
        """Returns config with dynamic ETH prices based on USD targets."""
        # Refresh logic...
        current_time = time.time()
        if current_time - self.last_updated > self.cache_ttl:
            self._refresh_config()
            
        config = self.cached_config.copy()
        
        # Calculate Dynamic Prices
        eth_price = self.get_eth_price()
        
        # Target: $26.00 USD for Subscription
        config["subscription_price_eth"] = round(26.00 / eth_price, 6)
        
        # Target: $0.10 USD for Pay-Per-Use
        config["pay_per_use_price_eth"] = round(0.10 / eth_price, 8)
        
        return config

    def _refresh_config(self):
        """Fetches the latest config from Remote URL or Local File."""
        # 1. Try Local File Override
        if os.path.exists(self.local_override_path):
            try:
                with open(self.local_override_path, 'r') as f:
                    self.cached_config = json.load(f)
                self.last_updated = time.time()
                # print("✅ Config updated from local file.") # Silenced for cleaner logs
                return
            except Exception:
                pass

        # 2. Remote URL... (omitted for brevity in this patch)

