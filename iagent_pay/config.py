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
        "rpc": "https://eth.llamarpc.com",
        "chain_id": 1,
        "symbol": "ETH"
    }
    
    SEPOLIA = {
        "name": "Sepolia Testnet",
        "rpc": "https://1rpc.io/sepolia",
        "chain_id": 11155111,
        "symbol": "SepoliaETH"
    }
    
    BASE_MAINNET = {
        "name": "Base (Coinbase)",
        "rpc": "https://mainnet.base.org",
        "chain_id": 8453,
        "symbol": "ETH"
    }
    
    POLYGON = {
        "name": "Polygon PoS",
        "rpc": "https://polygon-rpc.com",
        "chain_id": 137,
        "symbol": "MATIC"
    }

    # Solana Configs (Handled by SolanaDriver, but added here for validator)
    SOL_MAINNET = {
        "name": "Solana Mainnet",
        "rpc": "https://api.mainnet-beta.solana.com",
        "chain_id": None, # SVM 
        "symbol": "SOL"
    }
    
    SOL_DEVNET = {
        "name": "Solana Devnet",
        "rpc": "https://api.devnet.solana.com",
        "chain_id": None, 
        "symbol": "SOL"
    }

    @staticmethod
    def get_network(name: str):
        """Returns the config dict for the requested network."""
        name = name.upper()
        if hasattr(ChainConfig, name):
            return getattr(ChainConfig, name)
        raise ValueError(f"Unknown network: {name}")
