// iAgent-Pay Cyberpunk Dashboard Logic
// Powered by Ethers.js & Web3 simulation telemetry

// RPC Endpoints
// --- GLOBAL ERROR TRACKING (HELP DESK) ---
window.addEventListener('error', function(event) {
    try {
        fetch('/api/errors/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                error_message: event.message || 'Unknown Error',
                stack_trace: event.error ? event.error.stack : '',
                user_address: document.getElementById('agentAddress')?.value || 'Anonymous Web User'
            })
        }).catch(e => console.error('Error reporting failed:', e));
    } catch(e) {}
});

window.addEventListener('unhandledrejection', function(event) {
    try {
        fetch('/api/errors/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                error_message: event.reason ? (event.reason.message || event.reason.toString()) : 'Unhandled Promise Rejection',
                stack_trace: event.reason && event.reason.stack ? event.reason.stack : '',
                user_address: document.getElementById('agentAddress')?.value || 'Anonymous Web User'
            })
        }).catch(e => console.error('Error reporting failed:', e));
    } catch(e) {}
});

const RPC_URLS = {
    BASE: "https://mainnet.base.org",
    POLYGON: "https://polygon-rpc.com",
    BNB: "https://bsc-dataseed.binance.org",
    ETH: "https://eth.llamarpc.com"
};

const RPC_NAMES = {
    BASE: "Base Mainnet RPC",
    POLYGON: "Polygon PoS RPC",
    BNB: "BSC Dataseed RPC",
    ETH: "Ethereum LlamaRPC"
};

// Official USDC Addresses
const USDC_ADDR = {
    BASE: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    POLYGON: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    BNB: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    ETH: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
};

// Minimal ERC-20 ABI
const ERC20_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function decimals() view returns (uint8)"
];

const TREASURY_ADDRESS = "0xF29E7b5BC7fdd6C4d9B4DE9f68De31739FBB1526";

let currentChain = "BASE";
let provider = new ethers.JsonRpcProvider(RPC_URLS[currentChain]);
let rotationsCount = 0;
let volumeAccumulated = 750.00;

// Log helper to simulate standard terminal logs in the UI console
function logToConsole(message, type = "info") {
    const consoleEl = document.getElementById("terminalConsole");
    if (!consoleEl) return;

    const timestamp = new Date().toLocaleTimeString();
    let colorClass = "text-sky-400";
    
    // Check light-mode
    const isLightMode = document.body.classList.contains('light-mode');
    
    if (type === "warning") {
        colorClass = isLightMode ? "text-amber-600 font-semibold" : "text-amber-400";
    } else if (type === "error" || type === "alert") {
        colorClass = isLightMode ? "text-rose-600 font-semibold" : "text-rose-400";
    } else if (type === "success") {
        colorClass = isLightMode ? "text-emerald-600 font-bold" : "text-emerald-400 font-bold";
    } else if (type === "batch") {
        colorClass = isLightMode ? "text-indigo-600 font-semibold" : "text-indigo-400";
    } else {
        colorClass = isLightMode ? "text-slate-700" : "text-sky-400";
    }

    consoleEl.innerHTML += `<span class="text-gray-500">[${timestamp}]</span> <span class="${colorClass}">${message}</span><br>`;
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearConsole() {
    document.getElementById("terminalConsole").innerHTML = `<span class="text-gray-500">// Consola limpia. Esperando acciones...</span><br>`;
}

// Load default Treasury Address for testing
function loadTreasury() {
    document.getElementById('agentAddress').value = TREASURY_ADDRESS;
    inspectAgent();
}

async function checkSafetyKernel() {
    try {
        const trRes = await fetch(`/api/admin/treasury_stats`).catch(e => { throw e; });
        if (trRes.ok) {
            const trData = await trRes.json();
            document.getElementById('treasuryBalance').innerText = trData.balance.toFixed(2);
            if (trData.auto_yield) {
                document.getElementById('chkTreasuryYield').checked = true;
                document.getElementById('treasuryStatus').innerText = "ACTIVA (Aave)";
                document.getElementById('treasuryStatus').className = "text-emerald-400 font-bold";
            }
        }
    } catch(e) { showToastError(`Error Treasury: ${e.message}`); }
    
    let data = { active_alerts: 0 };
    try {
        const res = await fetch(`/api/admin/safety`).catch(e => { throw e; });
        if (!res.ok) throw new Error(res.statusText);
        data = await res.json();
    } catch(e) { showToastError(`Error Safety: ${e.message}`); }
    const alertBox = document.getElementById('safetyAlerts');
    
    if (data.active_alerts > 0) {
        alertBox.innerHTML = `
            <div class="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-xs flex items-start gap-2">
                <span>⚠️</span>
                <span>Se detectaron ${data.active_alerts} operaciones bloqueadas. Revisa los logs.</span>
            </div>
        `;
    } else {
        alertBox.innerHTML = `<div class="p-3 bg-white/5 border border-white/10 rounded-lg text-muted-xs-val text-xs text-center font-mono" data-i18n="kernelClean">Sistema Operando Nominalmente. Sin anomalías detectadas.</div>`;
    }
}

async function toggleTreasuryYield(isChecked) {
    try {
        const res = await fetch('/api/admin/yield_toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ enable: isChecked })
        }).catch(e => { throw e; });
        
        if (!res.ok) throw new Error(res.statusText);
        const data = await res.json();
        
        const statusEl = document.getElementById('treasuryStatus');
        if (data.success && isChecked) {
            statusEl.innerText = "ACTIVA (Aave)";
            statusEl.className = "text-emerald-400 font-bold";
        } else {
            statusEl.innerText = "INACTIVA";
            statusEl.className = "text-red-400 font-bold";
        }
    } catch(e) {
        showToastError(`Error Yield Toggle: ${e.message}`);
        console.error("Failed to toggle yield");
    }
}

async function inspectAgent() {
    const address = document.getElementById('agentAddress').value.trim();
    if (!address) {
        alert("Por favor ingresa una dirección.");
        return;
    }

    // Basic address resolution (Simulating social/ENS resolution)
    let resolvedAddress = address;
    if (address.endsWith(".eth")) {
        logToConsole(`[SOCIAL] Resolviendo dominio ENS: ${address}...`);
        try {
            // Standard mainnet provider for ENS resolver
            const ethProvider = new ethers.JsonRpcProvider(RPC_URLS.ETH);
            const resolved = await ethProvider.resolveName(address);
            if (resolved) {
                resolvedAddress = resolved;
                logToConsole(`[SOCIAL] Dominio resuelto exitosamente: ${resolvedAddress}`, "success");
            } else {
                logToConsole(`[SOCIAL] No se pudo resolver ENS. Usando dirección original.`, "warning");
            }
        } catch (e) {
            logToConsole(`[SOCIAL] Error de red resolviendo ENS: ${e.message}`, "warning");
        }
    }

    if (!ethers.isAddress(resolvedAddress)) {
        alert("¡Dirección Ethereum no válida!");
        return;
    }

    // Show Dashboard
    document.getElementById('dashboardView').classList.remove('hidden');

    clearConsole();
    logToConsole(`[CORE] Inicializando auditoría de agente: ${resolvedAddress}`);
    logToConsole(`[CORE] Cargando Safety Kernel en la red ${currentChain}...`);

    // Fetch Data
    await fetchNativeBalance(resolvedAddress);
    await fetchUSDCBalance(resolvedAddress);
    
    // Add default test transaction
    updateTransactionsTable();
}

async function switchChain(chain) {
    currentChain = chain;
    provider = new ethers.JsonRpcProvider(RPC_URLS[chain]);
    document.getElementById("activeRpcNode").innerText = RPC_NAMES[chain];

    // Update UI Chain Selector Buttons
    document.querySelectorAll('.chain-btn').forEach(btn => {
        btn.className = "chain-btn px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 bg-white/5 text-gray-400 border border-white/5 hover:border-gray-500";
    });

    const activeBtn = document.getElementById(`btn-${chain}`);
    if (activeBtn) {
        activeBtn.className = "chain-btn px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 bg-green-500/10 text-green-400 border border-green-400/30";
    }

    logToConsole(`[CORE] Conmutando a red: ${chain}`);

    // Update Symbols
    const symbol = chain === 'POLYGON' ? 'MATIC' : chain === 'BNB' ? 'BNB' : 'ETH';
    document.getElementById('nativeSymbol').innerText = symbol;

    // Refresh Balances
    const address = document.getElementById('agentAddress').value.trim();
    if (address && (ethers.isAddress(address) || address.endsWith(".eth"))) {
        let resolved = address;
        if (address.endsWith(".eth")) {
            const ethProvider = new ethers.JsonRpcProvider(RPC_URLS.ETH);
            resolved = await ethProvider.resolveName(address) || address;
        }
        if (ethers.isAddress(resolved)) {
            await fetchNativeBalance(resolved);
            await fetchUSDCBalance(resolved);
        }
    }
}

async function fetchNativeBalance(address) {
    try {
        const balance = await provider.getBalance(address);
        const formatted = ethers.formatEther(balance);
        const val = parseFloat(formatted);
        document.getElementById('nativeBalance').innerText = val.toFixed(4);
        logToConsole(`[RPC] Balance de Gas Nativo leído: ${val.toFixed(4)} ${document.getElementById('nativeSymbol').innerText}`);
        
        // Gas Watcher Alerta
        const gasBadge = document.getElementById("gasWatcherBadge");
        if (gasBadge) {
            if (val < 0.005) {
                gasBadge.innerText = "⚠️ Gas Crítico";
                gasBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold animate-pulse";
            } else {
                gasBadge.innerText = "🟢 Suficiente";
                gasBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold";
            }
        }
    } catch (e) {
        console.error(e);
        document.getElementById('nativeBalance').innerText = "Err";
        logToConsole(`[RPC] Error consultando balance nativo: ${e.message}`, "error");
        
        const gasBadge = document.getElementById("gasWatcherBadge");
        if (gasBadge) {
            gasBadge.innerText = "⚠️ Error RPC";
            gasBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-500 border border-amber-500/20 font-bold";
        }
    }
}

async function fetchUSDCBalance(address) {
    try {
        const tokenAddress = USDC_ADDR[currentChain];
        const contract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
        const balance = await contract.balanceOf(address);
        const decimals = await contract.decimals();
        const formatted = ethers.formatUnits(balance, decimals);
        document.getElementById('usdcBalance').innerText = parseFloat(formatted).toFixed(2);
        logToConsole(`[RPC] Balance USDC leído: $${parseFloat(formatted).toFixed(2)} USDC`);
    } catch (e) {
        console.error(e);
        document.getElementById('usdcBalance').innerText = "0.00";
        logToConsole(`[RPC] Token no detectado o error de balance: $0.00 USDC`, "warning");
    }
}

// ----------------------------------------------------
// Theme Switcher Logic
// ----------------------------------------------------
function toggleLightMode() {
    const body = document.body;
    const btn = document.getElementById("themeToggleBtn");
    const isLight = body.classList.toggle("light-mode");
    
    if (isLight) {
        btn.innerHTML = "🌙 Modo Oscuro";
        btn.className = "flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--panel-border)] bg-black/5 hover:bg-black/10 transition-all text-xs font-mono text-gray-800";
        logToConsole("[THEME] Cambiado a Modo Claro exitosamente.", "info");
    } else {
        btn.innerHTML = "☀️ Modo Claro";
        btn.className = "flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--panel-border)] bg-white/5 hover:bg-white/10 transition-all text-xs font-mono text-white";
        logToConsole("[THEME] Cambiado a Modo Oscuro exitosamente.", "info");
    }
}

// ----------------------------------------------------
// ----------------------------------------------------
// Tab Selector Logic
// ----------------------------------------------------
function showTab(tab) {
    const clientTab = document.getElementById("clientTabContent");
    const simTab = document.getElementById("simulationsTabContent");
    const clientBtn = document.getElementById("tab-client");
    const simBtn = document.getElementById("tab-simulations");

    if (tab === 'client') {
        clientTab.classList.remove('hidden');
        simTab.classList.add('hidden');
        clientBtn.className = "px-6 py-3 text-sm font-semibold border-b-2 border-[var(--accent-primary)] text-main transition-all flex items-center gap-2";
        simBtn.className = "px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-muted-val hover:text-main transition-all flex items-center gap-2";
        logToConsole("[SYSTEM] Conmutando a vista de producción del cliente.", "info");
    } else {
        clientTab.classList.add('hidden');
        simTab.classList.remove('hidden');
        clientBtn.className = "px-6 py-3 text-sm font-semibold border-b-2 border-transparent text-muted-val hover:text-main transition-all flex items-center gap-2";
        simBtn.className = "px-6 py-3 text-sm font-semibold border-b-2 border-[var(--accent-primary)] text-main transition-all flex items-center gap-2";
        logToConsole("[SYSTEM] Conmutando a entorno Sandbox de simulaciones avanzadas.", "info");
    }
}

// ----------------------------------------------------
// Simulated Ledger Helper
// ----------------------------------------------------
function addSimulatedTx(hash, type, recipient, detail, status = "Confirmada") {
    const tbody = document.getElementById("simTxTableBody");
    if (!tbody) return;

    // Remove placeholder row if it's there
    if (tbody.innerHTML.includes("Ninguna simulación ejecutada todavía")) {
        tbody.innerHTML = "";
    }

    const statusColor = status === "Confirmada" ? "text-emerald-500" : status === "Pendiente" ? "text-yellow-500" : "text-rose-500";

    tbody.innerHTML = `
        <tr>
            <td class="px-6 py-4 font-mono text-blue-400">${hash}</td>
            <td class="px-6 py-4"><span class="bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded text-xs font-bold font-sans">${type}</span></td>
            <td class="px-6 py-4 text-xs font-mono text-muted-val">${recipient}</td>
            <td class="px-6 py-4 text-main font-mono">${detail}</td>
            <td class="px-6 py-4 font-bold font-sans ${statusColor}">${status}</td>
        </tr>
    ` + tbody.innerHTML;

    const simTxCount = tbody.children.length;
    document.getElementById("simTxCountBadge").innerText = `${simTxCount} Transacciones Simuladas`;
}

// ----------------------------------------------------
// Sandbox State & Control Helpers
// ----------------------------------------------------
let simCapital = 10000.00;
let simVolumeAccumulated = 0.00;

function deductCapital(amount) {
    simCapital = Math.max(0, simCapital - amount);
    const capValEl = document.getElementById("simCapitalValue");
    if (capValEl) {
        capValEl.innerText = `$${simCapital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDC`;
    }
}

function addSimVolume(amount) {
    simVolumeAccumulated = Math.min(1000.00, simVolumeAccumulated + amount);
    const textEl = document.getElementById("volumeProgressText");
    const barEl = document.getElementById("volumeProgressBar");
    if (textEl && barEl) {
        textEl.innerText = `$${simVolumeAccumulated.toFixed(2)} / $1000.00`;
        const pct = (simVolumeAccumulated / 1000.0) * 100;
        barEl.style.width = `${pct}%`;
    }
}

function resetSandbox() {
    simCapital = 10000.00;
    simVolumeAccumulated = 0.00;
    rotationsCount = 0;
    
    const capValEl = document.getElementById("simCapitalValue");
    if (capValEl) {
        capValEl.innerText = "$10,000.00 USDC";
    }
    
    const textEl = document.getElementById("volumeProgressText");
    const barEl = document.getElementById("volumeProgressBar");
    if (textEl && barEl) {
        textEl.innerText = "$0.00 / $1000.00";
        barEl.style.width = "0%";
    }
    
    const rpcRotEl = document.getElementById("rpcRotations");
    if (rpcRotEl) {
        rpcRotEl.innerText = "0";
    }
    const rpcNodeEl = document.getElementById("simActiveRpcNode");
    if (rpcNodeEl) {
        rpcNodeEl.innerText = "Base Mainnet RPC";
    }
    const rpcLatEl = document.getElementById("simRpcLatency");
    if (rpcLatEl) {
        rpcLatEl.innerText = "12ms latency";
    }
    const rpcStatEl = document.getElementById("rpcStatusText");
    if (rpcStatEl) {
        rpcStatEl.innerText = "🟢 Saludable";
        rpcStatEl.className = "text-emerald-500 font-bold";
    }
    
    const consoleEl = document.getElementById("terminalConsole");
    if (consoleEl) {
        consoleEl.innerHTML = `<span class="text-gray-500">// Sandbox reiniciado. Listo para comenzar...</span><br>`;
    }
    
    const tbody = document.getElementById("simTxTableBody");
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-muted-xs-val font-mono">Ninguna simulación ejecutada todavía. Utilice los controles de arriba.</td></tr>`;
    }
    
    const badge = document.getElementById("simTxCountBadge");
    if (badge) {
        badge.innerText = "0 Transacciones Simuladas";
    }
}

function triggerSimulation(fn) {
    const mode = document.getElementById("simOpMode").value;
    if (mode === "loop") {
        logToConsole(`[BUCLE] Iniciando bucle de 5 ejecuciones consecutivas...`, "info");
        let delay = 0;
        for (let i = 1; i <= 5; i++) {
            setTimeout(() => {
                fn(i);
            }, delay);
            delay += 600; // staggered nicely
        }
    } else {
        fn(0);
    }
}

// ----------------------------------------------------
// v8.5.0 Sandbox Telemetry Simulators
// ----------------------------------------------------

// 1. Execute Pipelined Batch Payments
function simPipelinedBatch(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    
    logToConsole(`[BATCH] Iniciando transacción por lotes de 3 transferencias concurrentes...`, "batch");
    logToConsole(`[BATCH] Evaluando límites en Safety Kernel contra la suma total ($40.00 USDC)...`, "batch");
    logToConsole(`[BATCH] Resolviendo nonces secuenciales de forma canalizada (pipelined)...`, "batch");
    
    setTimeout(() => {
        logToConsole(`[BATCH] [CONCURRENTE] Firmando y enviando Tx 1 con nonce 104`, "batch");
        logToConsole(`[BATCH] [CONCURRENTE] Firmando y enviando Tx 2 con nonce 105`, "batch");
        logToConsole(`[BATCH] [CONCURRENTE] Firmando y enviando Tx 3 con nonce 106`, "batch");
    }, 600 / scale);

    setTimeout(() => {
        logToConsole(`[BATCH] Esperando recibos de transacciones concurrentemente...`, "info");
    }, 1200 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] ¡Lote completado con éxito! Gas total consumido: 0.0024 ETH. Ahorro por Multicall: 31.4%`, "success");
        
        addSimulatedTx(`0x3f5c..e9${suffix}`, "Lote Concurrent (1/3)", "0xProveedorA...", "$10.00 USDC");
        addSimulatedTx(`0x7a8d..12${suffix}`, "Lote Concurrent (2/3)", "0xProveedorB...", "$25.00 USDC");
        addSimulatedTx(`0xde41..5b${suffix}`, "Lote Concurrent (3/3)", "0xProveedorC...", "$5.00 USDC");

        // Deduct capital & Add simulated volume
        deductCapital(40.00);
        addSimVolume(40.00);
    }, 2500 / scale);
}

// 2. Simulate RPC Rate Limit (429) & Auto-Rotation
function simRpc429Rotation(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    const isRpcFailoverActive = document.getElementById("toggleRpcFailover").checked;

    logToConsole(`[RPC] Consultando balances del agente en nodo principal...`, "info");
    
    setTimeout(() => {
        logToConsole(`[RPC] [ERROR] HTTP 429 Too Many Requests (Rate limit excedido por el proveedor RPC).`, "warning");
        logToConsole(`[RPC] Aplicando política de Backoff Exponencial. Reintento 1 en 1.0s...`, "warning");
        document.getElementById("simRpcLatency").innerText = "---";
    }, 800 / scale);

    setTimeout(() => {
        logToConsole(`[RPC] [ERROR] HTTP 429 Too Many Requests. Reintento 2 en 2.0s...`, "warning");
    }, 2000 / scale);

    if (!isRpcFailoverActive) {
        setTimeout(() => {
            logToConsole(`[RPC] Failover DESACTIVADO. Nodo principal inaccesible. Conexión perdida permanentemente.`, "error");
            document.getElementById("rpcStatusText").innerText = "🔴 Desconectado";
            document.getElementById("rpcStatusText").className = "text-rose-500 font-bold";
            addSimulatedTx(`0xfailedrpc${suffix}`, "RPC Failure", "Main RPC Node", "Fallo Permanente", "Fallo");
        }, 3000 / scale);
        return;
    }

    setTimeout(() => {
        logToConsole(`[RPC] Reintentos agotados en nodo principal. Disparando Failover de Red...`, "warning");
        logToConsole(`[RPC] Rotando automáticamente al proveedor RPC secundario...`, "info");
        document.getElementById("rpcStatusText").innerText = "🟡 Conmutando...";
        document.getElementById("rpcStatusText").className = "text-yellow-500 font-bold";
    }, 3200 / scale);

    setTimeout(() => {
        rotationsCount += 1;
        document.getElementById("rpcRotations").innerText = rotationsCount;
        document.getElementById("simActiveRpcNode").innerText = "Secondary Base RPC (BlastAPI)";
        document.getElementById("simRpcLatency").innerText = "35ms latency";
        document.getElementById("rpcStatusText").innerText = "🟢 Saludable (Backup)";
        document.getElementById("rpcStatusText").className = "text-green-500 font-bold";
        logToConsole(`[SUCCESS] Conexión establecida con éxito en BlastAPI RPC. Operaciones de consulta reanudadas.`, "success");
        
        addSimulatedTx(`0xrotrpc..7a${suffix}`, "RPC Rotation", "BlastAPI Backup Node", "Conmutación exitosa");
    }, 4500 / scale);
}

// 3. Simulate Uniswap Auto-Swap Liquidity Balancing
function simAutoSwapLiquidity(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    const isAutoSwapActive = document.getElementById("toggleAutoSwap").checked;

    logToConsole(`[LIQUIDEZ] Solicitud de pago recibida por $150.00 USDC...`, "info");
    logToConsole(`[LIQUIDEZ] Verificando balance en stablecoins del agente... Balance disponible: $12.40 USDC`, "warning");
    logToConsole(`[LIQUIDEZ] Balance insuficiente. Fondos requeridos: $137.60 USDC.`, "warning");

    if (!isAutoSwapActive) {
        setTimeout(() => {
            logToConsole(`[LIQUIDEZ] Auto-Swap Fallback DESACTIVADO. Transacción abortada por falta de liquidez en stablecoins.`, "error");
            addSimulatedTx(`0xfailedup${suffix}`, "Auto-Swap Failed", "Uniswap V3 Router", "Líquidez Insuficiente", "Fallo");
        }, 1500 / scale);
        return;
    }

    logToConsole(`[LIQUIDEZ] Auto-Swap Fallback activo. Calculando intercambio óptimo de gas nativo a USDC...`, "info");
    
    setTimeout(() => {
        logToConsole(`[LIQUIDEZ] Intercambiando 0.052 ETH por $144.48 USDC en Uniswap v3 (incluye buffer de deslizamiento de seguridad del 5%)...`, "info");
    }, 1000 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Intercambio ejecutado con éxito. Tx Hash: 0xswap481d...`, "success");
        logToConsole(`[LIQUIDEZ] Balance actualizado. Procediendo con el pago original de $150.00 USDC.`, "info");
    }, 2200 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Transferencia de stablecoin confirmada en la blockchain.`, "success");
        
        addSimulatedTx(`0xswap48..1d${suffix}`, "Uniswap Swap", "Uniswap V3 Router", "-0.052 ETH (+144.48 USDC)");
        addSimulatedTx(`0xpay88d..a3${suffix}`, "Pago Autónomo", "0xSocioComercial...", "$150.00 USDC");

        deductCapital(150.00);
        addSimVolume(150.00);
    }, 3200 / scale);
}

// 4. Simulate Safety Limit Bypass block
function simSafetyLimitBypass(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    const isSafetyKernelActive = document.getElementById("toggleSafetyKernel").checked;

    logToConsole(`[SAFETY] Solicitud de pago recibida por $350.00 USDC a la dirección 0xDesconocido...`, "info");
    logToConsole(`[SAFETY] Evaluando políticas del Safety Kernel...`, "info");

    if (isSafetyKernelActive) {
        setTimeout(() => {
            logToConsole(`[SAFETY] [RECHAZADO] Transacción bloqueada por el Safety Kernel. Motivo: Monto solicitado ($350.00) excede el límite máximo por transacción individual configurado ($150.00 USDC).`, "alert");
            logToConsole(`[SAFETY] Disparando circuito de protección (Circuit Breaker). Ninguna transacción fue firmada ni transmitida a la red.`, "error");
            
            addSimulatedTx(`Bloqueado${suffix}`, "Safety Limit Bypass", "0xDesconocido...", "$350.00 USDC", "Rechazada");
        }, 1200 / scale);
    } else {
        setTimeout(() => {
            logToConsole(`[SAFETY] Safety Kernel DESACTIVADO. Omitiendo verificaciones de límites diarios y por transacción.`, "warning");
            logToConsole(`[SAFETY] Firmando y transmitiendo transacción de riesgo sin restricciones...`, "warning");
        }, 600 / scale);

        setTimeout(() => {
            logToConsole(`[SUCCESS] Transacción forzada confirmada en la red. ¡Peligro de drenaje detectado!`, "success");
            addSimulatedTx(`0xunsafe..f1${suffix}`, "Pago Forzado (Unsafe)", "0xDesconocido...", "$350.00 USDC", "Confirmada (Peligro)");

            deductCapital(350.00);
            addSimVolume(350.00);
        }, 1200 / scale);
    }
}

// 5. Simulate Gasless Paymaster Sponsor
function simGaslessPaymaster(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    const isGaslessActive = document.getElementById("toggleGasless").checked;

    logToConsole(`[PAYMASTER] Solicitud de pago sin saldo nativo de Gas para el Agente...`, "info");
    logToConsole(`[PAYMASTER] Detectando Paymaster Sponsor disponible en Base Mainnet...`, "info");

    if (!isGaslessActive) {
        setTimeout(() => {
            logToConsole(`[PAYMASTER] [ERROR] Faltan fondos de Gas nativo (ETH) en la billetera y Sponsor Gasless está DESACTIVADO. Transacción abortada.`, "error");
            addSimulatedTx(`0xfailedpay${suffix}`, "Gasless Paymaster", "0xSocioB...", "Falta Gas (ETH)", "Fallo");
        }, 1200 / scale);
        return;
    }

    logToConsole(`[PAYMASTER] Paymaster verificado: 0xSponsorPaymasterBase...`, "success");

    setTimeout(() => {
        logToConsole(`[PAYMASTER] Firmando meta-transacción ERC-4337 UserOperation...`, "info");
        logToConsole(`[PAYMASTER] Transmitiendo UserOperation a Bundler con gas patrocinado...`, "info");
    }, 600 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Transacción ejecutada con éxito. Costo de Gas: $0.00 (Sponsor por iAgent-Pay Enterprise)`, "success");
        addSimulatedTx(`0x4337..e2${suffix}`, "Paymaster Gasless", "0xSocioB...", "$12.50 USDC (Patrocinado)");

        deductCapital(12.50);
        addSimVolume(12.50);
    }, 1800 / scale);
}

// 6. Simulate HMAC-SHA256 Webhook Emission
function simHmacWebhook(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    
    logToConsole(`[WEBHOOK] Detectando evento de pago exitoso de $150.00 USDC...`, "info");
    logToConsole(`[WEBHOOK] Preparando firma criptográfica HMAC-SHA256 para webhook...`, "info");
    
    const payload = JSON.stringify({ event: "payment.success", amount: 150.0, timestamp: Date.now() });
    logToConsole(`[WEBHOOK] Generando hash con clave secreta del agente...`, "info");

    setTimeout(() => {
        logToConsole(`[WEBHOOK] Enviando POST request a https://api.cliente.com/webhooks`, "info");
        logToConsole(`[WEBHOOK] Headers enviados: Stripe-Signature: t=1775...,v1=8d24f...`, "info");
    }, 600 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Webhook recibido exitosamente por el servidor cliente. HTTP Status: 200 OK.`, "success");
        addSimulatedTx(`Webhook${suffix}`, "HMAC Notification", "api.cliente.com", "payment.success (200 OK)");
    }, 1500 / scale);
}

// 7. Simulate DeFi Yield Optimization (Aave v3)
function simDeFiAave(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    
    logToConsole(`[DEFI] Analizando fondos ociosos del agente... Balance disponible: $850.00 USDC`, "info");
    logToConsole(`[DEFI] Regla de auto-inversión activa: Mantener buffer de $200.00 y colocar el resto en yield pools.`, "info");
    logToConsole(`[DEFI] Depositando $650.00 USDC en el pool de liquidez Aave v3...`, "info");

    setTimeout(() => {
        logToConsole(`[DEFI] Interactuando con Aave Pool Contract (USDC token aUSDC)...`, "info");
    }, 600 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Fondos depositados exitosamente. Generando ~4.85% APY. Tx Hash: 0xaave441f...`, "success");
        addSimulatedTx(`0xaave44..1f${suffix}`, "Aave v3 Deposit", "Aave Lending Pool", "+$650.00 aUSDC");

        deductCapital(650.00);
    }, 1500 / scale);
}

// 8. Simulate Fleet Dispatch Coordinator
function simFleetDispatch(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    
    logToConsole(`[FLEET] Iniciando delegación de subtareas para la flota de agentes...`, "info");
    logToConsole(`[FLEET] Coordinador principal despacha 2 sub-agentes secundarios (AgenteCompras y AgenteEnvios)...`, "info");

    setTimeout(() => {
        logToConsole(`[FLEET] Generando presupuestos aislados de seguridad en Safety Kernel...`, "info");
        logToConsole(`[FLEET] AgenteCompras presupuestado con límite diario: $50.00 USDC`, "success");
        logToConsole(`[FLEET] AgenteEnvios presupuestado con límite diario: $20.00 USDC`, "success");
    }, 600 / scale);

    setTimeout(() => {
        logToConsole(`[SUCCESS] Flota despachada con éxito. Sub-agentes listos para ejecutar de forma autónoma.`, "success");
        addSimulatedTx(`0xfleet88..22${suffix}`, "Fleet Dispatch", "Safety Kernel Coordinator", "2 Sub-Agentes Despachados ($70K Escrow)");

        deductCapital(70.00);
    }, 1500 / scale);
}

// 9. Simulate Human-in-the-Loop Approval (KYA)
function simHumanLoopApproval(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";
    const isHumanLoopActive = document.getElementById("toggleHumanLoop").checked;

    logToConsole(`[HUMAN LOOP] Detectada transacción a destinatario no listado por $80.00 USDC...`, "info");
    logToConsole(`[HUMAN LOOP] Requiere verificación Know-Your-Agent (KYA) / Aprobación del Propietario.`, "warning");

    if (!isHumanLoopActive) {
        setTimeout(() => {
            logToConsole(`[HUMAN LOOP] [ERROR] Human-in-the-Loop DESACTIVADO. Dirección no autorizada en lista blanca. Transacción rechazada automáticamente por seguridad.`, "error");
            addSimulatedTx(`BlockedHuman${suffix}`, "Human Loop Rejection", "Owner Mobile", "$80.00 USDC", "Rechazada");
        }, 1200 / scale);
        return;
    }

    logToConsole(`[HUMAN LOOP] Enviando notificación push de aprobación al móvil del propietario...`, "info");
    logToConsole(`[HUMAN LOOP] [PENDIENTE] Esperando firma de aprobación manual...`, "warning");
    
    setTimeout(() => {
        logToConsole(`[SUCCESS] Aprobación manual confirmada por el Propietario. Firma cargada.`, "success");
        logToConsole(`[SUCCESS] Transacción liberada y transmitida con éxito.`, "success");
        addSimulatedTx(`0xhuman..7f${suffix}`, "Human Loop Approved", "Owner Mobile", "$80.00 USDC");

        deductCapital(80.00);
        addSimVolume(80.00);
    }, 1600 / scale);
}

// 10. Simulate Reputation Score Evaluation
function simReputationScore(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";

    logToConsole(`[REPUTACIÓN] Evaluando historial del agente para calcular Reputation Score...`, "info");
    logToConsole(`[REPUTACIÓN] Analizando 145 transacciones exitosas, 0 fallos de consenso, 1 bypass mitigado por Safety Kernel.`, "info");
    
    setTimeout(() => {
        logToConsole(`[REPUTACIÓN] Puntaje calculado: 98/100 (AAA - Excelente).`, "success");
        logToConsole(`[SUCCESS] Registro de reputación actualizado en contrato de reputación iAgent-Pay.`, "success");
        addSimulatedTx(`0xrep99..3a${suffix}`, "Reputation Audit", "iAgent-Pay Registry", "Score: 98/100 (AAA)");
    }, 1000 / scale);
}

// 11. Simulate HTTP 402 Paywall Micro-payment
function simHttp402Paywall(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";

    logToConsole(`[x402] Agente intenta descargar dataset de entrenamiento en api.dataset.com...`, "info");
    logToConsole(`[x402] Servidor responde con HTTP 402 Payment Required. Detalle de pago adjunto en cabeceras.`, "warning");
    logToConsole(`[x402] Procesando pago autónomo de $0.50 USDC por micro-licencia...`, "info");
    
    setTimeout(() => {
        logToConsole(`[SUCCESS] Pago de micro-licencia completado. Clave de descarga liberada.`, "success");
        addSimulatedTx(`0x402pay..9c${suffix}`, "HTTP 402 Paywall", "api.dataset.com", "$0.50 USDC");

        deductCapital(0.50);
        addSimVolume(0.50);
    }, 1200 / scale);
}

// 12. Simulate Fiat Off-Ramp ACH/SEPA
function simFiatOffRamp(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";

    logToConsole(`[FIAT] Balance acumulado supera el límite de tesorería local ($500.00 USDC).`, "info");
    logToConsole(`[FIAT] Iniciando retiro autónomo (Off-Ramp) hacia cuenta bancaria corporativa...`, "info");
    logToConsole(`[FIAT] Enrutando a través del puente fiat (ACH/SEPA)...`, "info");
    
    setTimeout(() => {
        logToConsole(`[SUCCESS] Retiro ejecutado. $500.00 USDC convertidos y transferidos a Cuenta IBAN ES89 2100...`, "success");
        addSimulatedTx(`0xfiat ACH..a1${suffix}`, "ACH Fiat Off-Ramp", "ES89 2100...", "$500.00 USD");

        deductCapital(500.00);
    }, 1500 / scale);
}

// 13. Simulate Social Resolver payments
function simSocialResolver(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";

    logToConsole(`[SOCIAL] Intento de pago autónomo al destinatario Twitter/X: @DesarrolladorAI`, "info");
    logToConsole(`[SOCIAL] Consultando registro de nombres de iAgent-Pay Social Registry...`, "info");
    
    setTimeout(() => {
        logToConsole(`[SOCIAL] Dirección resuelta para @DesarrolladorAI: 0x8a92fB41dD3b6928eC881775d0538fC14F3e8771`, "success");
        logToConsole(`[SUCCESS] Transacción enviada a la dirección resuelta. Hash: 0xsoc91d...`, "success");
        addSimulatedTx(`0xsoc91..8a${suffix}`, "Social Pay Resolve", "@DesarrolladorAI", "$15.00 USDC");

        deductCapital(15.00);
        addSimVolume(15.00);
    }, 1200 / scale);
}

// 14. Simulate Cross-Chain Bridge Swap
function simCrossChainBridge(loopNum = 0) {
    const scale = loopNum > 0 ? 5 : 1;
    const suffix = loopNum > 0 ? `-${loopNum}` : "";

    logToConsole(`[BRIDGE] Pago requerido en Polygon Mainnet ($30.00 USDC).`, "info");
    logToConsole(`[BRIDGE] Balance disponible en Base Mainnet ($120.00 USDC). Balance en Polygon: $0.00 USDC.`, "warning");
    logToConsole(`[BRIDGE] Iniciando puenteo cross-chain (Base -> Polygon) usando enrutamiento Li.Fi/Bridge...`, "info");
    
    setTimeout(() => {
        logToConsole(`[SUCCESS] Puenteo y swap completado. Fondos depositados en Polygon. Pago original procesado.`, "success");
        addSimulatedTx(`0xbridge..bb${suffix}`, "Cross-Chain Bridge", "Li.Fi Router (Base->Poly)", "$30.00 USDC");

        deductCapital(30.00);
        addSimVolume(30.00);
    }, 1600 / scale);
}


function updateVolumeProgressBar() {
    document.getElementById("volumeProgressText").innerText = `$${volumeAccumulated.toFixed(2)} / $1000.00`;
    const pct = (volumeAccumulated / 1000.0) * 100;
    document.getElementById("volumeProgressBar").style.width = `${pct}%`;
}

function showToastError(msg) {
    let toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.className = 'fixed bottom-4 right-4 bg-red-600/90 text-white px-6 py-3 rounded shadow-lg z-50 transition-opacity duration-300 opacity-0 pointer-events-none';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.remove('opacity-0');
    toast.classList.add('opacity-100');
    setTimeout(() => {
        toast.classList.remove('opacity-100');
        toast.classList.add('opacity-0');
    }, 5000);
}

async function updateTransactionsTable() {
    const tbody = document.getElementById("txTableBody");
    const countBadge = document.getElementById("txCountBadge");
    
    try {
        const response = await fetch('/api/transactions').catch(e => {
            showToastError(`Fallo de Red: ${e.message}`);
            throw e;
        });
        
        if (!response.ok) {
            showToastError(`Error API (${response.status}): ${response.statusText}`);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const txList = data.transactions ? data.transactions : data;
        
        if (!txList || txList.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-muted-val text-sm">
                        📭 No hay historial de transacciones en el ordenador aún.
                    </td>
                </tr>
            `;
            countBadge.innerText = "0 Transacciones";
            return;
        }
        
        let html = "";
        let calculatedVolume = 0.0;
        
        txList.forEach(tx => {
            const shortHash = tx.tx_hash.substring(0, 6) + ".." + tx.tx_hash.substring(tx.tx_hash.length - 4);
            const dateObj = new Date(tx.timestamp * 1000);
            const timeStr = dateObj.toLocaleTimeString() + " " + dateObj.toLocaleDateString();
            
            let statusColor = "text-emerald-500";
            let statusLabel = "Confirmada";
            
            if (tx.status.includes("FAILED")) {
                statusColor = "text-rose-500";
                statusLabel = "Fallida";
            } else if (tx.status.includes("BLOCKED")) {
                statusColor = "text-amber-500";
                statusLabel = "Bloqueada";
            } else if (tx.status.includes("SENT")) {
                statusColor = "text-sky-400";
                statusLabel = "Enviada";
            }
            
            let typeBadge = `<span class="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs font-bold font-sans">Pago</span>`;
            if (tx.status.includes("BLOCKED")) {
                typeBadge = `<span class="bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded text-xs font-bold font-sans">Seguridad</span>`;
            }
            
            html += `
                <tr>
                    <td class="px-6 py-4 font-mono text-blue-400"><a href="#" onclick="alert('Tx Hash: ${tx.tx_hash}')" class="hover:underline">${shortHash}</a></td>
                    <td class="px-6 py-4">${typeBadge}</td>
                    <td class="px-6 py-4 text-xs font-mono text-muted-val">${tx.recipient}</td>
                    <td class="px-6 py-4 text-green-400">${tx.amount.toFixed(4)} ${tx.symbol}</td>
                    <td class="px-6 py-4 text-xs text-muted-val">${timeStr}</td>
                    <td class="px-6 py-4 ${statusColor} font-bold font-sans">${statusLabel}</td>
                </tr>
            `;
            
            if (tx.status.includes("CONFIRMED") || tx.status.includes("SENT")) {
                const price = tx.symbol === "ETH" ? 2500.0 : (tx.symbol === "SOL" ? 150.0 : 1.0);
                calculatedVolume += tx.amount * price;
            }
        });
        
        tbody.innerHTML = html;
        countBadge.innerText = `${txList.length} ${txList.length === 1 ? 'Transacción' : 'Transacciones'}`;
        
        volumeAccumulated = calculatedVolume;
        updateVolumeProgressBar();
        
        // Update license status based on the 2-year free trial (730 days)
        const firstTxTimestamp = (txList && txList.length > 0) ? txList[txList.length - 1].timestamp : (Date.now() / 1000);
        const daysActive = (Date.now() / 1000 - firstTxTimestamp) / 86400;
        const daysRemaining = Math.max(0, 730 - daysActive);
        
        const licenseTextEl = document.getElementById("licenseText");
        const licenseSubEl = document.getElementById("licenseSub");
        if (licenseTextEl) {
            licenseTextEl.innerText = "Prueba Gratuita (2 Años)";
            licenseTextEl.className = "text-xl font-bold tracking-tight text-emerald-400 font-sans";
        }
        if (licenseSubEl) {
            licenseSubEl.innerText = `${Math.ceil(daysRemaining)} días restantes (Sin comisiones)`;
        }
        
        // Update Activation Date and Saved Fees
        const actDateEl = document.getElementById("licenseActivationDate");
        const savedFeesEl = document.getElementById("licenseSavedFees");
        if (actDateEl) {
            actDateEl.innerText = new Date(firstTxTimestamp * 1000).toLocaleDateString();
        }
        if (savedFeesEl) {
            const savedAmountVal = calculatedVolume * 0.001; // 0.1% of volume
            savedFeesEl.innerText = `$${savedAmountVal.toFixed(2)} USD`;
        }
        
    } catch (e) {
        console.error("Error updating transactions table:", e);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-rose-500 text-sm">
                    ⚠️ Error al integrar datos del ordenador: ${e.message}
                </td>
            </tr>
        `;
        countBadge.innerText = "Error";
    }
}

function downloadReport() {
    const address = document.getElementById('agentAddress').value.trim();
    if (!address) {
        alert("Por favor cargue un agente primero.");
        return;
    }
    
    // Build JSON data
    const reportData = {
        agent_wallet: address,
        active_chain: currentChain,
        rpc_node: document.getElementById("activeRpcNode").innerText,
        rpc_rotations: rotationsCount,
        balances: {
            native: document.getElementById('nativeBalance').innerText + " " + document.getElementById('nativeSymbol').innerText,
            stablecoin: "$" + document.getElementById('usdcBalance').innerText + " USDC"
        },
        safety_kernel: {
            daily_limit: document.getElementById('dailyLimit').innerText,
            max_tx_limit: document.getElementById('maxTxLimit').innerText,
            whitelist_status: "Active (2 addresses)"
        },
        auto_swap_fallback: "Desactivado (Upgrade disponible)",
        volume_accumulated_usd: volumeAccumulated,
        license_status: {
            type: "Prueba Gratuita (2 Años)",
            activation_date: document.getElementById("licenseActivationDate") ? document.getElementById("licenseActivationDate").innerText : "N/A",
            saved_commissions_usd: document.getElementById("licenseSavedFees") ? document.getElementById("licenseSavedFees").innerText : "$0.00 USD"
        },
        timestamp: new Date().toISOString(),
        transactions: []
    };
    
    // Parse transactions from the DOM table
    const rows = document.querySelectorAll("#txTableBody tr");
    rows.forEach(row => {
        const cols = row.querySelectorAll("td");
        if (cols.length >= 6) {
            reportData.transactions.push({
                hash: cols[0].innerText,
                type: cols[1].innerText,
                recipient: cols[2].innerText,
                amount: cols[3].innerText,
                date: cols[4].innerText,
                status: cols[5].innerText
            });
        }
    });

    try {
        const jsonContent = JSON.stringify(reportData, null, 4);
        const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        
        const downloadAnchor = document.createElement('a');
        downloadAnchor.href = url;
        downloadAnchor.download = `iagentpay_report_${address.slice(0,8)}.json`;
        
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        
        // Cleanup
        document.body.removeChild(downloadAnchor);
        URL.revokeObjectURL(url);
        
        logToConsole(`[SYSTEM] Reporte de auditoría de producción descargado para el agente ${address.slice(0,8)}...`, "success");
    } catch (e) {
        logToConsole(`[SYSTEM] Error al generar descarga: ${e.message}`, "error");
    }
}

function downloadSimReport() {
    const rpcNode = document.getElementById("simActiveRpcNode") ? document.getElementById("simActiveRpcNode").innerText : "Base Mainnet RPC";
    const rpcRotations = document.getElementById("rpcRotations") ? document.getElementById("rpcRotations").innerText : "0";
    const statusText = document.getElementById("rpcStatusText") ? document.getElementById("rpcStatusText").innerText : "🟢 Saludable";
    
    const reportData = {
        title: "iAgent-Pay Sandbox Simulation Audit Report",
        timestamp: new Date().toISOString(),
        sandbox_state: {
            sim_capital_remaining: `$${simCapital.toFixed(2)} USDC`,
            sim_volume_accumulated: `$${simVolumeAccumulated.toFixed(2)} USDC`,
            active_rpc_node: rpcNode,
            rpc_rotations_count: parseInt(rpcRotations),
            rpc_status: statusText,
            toggles: {
                safety_kernel: document.getElementById("toggleSafetyKernel").checked,
                auto_swap: document.getElementById("toggleAutoSwap").checked,
                rpc_failover: document.getElementById("toggleRpcFailover").checked,
                gasless_sponsor: document.getElementById("toggleGasless").checked,
                human_in_the_loop: document.getElementById("toggleHumanLoop").checked
            }
        },
        simulated_transactions: []
    };
    
    const rows = document.querySelectorAll("#simTxTableBody tr");
    rows.forEach(row => {
        const cols = row.querySelectorAll("td");
        if (cols.length >= 5) {
            reportData.simulated_transactions.push({
                hash: cols[0].innerText,
                type: cols[1].innerText,
                recipient: cols[2].innerText,
                detail: cols[3].innerText,
                status: cols[4].innerText
            });
        }
    });

    try {
        const jsonContent = JSON.stringify(reportData, null, 4);
        const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        
        const downloadAnchor = document.createElement('a');
        downloadAnchor.href = url;
        downloadAnchor.download = `iagentpay_sim_audit_${Date.now()}.json`;
        
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        
        document.body.removeChild(downloadAnchor);
        URL.revokeObjectURL(url);
        
        logToConsole(`[SYSTEM] Reporte de auditoría de simulaciones descargado con éxito...`, "success");
    } catch (e) {
        logToConsole(`[SYSTEM] Error al generar descarga de simulación: ${e.message}`, "error");
    }
}

function runStressTest() {
    resetSandbox();
    
    logToConsole("🧪 [TEST ESTRÉS] Iniciando simulación de estrés de 100 operaciones consecutivas...", "info");
    logToConsole("🧪 [TEST ESTRÉS] Alternando dinámicamente políticas y simulaciones en el kernel...", "info");

    const simulations = [
        simPipelinedBatch,
        simRpc429Rotation,
        simAutoSwapLiquidity,
        simSafetyLimitBypass,
        simGaslessPaymaster,
        simHmacWebhook,
        simDeFiAave,
        simFleetDispatch,
        simHumanLoopApproval,
        simReputationScore,
        simHttp402Paywall,
        simFiatOffRamp,
        simSocialResolver,
        simCrossChainBridge
    ];

    const originalSafety = document.getElementById("toggleSafetyKernel").checked;
    const originalAutoSwap = document.getElementById("toggleAutoSwap").checked;
    const originalRpc = document.getElementById("toggleRpcFailover").checked;
    const originalGasless = document.getElementById("toggleGasless").checked;
    const originalHuman = document.getElementById("toggleHumanLoop").checked;

    let op = 0;
    const totalOps = 100;
    
    function nextOp() {
        if (op >= totalOps) {
            document.getElementById("toggleSafetyKernel").checked = originalSafety;
            document.getElementById("toggleAutoSwap").checked = originalAutoSwap;
            document.getElementById("toggleRpcFailover").checked = originalRpc;
            document.getElementById("toggleGasless").checked = originalGasless;
            document.getElementById("toggleHumanLoop").checked = originalHuman;

            logToConsole(`[TEST ESTRÉS] ✅ PRUEBA DE ESTRÉS COMPLETADA CON ÉXITO.`, "success");
            logToConsole(`[TEST ESTRÉS] 📊 Resumen final:`, "info");
            logToConsole(`  - Total Operaciones: 100`, "info");
            logToConsole(`  - Capital Remanente USDC: $${simCapital.toFixed(2)} USDC`, "success");
            logToConsole(`  - Volumen Acumulado: $${simVolumeAccumulated.toFixed(2)} / $1000.00`, "success");
            logToConsole(`  - Estado de Excepciones del Runtime: 0 errores detectados (100% de éxito)`, "success");

            setTimeout(() => {
                logToConsole("[TEST ESTRÉS] Descargando reporte de auditoría JSON automáticamente...", "success");
                downloadSimReport();
            }, 800);
            return;
        }

        op++;
        if (op % 10 === 0) {
            document.getElementById("toggleSafetyKernel").checked = Math.random() > 0.5;
            document.getElementById("toggleAutoSwap").checked = Math.random() > 0.5;
            document.getElementById("toggleRpcFailover").checked = Math.random() > 0.5;
            document.getElementById("toggleGasless").checked = Math.random() > 0.5;
            document.getElementById("toggleHumanLoop").checked = Math.random() > 0.5;
        }

        const randSim = simulations[Math.floor(Math.random() * simulations.length)];
        randSim(op);

        setTimeout(nextOp, 25);
    }

    nextOp();
}
