from typing import Dict

# Standard ERC-20 ABI (Minimal for Transfer & Balance)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Official USDC Addresses (Native where available)
TOKEN_ADDRESSES = {
    "ETH": {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (Native)
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7"   # USDT
    },
    "BASE": {
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"   # USDC (Native)
    },
    "POLYGON": {
        "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # USDC (Native)
        # Note: Validated as Circle's official native USDC on Polygon
    },
    "ARBITRUM": {
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"   # USDC (Native)
    },
    "SEPOLIA": {
        "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"   # Testnet USDC
    },
    "LOCAL": {
        # For testing, we usually deploy a mock token.
        # Leaving empty for now.
    }
}
