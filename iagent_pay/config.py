import os

class ChainConfig:
    """
    Pre-configured settings for major AI-friendly blockchains.
    """
    LOCAL = {
        "name": "Local Testnet",
        "rpc": None, 
        "chain_id": 1337,
        "symbol": "ETH"
    }

    ETH = {
        "name": "Ethereum Mainnet",
        "rpc": [os.getenv("ETH_RPC_URL", "https://cloudflare-eth.com"), "https://rpc.ankr.com/eth"],
        "chain_id": 1,
        "symbol": "ETH"
    }
    
    SEPOLIA = {
        "name": "Sepolia Testnet",
        "rpc": ["https://ethereum-sepolia-rpc.publicnode.com", "https://sepolia.drpc.org"],
        "chain_id": 11155111,
        "symbol": "SepoliaETH"
    }
    
    BASE_MAINNET = {
        "name": "Base (Coinbase)",
        "rpc": ["https://mainnet.base.org", "https://base.llamarpc.com", "https://1rpc.io/base"],
        "chain_id": 8453,
        "symbol": "ETH"
    }
    
    BNB = {
        "name": "BNB Smart Chain",
        "rpc": ["https://bsc-dataseed.binance.org", "https://bsc-dataseed1.defibit.io"],
        "chain_id": 56,
        "symbol": "BNB"
    }
    
    POLYGON = {
        "name": "Polygon PoS",
        "rpc": ["https://polygon.drpc.org", "https://rpc.ankr.com/polygon"],
        "chain_id": 137,
        "symbol": "MATIC"
    }

    # Solana Configs (Handled by SolanaDriver)
    SOL_MAINNET = {
        "name": "Solana Mainnet",
        "rpc": [os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"), "https://solana-mainnet.g.allthatnode.com", "https://api.tatum.io/v3/solana/node/mainnet-beta"],
        "chain_id": None, 
        "symbol": "SOL"
    }
    
    SOL_DEVNET = {
        "name": "Solana Devnet",
        "rpc": "https://api.devnet.solana.com",
        "chain_id": None, 
        "symbol": "SOL"
    }

    XRP_TESTNET = {
        "name": "XRP Ledger Testnet",
        "rpc": "https://s.altnet.rippletest.net:51234",
        "chain_id": None,
        "symbol": "XRP"
    }

    # Aliases
    BASE = BASE_MAINNET
    SOLANA = SOL_MAINNET
    XRP = XRP_TESTNET

    @staticmethod
    def get_network(name: str):
        """Returns the config dict for the requested network."""
        name = name.upper()
        if hasattr(ChainConfig, name):
            return getattr(ChainConfig, name)
        raise ValueError(f"Unknown network: {name}")
