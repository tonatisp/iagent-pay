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
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "EURC": "0x1aBaEA1f7C830bD89Acc67eC4af51629edBa8523",
        "CNHC": "0x8965349fb649a33a30cbfda057d8ec2c48abe2a2", # Chinese Yuan (Offshore)
        "GYEN": "0xC08512927D12348F6620a698105e1BAac6EcD911", # Japanese Yen
        "XSGD": "0x70e8de73ce538da2beed35d14187f6959a8eca96", # Singapore Dollar
        "CADC": "",  # Canadian Dollar — official ERC-20 not yet available on Ethereum Mainnet. Disabled.
        "MXNT": "0x1b4129bbdc257fc6cb21c000ff97cbf2585f6931", # Mexican Peso (Tether MXN)
        "PEPE": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
        "SHIB": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE"
    },
    "BASE": {
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDT": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
        "DAI": "0x50c57259f6a7627c2fd6a2b230745fcee4d0a917db0cb",
        "WETH": "0x4200000000000000000000000000000000000006",
        "EURC": "0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42",
        "BRETT": "0x532f27101965dd16442E59d40670FaF5eBB142E4",
        "DEGEN": "0x4ed4E862860beD51a9570b96d8014731D348F3F8",
        "TOSHI": "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4"
    },
    "POLYGON": {
        "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "DAI": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063",
        "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619"
    },
    "ARBITRUM": {
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "DAI": "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",
        "WETH": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
    },
    "BNB": {
        "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", # USDC-BEP20
        "USDT": "0x55d398326f99059fF775485246999027B3197955", # USDT-BEP20
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", # Binance USD
        "DAI": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3", # DAI-BEP20
        "WETH": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8", # ETH-BEP20 (Binance-Peg)
        "EURC": "" # Not officially supported on BNB yet
    },
    "SEPOLIA": {
        "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        "USDT": "0xaA8E23Fb1079EA71e0a56F48a2aA51851D8433D0",
        "DAI": "0x3e622317f8C93f7328350cF0b56d9eD4C620C5d6" # Mock/Faucet DAI
    },
    "LOCAL": {
    }
}
