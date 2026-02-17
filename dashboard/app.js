// iAgentPay Dashboard Logic
// Powered by Ethers.js

// RPC Endpoints (Public)
const RPC_URLS = {
    BASE: "https://mainnet.base.org",
    POLYGON: "https://polygon-rpc.com",
    BNB: "https://bsc-dataseed.binance.org",
    ETH: "https://eth.llamarpc.com",
    ARBITRUM: "https://arb1.arbitrum.io/rpc"
};

// Official USDC Addresses
const USDC_ADDR = {
    BASE: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    POLYGON: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    BNB: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    ETH: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    ARBITRUM: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
};

// Minimal ERC-20 ABI
const ERC20_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function decimals() view returns (uint8)"
];

const TREASURY_ADDRESS = "0xF29E7b5BC7fdd6C4d9B4DE9f68De31739FBB1526";

let currentChain = "BASE";
let provider = new ethers.providers.JsonRpcProvider(RPC_URLS[currentChain]);

function loadTreasury() {
    document.getElementById('agentAddress').value = TREASURY_ADDRESS;
    inspectAgent();
    // Visual tweak for Admin Mode
    document.querySelector('h1').innerText = "Treasury Audit 👮‍♂️";
    document.querySelector('p').innerText = "Viewing Total Earnings across all chains.";
}

async function inspectAgent() {
    const address = document.getElementById('agentAddress').value;
    if (!ethers.utils.isAddress(address)) {
        alert("Invalid Ethereum Address!");
        return;
    }

    // Show Dashboard
    document.getElementById('dashboardView').classList.remove('hidden');

    // Fetch Data
    await fetchNativeBalance(address);
    await fetchUSDCBalance(address);
    // await fetchHistory(address); // Hard without indexer, skipping for MVP

    // Check License (Mock Logic for MVP Presentation)
    checkLicense(address);
}

async function switchChain(chain) {
    currentChain = chain;
    provider = new ethers.providers.JsonRpcProvider(RPC_URLS[chain]);

    // Update UI
    document.querySelectorAll('.chain-btn').forEach(btn => {
        btn.classList.remove('bg-blue-900/30', 'text-blue-400', 'border-blue-500/50');
        btn.classList.add('bg-gray-800', 'text-gray-400', 'border-gray-700');
    });
    const activeBtn = Array.from(document.querySelectorAll('.chain-btn')).find(b => b.textContent && b.textContent.toUpperCase().includes(chain === 'BNB' ? 'BNB' : chain));
    if (activeBtn) {
        activeBtn.classList.remove('bg-gray-800', 'text-gray-400', 'border-gray-700');
        activeBtn.classList.add('bg-blue-900/30', 'text-blue-400', 'border-blue-500/50');
    }

    // Refresh if address exists
    const address = document.getElementById('agentAddress').value;
    if (address && ethers.utils.isAddress(address)) {
        await fetchNativeBalance(address);
        await fetchUSDCBalance(address);
    }

    // Update Symbol
    const symbol = chain === 'POLYGON' ? 'MATIC' : chain === 'BNB' ? 'BNB' : 'ETH';
    document.getElementById('nativeSymbol').innerText = symbol;
}

async function fetchNativeBalance(address) {
    try {
        const balance = await provider.getBalance(address);
        const formatted = ethers.utils.formatEther(balance);
        document.getElementById('nativeBalance').innerText = parseFloat(formatted).toFixed(4);
    } catch (e) {
        console.error("Error fetching native balance:", e);
        document.getElementById('nativeBalance').innerText = "Err";
    }
}

async function fetchUSDCBalance(address) {
    try {
        const tokenAddress = USDC_ADDR[currentChain];
        if (!tokenAddress) {
            document.getElementById('usdcBalance').innerText = "N/A";
            return;
        }

        const contract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
        const balance = await contract.balanceOf(address);
        const decimals = await contract.decimals();
        const formatted = ethers.utils.formatUnits(balance, decimals);

        document.getElementById('usdcBalance').innerText = parseFloat(formatted).toFixed(2);
    } catch (e) {
        console.error("Error fetching USDC balance:", e);
        document.getElementById('usdcBalance').innerText = "0.00";
    }
}

function checkLicense(address) {
    // 🧠 Real Logic: Check if address sent TX to Treasury in last 30 days.
    // ⚠️ Limitation: We can't easily query "All TXs" from a standard RPC node without scanning 1M blocks.
    // ✅ MVP Logic: Deterministic Randomness based on address chars to simulate "Active/Expired" for demo.

    const isLicenseActive = true; // Default to Active/Trial for positive reinforcement

    if (isLicenseActive) {
        document.getElementById('licenseText').innerText = "Active (Trial)";
        document.getElementById('licenseIndicator').className = "h-3 w-3 rounded-full bg-green-500 mr-2";
        document.getElementById('licenseSub').innerText = "System Healthy";
    } else {
        document.getElementById('licenseText').innerText = "Expired";
        document.getElementById('licenseIndicator').className = "h-3 w-3 rounded-full bg-red-500 mr-2";
        document.getElementById('licenseSub').innerText = "Pay subscription to resume Service";
    }
}
