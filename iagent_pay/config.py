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
        "rpc": [os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"), "https://1rpc.io/eth", "https://rpc.ankr.com/eth"],
        "chain_id": 1,
        "symbol": "ETH"
    }
    
    SEPOLIA = {
        "name": "Sepolia Testnet",
        "rpc": ["https://1rpc.io/sepolia", "https://rpc.ankr.com/eth_sepolia", "https://eth-sepolia.public.blastapi.io"],
        "chain_id": 11155111,
        "symbol": "SepoliaETH"
    }
    
    BASE_MAINNET = {
        "name": "Base (Coinbase)",
        "rpc": ["https://mainnet.base.org", "https://base.llamarpc.com", "https://1rpc.io/base"],
        "chain_id": 8453,
        "symbol": "ETH"
    }
    
    POLYGON = {
        "name": "Polygon PoS",
        "rpc": ["https://polygon-rpc.com", "https://polygon.llamarpc.com", "https://1rpc.io/polygon"],
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

    # Aliases
    BASE = BASE_MAINNET
    SOLANA = SOL_MAINNET

    @staticmethod
    def get_network(name: str):
        """Returns the config dict for the requested network."""
        name = name.upper()
        if hasattr(ChainConfig, name):
            return getattr(ChainConfig, name)
        raise ValueError(f"Unknown network: {name}")
