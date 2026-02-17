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

    def get_config(self) -> Dict[str, Any]:
        """Returns the current configuration, refreshing if necessary."""
        current_time = time.time()
        
        # Check if cache is expired
        if current_time - self.last_updated > self.cache_ttl:
            print("🔄 Refreshing pricing config...")
            self._refresh_config()
            
        return self.cached_config

    def _refresh_config(self):
        """Fetches the latest config from Remote URL or Local File."""
        # 1. Try Local File Override (Simulating Remote for MVP)
        if os.path.exists(self.local_override_path):
            try:
                with open(self.local_override_path, 'r') as f:
                    self.cached_config = json.load(f)
                self.last_updated = time.time()
                print("✅ Config updated from local file.")
                return
            except Exception as e:
                print(f"⚠️ Failed to read local config: {e}")

        # 2. Try Remote URL (if configured)
        if self.config_url:
            try:
                with urllib.request.urlopen(self.config_url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    self.cached_config = data
                self.last_updated = time.time()
                print("✅ Config updated from Remote URL.")
                return
            except Exception as e:
                print(f"⚠️ Failed to reach remote config: {e}. Using cached/default.")
        
        # If both fail, we stick with what we have (Graceful Degradation)
