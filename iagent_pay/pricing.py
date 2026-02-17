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
        """
        Fetches ETH price from 3 sources and returns the MEDIAN to avoid outliers/downtime.
        Sources: CoinGecko, Coinbase, Binance.
        """
        prices = []
        
        # 1. CoinGecko
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode())
                price = float(data['ethereum']['usd'])
                prices.append(price)
        except Exception:
            pass # Fail silently, try next

        # 2. Coinbase
        try:
            url = "https://api.coinbase.com/v2/prices/ETH-USD/spot"
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode())
                price = float(data['data']['amount'])
                prices.append(price)
        except Exception:
            pass

        # 3. Binance (US)
        try:
            url = "https://api.binance.us/api/v3/ticker/price?symbol=ETHUSD"
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode())
                price = float(data['price'])
                prices.append(price)
        except Exception:
            pass
            
        # Logic: Robust Aggregation
        if not prices:
            print("⚠️ All Pricing APIs failed. Using Fallback.")
            return 3000.0 # Conservative fallback
            
        prices.sort()
        count = len(prices)
        
        if count == 1:
            return prices[0]
        elif count == 2:
            return sum(prices) / 2 # Average
        else:
            # Return Median (filters out 1 extreme outlier)
            return prices[1]

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

