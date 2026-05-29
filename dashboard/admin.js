// iAgent-Pay Master Operator Dashboard JavaScript

const API_BASE = window.location.origin;

let killSwitchActive = false;
let reputationData = [];
let chartInstances = {};
let advancedOperations = [];

// Operations Pagination State
let opCurrentPage = 1;
const opLimit = 100;
let opTotalPages = 1;

// Auth State Variables
let challengeToken = '';
let challengeText = '';

// DOM Elements
const refreshBtn = document.getElementById('refreshBtn');
const systemAlertBanner = document.getElementById('systemAlertBanner');
const alertDisableBtn = document.getElementById('alertDisableBtn');

const metricVolume = document.getElementById('metricVolume');
const metricTransactions = document.getElementById('metricTransactions');
const metricAgents = document.getElementById('metricAgents');
const metricAgentsSub = document.getElementById('metricAgentsSub');
const metricSavedCommissions = document.getElementById('metricSavedCommissions');

// Kill Switch DOM
const toggleKillSwitchBtn = document.getElementById('toggleKillSwitchBtn');
const toggleIndicator = document.getElementById('toggleIndicator');
const switchStatusText = document.getElementById('switchStatusText');
const killSwitchPanel = document.getElementById('killSwitchPanel');

// Forms & Inputs
const licenseForm = document.getElementById('licenseForm');
const licenseWallet = document.getElementById('licenseWallet');
const licenseGraceInput = document.getElementById('licenseGraceInput');
const licenseFeeInput = document.getElementById('licenseFeeInput');

const reputationForm = document.getElementById('reputationForm');
const repWallet = document.getElementById('repWallet');
const repScore = document.getElementById('repScore');

const agentSearch = document.getElementById('agentSearch');
const agentTableBody = document.getElementById('agentTableBody');

// Treasury DOM
const treasuryForm = document.getElementById('treasuryForm');
const treasuryEvm = document.getElementById('treasuryEvm');
const treasurySolana = document.getElementById('treasurySolana');
const treasuryXrpl = document.getElementById('treasuryXrpl');

// Operations DOM
const opStartDate = document.getElementById('opStartDate');
const opEndDate = document.getElementById('opEndDate');
const opStatusFilter = document.getElementById('opStatusFilter');
const opSearchBtn = document.getElementById('opSearchBtn');
const opPrintBtn = document.getElementById('opPrintBtn');
const opExportCsvBtn = document.getElementById('opExportCsvBtn');
const opPrevBtn = document.getElementById('opPrevBtn');
const opNextBtn = document.getElementById('opNextBtn');
const operationsTableBody = document.getElementById('operationsTableBody');
const opPageDisplay = document.getElementById('opPageDisplay');
const opPaginationInfo = document.getElementById('opPaginationInfo');

// Modal DOM
const txDetailModal = document.getElementById('txDetailModal');
const closeTxModalBtn = document.getElementById('closeTxModalBtn');
const modalPrintBtn = document.getElementById('modalPrintBtn');

// --- Helper: Authenticated Fetch Wrapper ---
// Read-only endpoints (metrics & transactions) are public and never trigger login overlay
const PUBLIC_ENDPOINTS = ['/api/admin/metrics', '/api/transactions'];

// --- Helper: Global Toast Notification ---
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

async function authFetch(url, options = {}) {
    const token = sessionStorage.getItem('adminToken');
    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    let res;
    try {
        res = await fetch(url, options);
    } catch (e) {
        showToastError(`Fallo de Red: ${e.message}`);
        throw e;
    }
    
    const isPublic = PUBLIC_ENDPOINTS.some(ep => url.includes(ep));
    if (res.status === 401 && !url.includes('/auth/') && !isPublic) {
        // Only show login overlay for protected write operations
        sessionStorage.removeItem('adminToken');
        document.getElementById('loginOverlay').classList.remove('hidden');
    }
    
    if (!res.ok && res.status !== 401) {
        try {
            const err = await res.clone().json();
            showToastError(`Error API (${res.status}): ${err.error || err.message || res.statusText}`);
        } catch(e) {
            showToastError(`Error API (${res.status}): ${res.statusText}`);
        }
    }
    
    return res;
}


// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    try {
        if (typeof Chart !== 'undefined') {
            initCharts();
        } else {
            console.error('Chart.js is not loaded.');
        }
    } catch (e) {
        console.error('Error initializing charts:', e);
    }
    
    try {
        await checkAuthStatus();
    } catch (e) {
        console.error('Error checking auth status:', e);
        showAuthError('Error crítico al cargar el sistema.');
    }

    // Event Listeners
    refreshBtn?.addEventListener('click', loadAllData);

    toggleKillSwitchBtn?.addEventListener('click', toggleKillSwitch);
    alertDisableBtn?.addEventListener('click', () => setKillSwitch(false));

    reputationForm?.addEventListener('submit', handleReputationSubmit);
    licenseForm?.addEventListener('submit', handleLicenseSubmit);
    treasuryForm?.addEventListener('submit', handleTreasurySubmit);
    agentSearch?.addEventListener('input', filterAgents);

    // Auth Listeners
    document.getElementById('registerAdminBtn')?.addEventListener('click', handleRegisterAdmin);
    document.getElementById('connectSignBtn')?.addEventListener('click', handleLoginSign);

    // Safety Limits Listeners
    document.getElementById('safetyLimitsForm')?.addEventListener('submit', handleSafetyLimitsSubmit);
    document.getElementById('registerAdminBtn')?.addEventListener('click', handleRegisterAdmin);
    document.getElementById('connectSignBtn')?.addEventListener('click', handleLoginSign);

    // Backup Listeners
    document.getElementById('exportBackupBtn')?.addEventListener('click', handleBackupExport);
    document.getElementById('importBackupBtn')?.addEventListener('click', () => {
        document.getElementById('backupFileInput')?.click();
    });
    document.getElementById('backupFileInput')?.addEventListener('change', handleBackupImport);

    // Reset DB Listener
    document.getElementById('resetDbBtn')?.addEventListener('click', handleResetDatabase);

    // Operations Listeners
    opSearchBtn?.addEventListener('click', () => {
        opCurrentPage = 1;
        fetchAdvancedTransactions();
    });
    
    opPrevBtn?.addEventListener('click', () => {
        if (opCurrentPage > 1) {
            opCurrentPage--;
            fetchAdvancedTransactions();
        }
    });
    
    opNextBtn?.addEventListener('click', () => {
        if (opCurrentPage < opTotalPages) {
            opCurrentPage++;
            fetchAdvancedTransactions();
        }
    });

    opPrintBtn?.addEventListener('click', () => window.print());
    opExportCsvBtn?.addEventListener('click', exportOperationsCsv);
    closeTxModalBtn?.addEventListener('click', () => txDetailModal?.classList.add('hidden'));
    modalPrintBtn?.addEventListener('click', () => window.print());
});

// --- Authentication Flow Logic ---
async function checkAuthStatus() {
    // Always load public data (metrics, transactions) immediately — no login required
    document.getElementById('loginOverlay').classList.add('hidden');
    loadAllData();
    loadSafetyLimits();

    // If there's a saved session token, validate it silently in the background
    const token = sessionStorage.getItem('adminToken');
    if (token) {
        const res = await fetch(`${API_BASE}/api/admin/metrics`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            // Token expired — clear it, but don't block the dashboard
            sessionStorage.removeItem('adminToken');
        }
    }
    // Challenge is fetched in background for write operations when needed
    fetchChallenge().catch(() => {});
}

async function fetchChallenge() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/auth/challenge`);
        if (!res.ok) throw new Error('Error al obtener desafío de autenticación');
        const data = await res.json();
        
        challengeToken = data.token;
        challengeText = data.challenge;
        
        const loginOverlay = document.getElementById('loginOverlay');
        const setupView = document.getElementById('setupView');
        const loginView = document.getElementById('loginView');
        const adminWalletDisplay = document.getElementById('adminWalletDisplay');
        const loginStatus = document.getElementById('loginStatus');
        
        loginOverlay.classList.remove('hidden');
        loginStatus.classList.add('hidden');
        
        if (data.setup_needed) {
            setupView.classList.remove('hidden');
            loginView.classList.add('hidden');
            document.getElementById('loginSubtitle').innerText = 'Configura la billetera del administrador maestro';
        } else {
            setupView.classList.add('hidden');
            loginView.classList.remove('hidden');
            adminWalletDisplay.innerText = `Master Admin:\n${data.admin_address}`;
            document.getElementById('loginSubtitle').innerText = 'Inicia sesión firmando el desafío criptográfico';
        }
    } catch (err) {
        console.error(err);
        showAuthError('Error de comunicación con el servidor de seguridad.');
    }
}

function showAuthError(msg) {
    const status = document.getElementById('loginStatus');
    status.innerText = msg;
    status.classList.remove('hidden');
}

async function handleRegisterAdmin() {
    if (!window.ethereum) {
        showAuthError('Instala MetaMask u otra billetera EVM compatible.');
        return;
    }
    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const wallet = accounts[0];
        
        const res = await fetch(`${API_BASE}/api/admin/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: wallet })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Error al registrar administrador');
        }
        
        await fetchChallenge();
    } catch (err) {
        showAuthError(err.message);
    }
}

async function handleLoginSign() {
    if (!window.ethereum) {
        showAuthError('Instala MetaMask u otra billetera EVM compatible.');
        return;
    }
    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const wallet = accounts[0];
        
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [challengeText, wallet]
        });
        
        const res = await fetch(`${API_BASE}/api/admin/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token: challengeToken,
                address: wallet,
                signature: signature
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Verificación de firma fallida.');
        }
        
        const data = await res.json();
        sessionStorage.setItem('adminToken', data.token);
        document.getElementById('loginOverlay').classList.add('hidden');
        loadAllData();
    } catch (err) {
        showAuthError(err.message);
    }
}

// --- Backup & Restore Logic ---
async function handleBackupExport() {
    const password = document.getElementById('backupPassword').value;
    if (!password || password.length < 4) {
        alert('Por favor ingresa una contraseña de al menos 4 caracteres para encriptar el respaldo.');
        return;
    }
    try {
        const token = sessionStorage.getItem('adminToken');
        const res = await fetch(`${API_BASE}/api/admin/backup/export`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            },
            body: JSON.stringify({ password })
        });
        
        if (!res.ok) {
            throw new Error('Error al exportar copia de seguridad');
        }
        
        // Streaming download via Blob
        const blob = await res.blob();
        
        // Extract filename from header
        let filename = `iagentpay_backup_${Date.now()}.enc`;
        const disp = res.headers.get('Content-Disposition');
        if (disp && disp.includes('filename=')) {
            filename = disp.split('filename=')[1].replace(/"/g, '');
        }
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        alert('Copia de seguridad encriptada descargada con éxito mediante Data Stream.');
    } catch (err) {
        alert('Falla al exportar respaldo: ' + err.message);
    }
}

async function handleBackupImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const password = document.getElementById('backupPassword').value;
    if (!password) {
        alert('Por favor ingresa la contraseña para desencriptar el respaldo.');
        e.target.value = '';
        return;
    }
    
    try {
        const token = sessionStorage.getItem('adminToken');
        const res = await fetch(`${API_BASE}/api/admin/backup/import`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'X-Backup-Password': password,
                'Content-Type': 'application/octet-stream'
            },
            body: file
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Error al importar copia de seguridad');
        }
        
        const result = await res.json();
        alert(result.message || 'Respaldo restaurado con éxito.');
        loadAllData();
    } catch (err) {
        alert('Falla al importar respaldo: ' + err.message);
    } finally {
        e.target.value = '';
    }
}

async function handleResetDatabase() {
    if (!window.ethereum) {
        alert("MetaMask (u otra billetera EVM) no detectada.");
        return;
    }

    const confirmation = confirm("⚠️ ¡ADVERTENCIA CRÍTICA!\n\n¿Estás absolutamente seguro de que deseas ELIMINAR TODOS LOS DATOS?\nEsta acción requerirá firmar un mensaje con la billetera de Administrador Maestro.");
    if (!confirmation) return;

    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const wallet = accounts[0];
        const msg = "Confirmar reseteo total de la base de datos de iAgentPay.";
        
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [msg, wallet]
        });

        const res = await authFetch(`${API_BASE}/api/admin/reset_db`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ signature, address: wallet })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Error al restablecer la base de datos');
        }
        
        alert("✅ Base de datos restablecida a cero exitosamente.");
        window.location.reload();
    } catch (err) {
        alert("Falla al restablecer el sistema: " + err.message);
    }
}

// --- Tab Switching Logic ---
window.switchTab = function(tabId) {
    const tabs = ['analytics', 'reputation', 'licenses', 'emergency', 'operations', 'config', 'escrow', 'forensics', 'advancedReports'];
    
    tabs.forEach(t => {
        const btn = document.getElementById(`tabBtn${capitalize(t)}`);
        const content = document.getElementById(`tabContent${capitalize(t)}`);
        
        if (t === tabId) {
            // Active style
            btn.classList.add('border-blue-500', 'text-white', 'font-bold');
            btn.classList.remove('border-transparent', 'text-gray-400', 'font-medium');
            content.classList.remove('hidden');
        } else {
            // Inactive style
            btn.classList.remove('border-blue-500', 'text-white', 'font-bold');
            btn.classList.add('border-transparent', 'text-gray-400', 'font-medium');
            content.classList.add('hidden');
        }
    });

    // Resize Chart.js canvases to fit when showing
    if (tabId === 'analytics') {
        setTimeout(() => {
            Object.values(chartInstances).forEach(chart => {
                chart.resize();
            });
        }, 50);
    }
    
    if (tabId === 'escrow') loadEscrows();
    if (tabId === 'forensics') loadForensics();
};

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

async function loadAllData() {
    await fetchMetrics();
    await fetchReputation();
    await fetchKillSwitch();
    await fetchTreasury();
    await fetchTransactions(); // Live txs
    await fetchAdvancedTransactions(); // Advanced operations history
    await fetchAndRenderCharts();
    
    // Initial silent load for new tabs
    try { loadEscrows(); } catch(e) {}
    try { loadForensics(); } catch(e) {}
}

// --- Advanced Operations Logic ---
async function fetchAdvancedTransactions() {
    try {
        const start = opStartDate.value;
        const end = opEndDate.value;
        const status = opStatusFilter.value;
        
        let url = `${API_BASE}/api/transactions?page=${opCurrentPage}&limit=${opLimit}&status=${status}`;
        if (start) url += `&start_date=${start}`;
        if (end) url += `&end_date=${end}`;

        const res = await authFetch(url);
        if (!res.ok) throw new Error('Error al obtener historial de operaciones');
        const data = await res.json();
        
        advancedOperations = data.transactions;
        opTotalPages = data.pagination.total_pages;
        
        opPaginationInfo.innerText = `Mostrando ${advancedOperations.length} de ${data.pagination.total_count} resultados`;
        opPageDisplay.innerText = `Pág. ${opCurrentPage} de ${opTotalPages || 1}`;
        
        opPrevBtn.disabled = opCurrentPage <= 1;
        opNextBtn.disabled = opCurrentPage >= opTotalPages;
        
        renderAdvancedOperations();
    } catch (err) {
        console.error('Error fetching advanced operations:', err);
        operationsTableBody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-red-400">Error al consultar el historial</td></tr>`;
    }
}

function getExplorerUrl(txHash, symbol) {
    if (!txHash) return '#';
    const hash = txHash.trim();
    const sym = (symbol || '').toUpperCase().trim();
    
    // Check if it's a Solana tx (or SPL token)
    if (sym === 'SOL' || sym.endsWith('SOL') || !hash.startsWith('0x')) {
        if (hash.length > 50 && !hash.startsWith('r')) {
            return `https://solscan.io/tx/${hash}`;
        }
    }
    
    // Check if it's XRPL
    if (sym === 'XRP' || hash.startsWith('r') || (hash.length === 64 && !hash.startsWith('0x'))) {
        return `https://livenet.xrpl.org/transactions/${hash}`;
    }
    
    // Fallback to EVM
    return `https://etherscan.io/tx/${hash}`;
}

function renderAdvancedOperations() {
    if (advancedOperations.length === 0) {
        operationsTableBody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-gray-500">No se encontraron operaciones con los filtros aplicados.</td></tr>`;
        return;
    }

    operationsTableBody.innerHTML = '';
    advancedOperations.forEach(tx => {
        let statusBadge = '';
        if (tx.status === 'CONFIRMED') {
            statusBadge = '<span class="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-[10px] font-bold uppercase border border-emerald-500/20">CONFIRMADO</span>';
        } else if (tx.status === 'FAILED') {
            statusBadge = '<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-[10px] font-bold uppercase border border-red-500/20">FALLIDO</span>';
        } else {
            statusBadge = `<span class="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-[10px] font-bold uppercase border border-yellow-500/20">${tx.status}</span>`;
        }

        const dateStr = new Date(tx.timestamp * 1000).toLocaleString();
        const amountUsdText = tx.amount_usd !== undefined ? `<span class="text-[10px] text-gray-400 block">($${tx.amount_usd.toFixed(2)} USD)</span>` : '';
        
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-900/40 transition-colors';
        tr.innerHTML = `
            <td class="py-3 px-4 text-gray-400 whitespace-nowrap">${dateStr}</td>
            <td class="py-3 px-4 text-blue-400 font-semibold flex items-center gap-2"><span class="text-xs">🤖</span> Agente Activo</td>
            <td class="py-3 px-4 font-mono-code text-[11px] text-gray-300 break-all max-w-[200px]">${tx.recipient}</td>
            <td class="py-3 px-4 font-bold text-white whitespace-nowrap">
                ${tx.amount} <span class="text-xs text-gray-500">${tx.symbol || 'USD'}</span>
                ${amountUsdText}
            </td>
            <td class="py-3 px-4 text-center">${statusBadge}</td>
            <td class="py-3 px-4 text-center print-hide">
                <button class="view-detail-btn px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-xs transition-colors" data-hash="${tx.tx_hash}">Ver</button>
            </td>
        `;
        operationsTableBody.appendChild(tr);
    });

    document.querySelectorAll('.view-detail-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const hash = e.target.getAttribute('data-hash');
            openTxModal(hash);
        });
    });
}

function openTxModal(hash) {
    const tx = advancedOperations.find(t => t.tx_hash === hash);
    if (!tx) return;

    const explorerUrl = getExplorerUrl(tx.tx_hash, tx.symbol);
    const hashEl = document.getElementById('modalTxHash');
    hashEl.innerHTML = `
        <a href="${explorerUrl}" target="_blank" class="text-blue-400 hover:text-blue-300 underline inline-flex items-center gap-1 font-mono-code break-all">
            <span>🔗</span> ${tx.tx_hash}
        </a>
    `;
    
    document.getElementById('modalTxDate').innerText = new Date(tx.timestamp * 1000).toLocaleString();
    
    let statusText = tx.status;
    let statusColor = 'text-yellow-400';
    if (tx.status === 'CONFIRMED') {
        statusText = 'CONFIRMADO';
        statusColor = 'text-emerald-400';
    } else if (tx.status === 'FAILED') {
        statusText = 'FALLIDO';
        statusColor = 'text-red-400';
    }
    
    const statusEl = document.getElementById('modalTxStatus');
    statusEl.innerText = statusText;
    statusEl.className = `font-bold ${statusColor}`;

    document.getElementById('modalTxRecipient').innerText = tx.recipient;
    const amountUsdText = tx.amount_usd !== undefined ? ` ($${tx.amount_usd.toFixed(2)} USD)` : '';
    document.getElementById('modalTxAmount').innerText = `${tx.amount} ${tx.symbol || 'USD'}${amountUsdText}`;
    document.getElementById('modalTxFee').innerText = tx.fee_paid ? `${tx.fee_paid} NATIVE` : 'N/A';

    txDetailModal.classList.remove('hidden');
    txDetailModal.classList.add('flex');
}

function exportOperationsCsv() {
    if (advancedOperations.length === 0) {
        alert('No hay operaciones para exportar.');
        return;
    }
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Timestamp,Fecha,Destinatario,Monto,Simbolo,Estado,TxHash,Fee\n";
    
    advancedOperations.forEach(tx => {
        const dateStr = new Date(tx.timestamp * 1000).toISOString();
        const row = [
            tx.timestamp,
            dateStr,
            tx.recipient,
            tx.amount,
            tx.symbol || 'USD',
            tx.status,
            tx.tx_hash,
            tx.fee_paid || '0'
        ].join(",");
        csvContent += row + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `operaciones_iagentpay_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// --- Live Transactions (Dashboard limit 15) ---
async function fetchTransactions() {
    try {
        const res = await authFetch(`${API_BASE}/api/transactions?limit=15`);
        if (!res.ok) throw new Error('Error al obtener últimas operaciones');
        const data = await res.json();
        // The API now returns { transactions: [...], pagination: {...} }
        renderTransactionsTable(data.transactions || []);
    } catch (err) {
        console.error('Error fetching transactions:', err);
        document.getElementById('liveTransactionsBody').innerHTML = `<tr><td colspan="6" class="py-8 text-center text-red-400">Error al consultar transacciones en vivo</td></tr>`;
    }
}

function renderTransactionsTable(transactions) {
    const tbody = document.getElementById('liveTransactionsBody');
    if (transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-gray-500">Ninguna operación registrada recientemente.</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    // Show only the last 15 transactions
    transactions.slice(0, 15).forEach(tx => {
        let statusBadge = '';
        if (tx.status === 'CONFIRMED') {
            statusBadge = '<span class="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-[10px] font-bold uppercase border border-emerald-500/20">CONFIRMADO</span>';
        } else if (tx.status === 'FAILED') {
            statusBadge = '<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-[10px] font-bold uppercase border border-red-500/20">FALLIDO</span>';
        } else {
            statusBadge = `<span class="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-[10px] font-bold uppercase border border-yellow-500/20">${tx.status}</span>`;
        }

        const dateStr = new Date(tx.timestamp * 1000).toLocaleString();
        const explorerUrl = getExplorerUrl(tx.tx_hash, tx.symbol);
        const shortHash = tx.tx_hash ? `${tx.tx_hash.substring(0, 8)}...${tx.tx_hash.substring(tx.tx_hash.length - 8)}` : 'N/A';
        const amountUsdText = tx.amount_usd !== undefined ? `<span class="text-[10px] text-gray-500 block">($${tx.amount_usd.toFixed(2)} USD)</span>` : '';
        
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-900/40 transition-colors';
        tr.innerHTML = `
            <td class="py-4 px-4 text-gray-400 whitespace-nowrap">${dateStr}</td>
            <td class="py-4 px-4 text-blue-400 font-semibold flex items-center gap-2"><span class="text-xs">🤖</span> Agente Activo</td>
            <td class="py-4 px-4 font-mono-code text-[11px] text-gray-300 break-all max-w-[200px]">${tx.recipient}</td>
            <td class="py-4 px-4 font-bold text-white whitespace-nowrap">
                ${tx.amount} <span class="text-xs text-gray-500">${tx.symbol || 'USD'}</span>
                ${amountUsdText}
            </td>
            <td class="py-4 px-4 font-mono-code text-[11px] text-gray-400 break-all max-w-[200px]">
                <a href="${explorerUrl}" target="_blank" class="text-blue-400 hover:text-blue-300 underline inline-flex items-center gap-1 font-mono-code">
                    <span>🔗</span> ${shortHash}
                </a>
            </td>
            <td class="py-4 px-4 text-center">${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- API Calls ---

async function fetchMetrics() {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/metrics`);
        if (!res.ok) throw new Error('Error al obtener métricas');
        const data = await res.json();
        
        // Update dashboard values
        metricVolume.innerText = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(data.total_volume_usd);
        metricTransactions.innerText = data.total_transactions;
        metricAgents.innerText = data.total_agents;
        metricAgentsSub.innerText = `${data.trial_agents} En Gracia | ${data.blacklisted_agents} Sancionados`;
        metricSavedCommissions.innerText = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(data.commissions_saved_usd);
        
        return data;
    } catch (err) {
        console.error('Error fetching metrics:', err);
    }
}

async function fetchKillSwitch() {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/killswitch`);
        if (!res.ok) throw new Error('Error al obtener Kill Switch');
        const data = await res.json();
        updateKillSwitchUI(data.active);
    } catch (err) {
        console.error('Error fetching kill switch:', err);
    }
}

async function setKillSwitch(active) {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/killswitch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active })
        });
        if (!res.ok) throw new Error('Error al guardar Kill Switch');
        const data = await res.json();
        updateKillSwitchUI(data.active);
        fetchMetrics(); // Refresh status indicators
    } catch (err) {
        alert('Falla al enviar comando de suspensión global: ' + err.message);
    }
}

function toggleKillSwitch() {
    setKillSwitch(!killSwitchActive);
}

function updateKillSwitchUI(active) {
    killSwitchActive = active;
    if (active) {
        // Red glowing active state
        toggleKillSwitchBtn.classList.remove('bg-gray-700');
        toggleKillSwitchBtn.classList.add('bg-red-600', 'glow-red');
        toggleIndicator.style.transform = 'translateX(24px)';
        switchStatusText.innerText = '⚠️ FLUIDO GLOBAL SUSPENDIDO';
        switchStatusText.classList.remove('text-emerald-400');
        switchStatusText.classList.add('text-red-500');
        killSwitchPanel.classList.add('kill-switch-active');
        systemAlertBanner.classList.remove('hidden');
    } else {
        // Healthy green inactive state
        toggleKillSwitchBtn.classList.remove('bg-red-600', 'glow-red');
        toggleKillSwitchBtn.classList.add('bg-gray-700');
        toggleIndicator.style.transform = 'translateX(0)';
        switchStatusText.innerText = '🟢 SISTEMA ACTIVO (ONLINE)';
        switchStatusText.classList.remove('text-red-500');
        switchStatusText.classList.add('text-emerald-400');
        killSwitchPanel.classList.remove('kill-switch-active');
        systemAlertBanner.classList.add('hidden');
    }
}

async function fetchReputation() {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/reputation`);
        if (!res.ok) throw new Error('Error al obtener lista de reputación');
        reputationData = await res.json();
        renderAgentTable(reputationData);
    } catch (err) {
        console.error('Error fetching reputation:', err);
        agentTableBody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-red-400">Error al consultar el registro KYA</td></tr>`;
    }
}

function renderAgentTable(data) {
    if (data.length === 0) {
        agentTableBody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-gray-500">Ningún agente externo registrado en la red local.</td></tr>`;
        return;
    }

    agentTableBody.innerHTML = '';
    data.forEach(agent => {
        const score = parseFloat(agent.score);
        let badgeClass = '';
        let badgeText = '';
        let allowTxBadge = '';

        if (score === 0.0) {
            badgeClass = 'bg-red-500/10 border border-red-500/20 text-red-400';
            badgeText = 'BLACKLISTED';
            allowTxBadge = '<span class="text-red-500">❌ Bloqueado</span>';
        } else if (score <= 2.0) {
            badgeClass = 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400';
            badgeText = 'ADVERTENCIA';
            allowTxBadge = '<span class="text-yellow-400">⚠️ Auditado</span>';
        } else if (score <= 4.0) {
            badgeClass = 'bg-blue-500/10 border border-blue-500/20 text-blue-400';
            badgeText = 'TRUSTED (BASIC)';
            allowTxBadge = '<span class="text-emerald-400">🟢 Autorizado</span>';
        } else {
            badgeClass = 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400';
            badgeText = 'ELITE / SB-NFT MINTED';
            allowTxBadge = '<span class="text-emerald-400">🟢 Autorizado</span>';
        }

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-900/40 border-b border-gray-900';
        tr.innerHTML = `
            <td class="py-4 px-4 font-mono-code text-[11px] text-gray-400">${agent.address}</td>
            <td class="py-4 px-4">
                <span class="px-2.5 py-1 text-[10px] font-bold rounded-full ${badgeClass}">${badgeText}</span>
            </td>
            <td class="py-4 px-4 font-semibold text-white">${score.toFixed(1)} / 5.0 <span class="text-[10px] text-gray-500">(${agent.reviews} revs)</span></td>
            <td class="py-4 px-4 text-center text-xs font-semibold">${allowTxBadge}</td>
            <td class="py-4 px-4 text-right">
                ${score === 0.0 ? 
                    `<button onclick="updateAgentScore('${agent.address}', 3.0)" class="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/40 border border-emerald-500/20 text-emerald-400 rounded text-[10px] font-bold uppercase transition-all">Desbloquear</button>` : 
                    `<button onclick="updateAgentScore('${agent.address}', 0.0)" class="px-2.5 py-1 bg-red-600/20 hover:bg-red-600/40 border border-red-500/20 text-red-400 rounded text-[10px] font-bold uppercase transition-all">Sancionar</button>`
                }
            </td>
        `;
        agentTableBody.appendChild(tr);
    });
}

async function updateAgentScore(address, score) {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/reputation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, score })
        });
        if (!res.ok) throw new Error('Error al actualizar reputación');
        fetchReputation();
        fetchMetrics();
        fetchAndRenderCharts();
    } catch (err) {
        alert('Falla al actualizar reputación del agente: ' + err.message);
    }
}

async function handleReputationSubmit(e) {
    e.preventDefault();
    const address = repWallet.value.trim();
    const score = parseFloat(repScore.value);
    
    if (!address.startsWith('0x') && address.length < 30) {
        alert('Dirección de billetera inválida. Debe ser una dirección EVM, Solana o DID.');
        return;
    }

    await updateAgentScore(address, score);
    repWallet.value = '';
    alert('Reputación del agente registrada exitosamente.');
}

async function handleLicenseSubmit(e) {
    e.preventDefault();
    const wallet = licenseWallet.value.trim();
    const grace = parseInt(licenseGraceInput.value);
    const feePercent = parseFloat(licenseFeeInput.value);
    const feeRate = feePercent / 100.0;

    if (!wallet.startsWith('0x') && wallet.length < 30) {
        alert('Dirección de billetera inválida.');
        return;
    }

    try {
        const res = await authFetch(`${API_BASE}/api/admin/licenses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address: wallet, grace_days: grace, fee_rate: feeRate })
        });
        if (!res.ok) throw new Error('Error al guardar licencia');
        const data = await res.json();
        alert(`🏆 Licencia Personalizada Registrada en la Red!\n\nDirección: ${data.address}\nPeriodo de Gracia: ${data.grace_days} Días\nComisión: ${(data.fee_rate * 100).toFixed(2)}%`);
        licenseWallet.value = '';
        loadAllData();
    } catch (err) {
        alert('Falla al registrar licencia VIP: ' + err.message);
    }
}

function filterAgents() {
    const query = agentSearch.value.toLowerCase().trim();
    const filtered = reputationData.filter(agent => 
        agent.address.toLowerCase().includes(query)
    );
    renderAgentTable(filtered);
}

// --- Charting Logic using Chart.js ---

function initCharts() {
    const volEl = document.getElementById('volumeChart');
    const ageEl = document.getElementById('agentsChart');
    const feeEl = document.getElementById('feesChart');

    if (!volEl || !ageEl || !feeEl) {
        console.warn('Chart canvas elements not found in DOM. Skipping initCharts.');
        return;
    }

    const ctxVol = volEl.getContext('2d');
    const ctxAge = ageEl.getContext('2d');
    const ctxFee = feeEl.getContext('2d');

    // 1. Volume History (Line Chart)
    chartInstances.volume = new Chart(ctxVol, {
        type: 'line',
        data: {
            labels: ['Q1', 'Q2', 'Q3', 'Q4', 'Hoy'],
            datasets: [{
                label: 'Volumen USD',
                data: [1200, 2400, 4800, 8900, 12000],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
            }
        }
    });

    // 2. Agents Distribution (Doughnut Chart)
    chartInstances.agents = new Chart(ctxAge, {
        type: 'doughnut',
        data: {
            labels: ['En Periodo de Gracia', 'Licencias VIP', 'Bloqueados'],
            datasets: [{
                data: [1, 0, 0],
                backgroundColor: ['#3b82f6', '#10b981', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9ca3af', font: { size: 11 } }
                }
            }
        }
    });

    // 3. Fees Saved vs Collected (Bar Chart)
    chartInstances.fees = new Chart(ctxFee, {
        type: 'bar',
        data: {
            labels: ['Comisiones Ahorradas', 'Comisiones Cobradas'],
            datasets: [{
                label: 'USD',
                data: [0, 0],
                backgroundColor: ['#10b981', '#3b82f6'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#9ca3af' } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
            }
        }
    });

    // 4. Escrow Chart
    const escEl = document.getElementById('escrowChart');
    if (escEl) {
        chartInstances.escrow = new Chart(escEl.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Retenidos (LOCKED)', 'Liberados (RELEASED)', 'Reembolsados (REFUNDED)'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#f59e0b', '#10b981', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#9ca3af', font: { size: 11 } } }
                }
            }
        });
    }

    // 5. Reputation Chart
    const repEl = document.getElementById('reputationChart');
    if (repEl) {
        chartInstances.reputation = new Chart(repEl.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Elite (5.0)', 'Confiable (3.0+)', 'Advertencia', 'Lista Negra'],
                datasets: [{
                    label: 'Agentes',
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#8b5cf6', '#3b82f6', '#f59e0b', '#ef4444'],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
                }
            }
        });
    }
}

async function fetchAndRenderCharts() {
    try {
        const metricsRes = await authFetch(`${API_BASE}/api/admin/metrics`);
        const txsRes = await fetch(`${API_BASE}/api/transactions`);
        
        
        const escrowsRes = await authFetch(`${API_BASE}/api/admin/escrows`);
        const repRes = await authFetch(`${API_BASE}/api/admin/reputation`);

        if (!metricsRes.ok || !txsRes.ok) return;

        const escrowsData = (escrowsRes && escrowsRes.ok) ? await escrowsRes.json() : { escrows: [] };
        const repData = (repRes && repRes.ok) ? await repRes.json() : [];

        
        const metrics = await metricsRes.json();
        const txsData = await txsRes.json();
        const txs = txsData.transactions || [];
        
        // --- 1. Process Volume Chart Data ---
        let volumeLabels = [];
        let volumeData = [];
        
        if (txs.length === 0) {
            volumeLabels = ['Ahora'];
            volumeData = [0];
        } else {
            // Group by index or simple chronological order
            const sortedTxs = [...txs].reverse();
            let runningSum = 0;
            sortedTxs.forEach((tx, idx) => {
                const txUsd = tx.amount_usd !== undefined ? tx.amount_usd : (tx.amount * 2500.0);
                runningSum += txUsd;
                volumeLabels.push(`Tx #${idx + 1}`);
                volumeData.push(runningSum);
            });
        }
        
        chartInstances.volume.data.labels = volumeLabels;
        chartInstances.volume.data.datasets[0].data = volumeData;
        chartInstances.volume.update();
        
        // --- 2. Process Agents Distribution ---
        const trialCount = metrics.trial_agents || 1;
        const payingCount = metrics.paying_agents || 0;
        const blacklistedCount = metrics.blacklisted_agents || 0;
        
        chartInstances.agents.data.datasets[0].data = [trialCount, payingCount, blacklistedCount];
        chartInstances.agents.update();
        
        // --- 3. Process Fees Chart ---
        const savedFees = metrics.commissions_saved_usd || 0.0;
        const collectedFees = metrics.commissions_collected_usd || 0.0;
        
        chartInstances.fees.data.datasets[0].data = [savedFees, collectedFees];
        chartInstances.fees.update();

    
        // --- 4. Process Escrow Chart Data ---
        if (chartInstances.escrow && escrowsData.escrows) {
            let locked = 0, released = 0, refunded = 0;
            escrowsData.escrows.forEach(e => {
                const s = (e.status || "").toUpperCase();
                if (s === 'LOCKED') locked++;
                else if (s === 'RELEASED') released++;
                else if (s === 'REFUNDED') refunded++;
            });
            chartInstances.escrow.data.datasets[0].data = [locked, released, refunded];
            chartInstances.escrow.update();
        }

        // --- 5. Process Reputation Chart Data ---
        if (chartInstances.reputation && repData) {
            let elite = 0, trusted = 0, warning = 0, blacklisted = 0;
            repData.forEach(r => {
                const s = parseFloat(r.score);
                if (s === 5.0) elite++;
                else if (s >= 3.0) trusted++;
                else if (s >= 1.0) warning++;
                else blacklisted++;
            });
            chartInstances.reputation.data.datasets[0].data = [elite, trusted, warning, blacklisted];
            chartInstances.reputation.update();
        }

        } catch (err) {
        console.error('Error rendering dynamic charts:', err);
    }
}

async function fetchTreasury() {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/treasury`);
        if (!res.ok) throw new Error('Error al obtener tesorería');
        const data = await res.json();
        treasuryEvm.value = data.EVM || '';
        treasurySolana.value = data.SOLANA || '';
        treasuryXrpl.value = data.XRPL || '';
    } catch (err) {
        console.error('Error fetching treasury:', err);
    }
}

async function handleTreasurySubmit(e) {
    e.preventDefault();
    const evm = treasuryEvm.value.trim();
    const solana = treasurySolana.value.trim();
    const xrpl = treasuryXrpl.value.trim();

    const password = window.prompt("Por seguridad, ingresa tu contraseña maestra de tesorería para guardar los cambios:");
    if (password === null) return; // User cancelled

    try {
        const res = await authFetch(`${API_BASE}/api/admin/treasury`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ evm, solana, xrpl, password })
        });
        if (!res.ok) throw new Error('Error al guardar billeteras de tesorería');
        const data = await res.json();
        alert('💰 Billeteras de destino para comisiones actualizadas con éxito!');
        loadAllData();
    } catch (err) {
        alert('Falla al actualizar billeteras de tesorería: ' + err.message);
    }
}

// --- Safety Limits No-Code Logic ---
async function loadSafetyLimits() {
    try {
        const res = await authFetch(`${API_BASE}/api/admin/safety_limits`);
        if (!res.ok) throw new Error('Error al obtener limites de seguridad');
        const data = await res.json();
        
        const slDailyLimit = document.getElementById('slDailyLimit');
        const slMaxTx = document.getElementById('slMaxTx');
        const slHumanThreshold = document.getElementById('slHumanThreshold');
        const slMaxTxMinute = document.getElementById('slMaxTxMinute');
        
        if (slDailyLimit) slDailyLimit.value = data.safety_daily_limit_usd;
        if (slMaxTx) slMaxTx.value = data.safety_max_tx_usd;
        if (slHumanThreshold) slHumanThreshold.value = data.safety_human_threshold_usd;
        if (slMaxTxMinute) slMaxTxMinute.value = data.safety_max_tx_per_minute;
    } catch (err) {
        console.error('Error fetching safety limits:', err);
    }
}

async function handleSafetyLimitsSubmit(e) {
    e.preventDefault();
    if (!window.ethereum) {
        alert('Instala MetaMask u otra billetera EVM compatible para firmar esta operacion.');
        return;
    }
    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const wallet = accounts[0];
        
        const challengeText = "Autorizo modificar los limites presupuestales de las IAs.";
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [challengeText, wallet]
        });
        
        const payload = {
            signature: signature,
            address: wallet,
            safety_daily_limit_usd: parseFloat(document.getElementById('slDailyLimit').value),
            safety_max_tx_usd: parseFloat(document.getElementById('slMaxTx').value),
            safety_human_threshold_usd: parseFloat(document.getElementById('slHumanThreshold').value),
            safety_max_tx_per_minute: parseInt(document.getElementById('slMaxTxMinute').value)
        };
        
        const res = await authFetch(`${API_BASE}/api/admin/safety_limits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || 'Falla al guardar limites de seguridad');
        }
        
        alert('Limites de Seguridad y Presupuesto actualizados exitosamente en todo el protocolo.');
        loadSafetyLimits();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ══════════════════════════════════════════════════════════
// ESCROW ANTI-ALUCINACIÓN
// ══════════════════════════════════════════════════════════
window.loadEscrows = async function() {
    const statusFilter = document.getElementById('escrowStatusFilter')?.value || 'ALL';
    const tbody = document.getElementById('escrowTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-600 py-8">Cargando...</td></tr>';

    try {
        const url = statusFilter === 'ALL'
            ? '/api/admin/escrows'
            : `/api/admin/escrows?status=${statusFilter}`;
        const res = await authFetch(url);
        const data = await res.json();

        // Update summary counters
        const s = data.summary || {};
        const setEl = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        setEl('escrowTotal',    s.total    ?? 0);
        setEl('escrowLocked',   s.locked   ?? 0);
        setEl('escrowReleased', s.released ?? 0);
        setEl('escrowRefunded', s.refunded ?? 0);

        const escrows = data.escrows || [];
        if (escrows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-600 py-8">No hay escrows registrados.</td></tr>';
            return;
        }

        tbody.innerHTML = escrows.map(e => {
            const statusIcon = e.status === 'LOCKED' ? '🔐' : e.status === 'RELEASED' ? '✅' : '🔴';
            const statusColor = e.status === 'LOCKED' ? 'text-yellow-400' : e.status === 'RELEASED' ? 'text-emerald-400' : 'text-red-400';
            const date = e.created_at ? new Date(e.created_at * 1000).toLocaleString() : '—';
            const task = (e.task || '').slice(0, 60) + ((e.task || '').length > 60 ? '...' : '');
            const recipient = (e.recipient || '').slice(0, 18) + '...';
            return `<tr class="hover:bg-gray-900/40 transition-colors">
                <td class="px-4 py-3 font-mono text-xs text-indigo-300">${e.id}</td>
                <td class="px-4 py-3">${task}</td>
                <td class="px-4 py-3 font-mono text-xs text-gray-400">${recipient}</td>
                <td class="px-4 py-3 text-emerald-400 font-bold">$${parseFloat(e.amount_usd || 0).toFixed(2)}</td>
                <td class="px-4 py-3 font-bold ${statusColor}">${statusIcon} ${e.status}</td>
                <td class="px-4 py-3 text-gray-500">${date}</td>
            </tr>`;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-red-400 py-8">Error: ${err.message}</td></tr>`;
    }
};

// ══════════════════════════════════════════════════════════
// PROOF-OF-REASONING — RECIBOS FORENSES
// ══════════════════════════════════════════════════════════
window.loadForensics = async function() {
    const searchVal = document.getElementById('forensicsTxSearch')?.value.trim() || '';
    const tbody = document.getElementById('forensicsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-gray-600 py-8">Cargando...</td></tr>';

    try {
        const url = searchVal ? `/api/admin/forensics?tx=${encodeURIComponent(searchVal)}` : '/api/admin/forensics';
        const res = await authFetch(url);
        const data = await res.json();

        const receipts = data.receipts || [];
        if (receipts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-gray-600 py-8">No hay recibos forenses. Los pagos con razonamiento adjunto aparecerán aquí.</td></tr>';
            return;
        }

        tbody.innerHTML = receipts.map(r => {
            const date = r.timestamp ? new Date(r.timestamp * 1000).toLocaleString() : '—';
            const shortHash = (r.reasoning_hash || '').slice(0, 16) + '...';
            const shortReasoning = (r.reasoning_text || '').slice(0, 55) + ((r.reasoning_text || '').length > 55 ? '...' : '');
            const txShort = (r.tx_hash || '').slice(0, 20) + '...';
            const safeR = JSON.stringify(r).replace(/'/g, "\\'");
            return `<tr class="hover:bg-indigo-950/20 transition-colors cursor-pointer" onclick='showForensicModal(${safeR})'>
                <td class="px-4 py-3 font-mono text-xs text-blue-300" title="${r.tx_hash}">${txShort}</td>
                <td class="px-4 py-3 text-emerald-400 font-bold">${parseFloat(r.amount || 0).toFixed(4)}</td>
                <td class="px-4 py-3 text-gray-400">${r.symbol || ''}</td>
                <td class="px-4 py-3 text-gray-300 italic">${shortReasoning}</td>
                <td class="px-4 py-3 font-mono text-xs text-yellow-400" title="${r.reasoning_hash}">${shortHash}</td>
                <td class="px-4 py-3 text-gray-500">${date}</td>
                <td class="px-4 py-3"><button class="px-2 py-1 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded">🔍 Ver</button></td>
            </tr>`;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-red-400 py-8">Error: ${err.message}</td></tr>`;
    }
};

window.showForensicModal = function(r) {
    document.getElementById('fModalTxHash').textContent    = r.tx_hash || '';
    document.getElementById('fModalAmount').textContent   = `${parseFloat(r.amount || 0).toFixed(6)} ${r.symbol || ''}`;
    document.getElementById('fModalTimestamp').textContent = r.timestamp ? new Date(r.timestamp * 1000).toLocaleString() : '—';
    document.getElementById('fModalReasoning').textContent = r.reasoning_text || 'Sin razonamiento adjunto.';
    document.getElementById('fModalHash').textContent     = r.reasoning_hash || '—';
    const modal = document.getElementById('forensicModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
};

// ══════════════════════════════════════════════════════════
// EXPORTACIÓN DE REPORTES (PDF & EXCEL)
// ══════════════════════════════════════════════════════════
document.getElementById('exportExcelBtn')?.addEventListener('click', () => {
    const vol = document.getElementById('volumeTotal')?.innerText || '0';
    const tx = document.getElementById('txTotal')?.innerText || '0';
    const agents = document.getElementById('agentTotal')?.innerText || '0';
    const saved = document.getElementById('feesSavedTotal')?.innerText || '0';

    const csvContent = `data:text/csv;charset=utf-8,Metrica,Valor\nVolumen Procesado,${vol.replace(/,/g, '')}\nTransacciones,${tx}\nAgentes Registrados,${agents}\nComisiones Ahorradas,${saved.replace(/,/g, '')}`;
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "iAgentPay_Resumen_Ejecutivo.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
});

document.getElementById('exportPdfBtn')?.addEventListener('click', () => {
    const w = window.open('', '_blank');
    const vol = document.getElementById('volumeTotal')?.innerText || '0';
    const tx = document.getElementById('txTotal')?.innerText || '0';
    const agents = document.getElementById('agentTotal')?.innerText || '0';
    const saved = document.getElementById('feesSavedTotal')?.innerText || '0';
    
    w.document.write(`
        <html>
            <head>
                <title>Resumen Ejecutivo - iAgent-Pay</title>
                <style>
                    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #333; line-height: 1.6; }
                    .header { border-bottom: 2px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }
                    h1 { color: #1e3a8a; margin: 0 0 10px 0; }
                    .subtitle { color: #666; font-size: 14px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                    th { background-color: #f8fafc; color: #1e293b; font-weight: bold; }
                    .footer { margin-top: 50px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Resumen Ejecutivo y Registro Contable</h1>
                    <div class="subtitle">
                        <strong>Fecha de Emisión:</strong> ${new Date().toLocaleDateString()}<br>
                        <strong>Sistema:</strong> Protocolo iAgent-Pay v6.0.0 (Pre-Lanzamiento)
                    </div>
                </div>
                
                <h3>1. Reporte de Crecimiento y Capital</h3>
                <p>Durante las operaciones históricas, el flujo monetario procesado por los Agentes IA a través de los contratos inteligentes se resume en la siguiente tabla contable:</p>
                
                <table>
                    <tr><th>Métrica Contable</th><th>Valor Registrado</th></tr>
                    <tr><td><strong>Volumen Global Procesado</strong></td><td>${vol}</td></tr>
                    <tr><td><strong>Transacciones Liquidadas</strong></td><td>${tx} operaciones</td></tr>
                    <tr><td><strong>Agentes Registrados (KYA)</strong></td><td>${agents} identidades DIDs</td></tr>
                    <tr><td><strong>Comisiones Ahorradas a Usuarios</strong></td><td>${saved}</td></tr>
                </table>
                
                <div class="footer">
                    <p><em>Documento generado automáticamente y validado por el Safety Kernel de iAgent-Pay.</em></p>
                </div>
            </body>
        </html>
    `);
    w.document.close();
    // Allow a small delay for rendering before opening print dialog
    setTimeout(() => { w.print(); }, 250);
});

// ══════════════════════════════════════════════════════════
// ADVANCED REPORTS & CHARTS
// ══════════════════════════════════════════════════════════
let advChartVolume = null;
let advChartAgents = null;
let advChartFees = null;

async function loadAdvancedReports() {
    const btn = document.getElementById('btnLoadAdvReports');
    const grid = document.getElementById('advReportsGrid');
    
    if (btn) btn.innerText = 'Cargando...';
    
    const horizon = document.getElementById('repHorizon').value;
    const start = document.getElementById('repStartDate').value;
    const end = document.getElementById('repEndDate').value;
    
    let url = `/api/admin/advanced_reports?horizon=${horizon}`;
    if (start) url += `&start_date=${start}`;
    if (end) url += `&end_date=${end}`;
    
    try {
        const res = await authFetch(url);
        if (!res.ok) throw new Error("Falla al cargar datos.");
        const data = await res.json();
        
        // Destruir gráficos anteriores si existen
        if (advChartVolume) advChartVolume.destroy();
        if (advChartAgents) advChartAgents.destroy();
        if (advChartFees) advChartFees.destroy();
        
        // Configuración visual común
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.font.family = "'Inter', sans-serif";
        
        const gridOptions = { color: 'rgba(255,255,255,0.05)' };
        
        // Grafica Volumen
        const ctxVol = document.getElementById('chartAdvVolume').getContext('2d');
        advChartVolume = new Chart(ctxVol, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Volumen USD',
                    data: data.volume,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: gridOptions }, y: { grid: gridOptions } } }
        });
        
        // Grafica Agentes
        const ctxAg = document.getElementById('chartAdvAgents').getContext('2d');
        advChartAgents = new Chart(ctxAg, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Nuevos Agentes',
                    data: data.agents,
                    backgroundColor: '#10b981',
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: gridOptions }, y: { grid: gridOptions, beginAtZero: true } } }
        });
        
        // Grafica Comisiones
        const ctxFees = document.getElementById('chartAdvFees').getContext('2d');
        advChartFees = new Chart(ctxFees, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Comisiones USD',
                    data: data.fees,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    fill: true,
                    tension: 0.2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: gridOptions }, y: { grid: gridOptions } } }
        });

        // Habilitar visibilidad
        grid.classList.remove('opacity-50', 'pointer-events-none');
        
        // Asignar datos al DOM para exportación global
        window._advReportData = data;
        
    } catch (err) {
        showToastError(err.message);
    } finally {
        if (btn) btn.innerText = 'Generar Reporte';
    }
}

document.getElementById('btnLoadAdvReports')?.addEventListener('click', loadAdvancedReports);

// Modificar switchTab para cargar automaticamente la primera vez
const oldSwitchTab = window.switchTab;
window.switchTab = function(tabId) {
    oldSwitchTab(tabId);
    if (tabId === 'advancedReports' && !advChartVolume) {
        loadAdvancedReports();
    }
    if (tabId === 'errors') {
        loadErrors();
    }
};

// EXPORT TO PDF CON GRÁFICOS INCLUIDOS
document.getElementById('btnAdvExportPdf')?.addEventListener('click', () => {
    if (!advChartVolume) {
        alert("Primero genera el reporte en pantalla.");
        return;
    }
    
    const w = window.open('', '_blank');
    const horizonLabel = document.getElementById('repHorizon').options[document.getElementById('repHorizon').selectedIndex].text;
    
    // Obtener imágenes base64 de las gráficas
    const imgVol = document.getElementById('chartAdvVolume').toDataURL('image/png');
    const imgAg = document.getElementById('chartAdvAgents').toDataURL('image/png');
    const imgFees = document.getElementById('chartAdvFees').toDataURL('image/png');
    
    w.document.write(`
        <html>
            <head>
                <title>Reporte Financiero Avanzado - iAgent-Pay</title>
                <style>
                    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #333; line-height: 1.6; }
                    .header { border-bottom: 2px solid #1e3a8a; padding-bottom: 20px; margin-bottom: 30px; }
                    h1 { color: #1e3a8a; margin: 0 0 10px 0; }
                    .subtitle { color: #666; font-size: 14px; }
                    .chart-container { margin-bottom: 40px; border: 1px solid #eee; padding: 20px; border-radius: 8px; text-align: center; page-break-inside: avoid; }
                    .chart-container img { max-width: 100%; height: auto; max-height: 400px; }
                    .footer { margin-top: 50px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Reporte Financiero y Crecimiento de Protocolo</h1>
                    <div class="subtitle">
                        <strong>Agrupación:</strong> ${horizonLabel}<br>
                        <strong>Fecha de Emisión:</strong> ${new Date().toLocaleDateString()}
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Crecimiento de Capital Procesado (USD)</h3>
                    <img src="${imgVol}" />
                </div>

                <div class="chart-container">
                    <h3>Nuevos Usuarios / Agentes KYA Registrados</h3>
                    <img src="${imgAg}" />
                </div>

                <div class="chart-container">
                    <h3>Comisiones Recaudadas (USD)</h3>
                    <img src="${imgFees}" />
                </div>
                
                <div class="footer">
                    <p><em>Documento generado automáticamente por el Panel Analítico de iAgent-Pay.</em></p>
                </div>
            </body>
        </html>
    `);
    w.document.close();
    setTimeout(() => { w.print(); }, 500);
});

// EXPORT TO EXCEL
document.getElementById('btnAdvExportExcel')?.addEventListener('click', () => {
    if (!window._advReportData) return;
    const data = window._advReportData;
    
    let csv = "data:text/csv;charset=utf-8,Periodo,Volumen USD,Comisiones USD,Nuevos Agentes\n";
    for (let i = 0; i < data.labels.length; i++) {
        csv += `${data.labels[i]},${data.volume[i]},${data.fees[i]},${data.agents[i]}\n`;
    }
    
    const encodedUri = encodeURI(csv);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "iAgentPay_Analitica_Detallada.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
});

// ══════════════════════════════════════════════════════════
// REGISTRO DE ERRORES (HELP DESK)
// ══════════════════════════════════════════════════════════
window.loadErrors = async function() {
    const tbody = document.getElementById('errorsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-600 py-8">Cargando errores...</td></tr>';

    try {
        const res = await authFetch('/api/admin/errors');
        if (!res.ok) throw new Error('Error fetching error logs');
        const data = await res.json();
        
        const errors = data.errors || [];
        if (errors.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-600 py-8">🎉 ¡Excelente! No hay errores registrados.</td></tr>';
            return;
        }

        tbody.innerHTML = errors.map(e => {
            const date = new Date(e.timestamp * 1000).toLocaleString();
            const isSolved = e.status === 'SOLVED';
            const rowClass = isSolved ? 'opacity-50' : 'hover:bg-red-900/20';
            const statusLabel = isSolved ? '<span class="text-emerald-500">✅ Resuelto</span>' : '<span class="text-red-500">⚠️ Pendiente</span>';
            const btn = isSolved ? '' : `<button onclick="resolveError(${e.id})" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold transition">Marcar Resuelto</button>`;
            
            return `<tr class="transition-colors border-b border-gray-800/50 ${rowClass}">
                <td class="px-4 py-3 font-mono text-gray-500">#${e.id}</td>
                <td class="px-4 py-3">${date}</td>
                <td class="px-4 py-3 font-mono text-gray-400">${e.user_address || 'Anonymous'}</td>
                <td class="px-4 py-3 font-bold text-gray-300">
                    ${e.error_message}
                    ${e.stack_trace ? `<p class="text-xs font-mono text-gray-500 mt-1 break-all">${e.stack_trace.substring(0, 100)}...</p>` : ''}
                </td>
                <td class="px-4 py-3">${statusLabel}</td>
                <td class="px-4 py-3">${btn}</td>
            </tr>`;
        }).join('');

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-8">Error: ${err.message}</td></tr>`;
    }
};

window.resolveError = async function(id) {
    if(!confirm('¿Estás seguro de marcar este error como resuelto?')) return;
    try {
        const res = await authFetch('/api/admin/errors/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        });
        if (!res.ok) throw new Error('Fallo al resolver el error');
        loadErrors();
    } catch (err) {
        alert('Error: ' + err.message);
    }
};

// ══════════════════════════════════════════════════════════
// DATABASE RESET
// ══════════════════════════════════════════════════════════
document.getElementById('resetDbBtn')?.addEventListener('click', async () => {
    if(!confirm('⚠️ ADVERTENCIA EXTREMA ⚠️\n\nEstás a punto de borrar TODOS los registros, transacciones, reputación, contratos escrow, recibos y errores.\n\nEsta acción es IRREVERSIBLE. ¿Estás absolutamente seguro?')) return;
    
    try {
        if (!window.ethereum) throw new Error("MetaMask no está instalado.");
        const provider = new ethers.providers.Web3Provider(window.ethereum);
        const signer = provider.getSigner();
        const address = await signer.getAddress();
        
        const message = "Confirmar reseteo total de la base de datos de iAgentPay.";
        const signature = await signer.signMessage(message);
        
        const res = await authFetch('/api/admin/reset_db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ signature, address })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al resetear la base de datos');
        
        alert('✅ ' + data.message);
        window.location.reload();
    } catch (err) {
        showToastError('Fallo el Reseteo: ' + err.message);
    }
});

