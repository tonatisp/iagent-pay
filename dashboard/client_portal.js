// client_portal.js

let isWalletConnected = false;
let userWallet = "";

// Elementos del DOM
const sliderDaily = document.getElementById("sliderDailyLimit");
const sliderTx = document.getElementById("sliderTxLimit");
const valDaily = document.getElementById("valDailyLimit");
const valTx = document.getElementById("valTxLimit");
const chkDisclaimer = document.getElementById("chkDisclaimer");
const btnGenerate = document.getElementById("btnGenerate");
const txtWhitelist = document.getElementById("txtWhitelist");
const btnConnect = document.getElementById("btnConnectWallet");
const resultBox = document.getElementById("resultBox");
const outputKey = document.getElementById("outputKey");

// Sincronizar sliders y valores
function updateValues() {
    valDaily.innerText = sliderDaily.value;
    valTx.innerText = sliderTx.value;
    
    // Si el límite por transacción es mayor al diario, forzar ajuste
    if (parseInt(sliderTx.value) > parseInt(sliderDaily.value)) {
        sliderTx.value = sliderDaily.value;
        valTx.innerText = sliderTx.value;
    }
    
    validateForm();
}

// Validar formulario para habilitar botón
function validateForm() {
    if (isWalletConnected && chkDisclaimer.checked) {
        btnGenerate.disabled = false;
    } else {
        btnGenerate.disabled = true;
    }
}

chkDisclaimer.addEventListener("change", validateForm);

// Simular conexión de Master Wallet
async function connectWallet() {
    btnConnect.innerHTML = `<svg class="animate-spin h-5 w-5 mr-3 border-t-2 border-emerald-400 rounded-full" viewBox="0 0 24 24"></svg> Conectando...`;
    
    // Simulación de delay Web3 (MetaMask, etc)
    setTimeout(() => {
        isWalletConnected = true;
        userWallet = "0x" + Math.random().toString(16).substr(2, 40);
        
        btnConnect.innerHTML = `🟢 Conectado: ${userWallet.substring(0,6)}...${userWallet.substring(userWallet.length-4)}`;
        btnConnect.classList.replace("text-emerald-400", "text-white");
        btnConnect.classList.replace("bg-emerald-500/10", "bg-emerald-600");
        
        validateForm();
    }, 1000);
}

// Enviar solicitud de generación de Session Key al Backend
async function generateKey() {
    if (!isWalletConnected || !chkDisclaimer.checked) return;
    
    btnGenerate.disabled = true;
    btnGenerate.innerHTML = `<svg class="animate-spin h-6 w-6 mx-auto border-t-2 border-white rounded-full" viewBox="0 0 24 24"></svg>`;
    resultBox.classList.add("hidden");
    
    const whitelistRaw = txtWhitelist.value.trim();
    let whitelistArray = [];
    if (whitelistRaw) {
        whitelistArray = whitelistRaw.split("\n").map(addr => addr.trim()).filter(addr => addr.length > 0);
    }
    
    const payload = {
        master_wallet: userWallet,
        daily_limit: parseFloat(sliderDaily.value),
        tx_limit: parseFloat(sliderTx.value),
        whitelist: whitelistArray,
        auto_yield: document.getElementById('chkAutoYield').checked,
        accepted_disclaimer: true
    };
    
    try {
        const response = await fetch('/api/client/generate_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            outputKey.textContent = JSON.stringify(data.session_key, null, 2);
            resultBox.classList.remove("hidden");
            
            // Scroll to result
            resultBox.scrollIntoView({ behavior: 'smooth', block: 'end' });
        } else {
            alert("Error: " + (data.error || "Desconocido"));
        }
    } catch (error) {
        console.error("Fetch error:", error);
        alert("Server connection failed.");
    } finally {
        // Retrieve original text based on language
        const lang = document.getElementById("langSelect").value;
        const dict = (typeof TRANSLATIONS !== 'undefined' && TRANSLATIONS[lang]) ? TRANSLATIONS[lang] : TRANSLATIONS['es'];
        btnGenerate.innerHTML = `<span data-i18n="cpGenerateBtn">${dict.cpGenerateBtn || 'Generar Session Key ⚡'}</span>`;
        validateForm(); // Re-evaluar estado del botón
    }
}

function copyKey() {
    navigator.clipboard.writeText(outputKey.textContent).then(() => {
        const lang = document.getElementById("langSelect").value;
        const dict = (typeof TRANSLATIONS !== 'undefined' && TRANSLATIONS[lang]) ? TRANSLATIONS[lang] : TRANSLATIONS['es'];
        alert(dict.cpCopyAlert || "¡Session Key copiada al portapapeles! Inyéctala en tu agente.");
    }).catch(err => {
        console.error('Error al copiar: ', err);
    });
}

// Multilanguage logic
function changeLanguage(lang) {
    if (typeof TRANSLATIONS === 'undefined') return;
    
    const dict = TRANSLATIONS[lang] || TRANSLATIONS['es'];
    
    // Update elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            // Keep inner HTML structure if replacing span
            if (el.tagName === 'SPAN' && el.innerHTML.includes('<') && !el.innerHTML.includes('🔗')) {
                 el.innerText = dict[key];
            } else {
                 el.innerHTML = dict[key];
            }
        }
    });
}

// Inicialización
updateValues();
changeLanguage('es');
