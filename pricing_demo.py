import time
import json
from iagent_pay import PricingManager

def demo_dynamic_pricing():
    print("💸 Dynamic Pricing Demo")
    print("=======================")
    
    # 1. Create a "remote" config file locally
    initial_config = {
        "trial_days": 30,
        "subscription_price_eth": 0.05
    }
    with open("pricing_config.json", "w") as f:
        json.dump(initial_config, f)
        
    # Initialize Manager with short TTL for demo
    pm = PricingManager(cache_ttl_seconds=2)
    
    print(f"🔹 T=0s: Price is {pm.get_config()['subscription_price_eth']} ETH")
    
    # 2. Simulate User keeping app open...
    print("⏳ App running... (User is idle)")
    time.sleep(3) 
    
    # 3. ADMIN (You) changes price remotely
    print("\n👑 ADMIN: Updating price to 0.10 ETH...")
    new_config = {
        "trial_days": 15,
        "subscription_price_eth": 0.10
    }
    with open("pricing_config.json", "w") as f:
        json.dump(new_config, f)
        
    # 4. User tries to buy again
    print("\n🔹 T=3s: User checks price again...")
    current_price = pm.get_config()['subscription_price_eth']
    print(f"💰 New Price Detected: {current_price} ETH")
    
    if current_price == 0.10:
        print("✅ SUCCESS: App detected price change without restart!")
    else:
        print("❌ FAILED: App used stale price.")

if __name__ == "__main__":
    demo_dynamic_pricing()
