import requests
import base64
import json

def get_jupiter_quote(input_mint, output_mint, amount, slippage_bps=50):
    """
    Fetches a quote from Jupiter Aggregator (Solana).
    """
    # url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={slippage_bps}"
    # Alternative / Proxy
    url = f"https://api.jup.ag/swap/v1/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps={slippage_bps}"
    try:
        print(f"   Derived URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return {"error": str(e)}

def main():
    print("--- 🪐 Jupiter Swap Prototype ---")
    
    # 1. Define Mints
    SOL_MINT = "So11111111111111111111111111111111111111112"
    BONK_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    
    # 2. Get Quote (0.01 SOL -> BONK)
    amount_lamports = int(0.01 * 1e9) # 0.01 SOL
    print(f"🔍 Fetching Quote for {amount_lamports} Lamports (SOL -> BONK)...")
    
    quote = get_jupiter_quote(SOL_MINT, BONK_MINT, amount_lamports)
    
    if "error" in quote:
        print(f"❌ Quote Failed: {quote}")
        return

    out_amount = int(quote.get("outAmount"))
    print(f"✅ Quote Received!")
    print(f"   In:  0.01 SOL")
    print(f"   Out: {out_amount / 1e5:.2f} BONK (Approx)")
    print(f"   Route: {len(quote.get('routePlan', []))} hops")
    
    # Note: We can't execute the swap without a signed transaction, 
    # but successfully getting a quote proves integration is possible.

if __name__ == "__main__":
    main()
