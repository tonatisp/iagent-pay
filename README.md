<div align="center">
  <img src="https://img.shields.io/badge/iAgentPay-v5.0.0-blue?style=for-the-badge&logo=python" alt="iAgentPay Version" />
  <img src="https://img.shields.io/badge/Coverage-100%25-brightgreen?style=for-the-badge" alt="Coverage" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  
  <h1>🤖💸 iAgentPay</h1>
  <p><b>La infraestructura bancaria estándar para Agentes de IA Autónomos.</b></p>
</div>

iAgentPay permite a cualquier sistema de Inteligencia Artificial (CrewAI, LangChain, Claude, Cursor) poseer su propia billetera, manejar presupuestos, y realizar pagos tanto en **Criptomonedas (USDC en Solana/Base)** como en **Dinero Fiat (Stripe/ACH)**, todo protegido por un Kernel de Seguridad atómico.

---

## 🌟 ¿Por qué iAgentPay? (vs La Competencia)

A diferencia de otras soluciones diseñadas para humanos y adaptadas a la fuerza para IA, **iAgentPay nació nativamente para agentes autónomos.**

| Característica | iAgentPay v5.0 | Coinbase AgentKit | Stripe Agent Toolkit | OmniAgentPay |
| :--- | :---: | :---: | :---: | :---: |
| **Multi-Cadena Real** | ✅ (Base, Solana, XRPL) | ❌ (Solo EVM) | ❌ (No Crypto) | ✅ |
| **Fiat Bridge (Stripe/ACH)** | ✅ (Smart Routing) | ❌ | ✅ | ❌ |
| **Safety Kernel (Límites)** | ✅ (Atómico / Hilos) | ⚠️ (Básico) | ❌ | ✅ |
| **Sub-Agentes (Flotas)** | ✅ (Límites aislados) | ❌ | ❌ | ❌ |
| **Know Your Agent (KYA)** | ✅ (DID + Reputación) | ❌ | ❌ | ❌ |
| **HTTP 402 Autopay** | ✅ (x402 Protocol) | ❌ | ❌ | ❌ |

---

## ⚡ Instalación Rápida

Instala el SDK completo o módulos específicos según tus necesidades:

```bash
pip install "iagent-pay"            # Core SDK
pip install "iagent-pay[fastapi]"   # Para montar servidores x402
pip install "iagent-pay[crewai]"    # Para agentes de CrewAI
pip install "iagent-pay[fiat]"      # Para usar Stripe/ACH
pip install "iagent-pay[all]"       # Instalar todo
```

Inicia tu proyecto en segundos con nuestro CLI:
```bash
iagent-pay init mi-proyecto-ia
```

---

## 🚀 Quickstart (En 1 minuto)

### 1. El Safety Kernel (Límites de Gasto)
Nunca dejes a tu IA con una billetera sin límites. El Kernel bloquea gastos anómalos.

```python
from iagent_pay.safety_kernel import SafetyKernel, SafetyConfig

kernel = SafetyKernel(SafetyConfig(
    daily_limit_usd=50.0,       # Máximo $50 al día
    max_tx_usd=10.0,            # Máximo $10 por transacción
    enable_whitelist=True,
    allowed_recipients=["0xTrustedVendor..."]
))

# El agente intenta gastar $5.0 (Aprobado ✅)
kernel.check(amount=5.0, recipient="0xTrustedVendor...")

# El agente es hackeado e intenta gastar $100 (Bloqueado ❌)
# Lanza: TransactionCapExceeded
kernel.check(amount=100.0, recipient="0xHacker...") 
```

### 2. Smart Routing (Crypto vs Fiat)
Delega al SDK la decisión de qué riel de pago usar dependiendo del destinatario.

```python
from iagent_pay.fiat_bridge import FiatBridge

bridge = FiatBridge(stripe_key="sk_live_...")

# Automáticamente usa USDC en Base/Solana (Es una wallet cripto)
bridge.smart_send(10.0, recipient="0xAliceWallet...") 

# Automáticamente crea un Stripe Invoice (Es un email)
bridge.smart_send(10.0, recipient="freelancer@gmail.com", description="Pago de diseño")
```

### 3. Integración con CrewAI
Dale a tu agente el poder de pagar autónomamente.

```python
from crewai import Agent
from iagent_pay.integrations.crewai import iAgentPayTool

agent = Agent(
    role='Comprador de Datos',
    goal='Comprar los mejores datasets de internet',
    tools=[iAgentPayTool(daily_limit_usd=15.0)],
    verbose=True
)
```

---

## 🛡️ Arquitectura Empresarial (v5.0)

iAgentPay está dividido en submódulos modulares listos para producción:

1. **`usdc_driver`**: Motor de transacciones nativas en Solana, Base y XRPL.
2. **`x402_client / server`**: Implementación del estándar HTTP 402 para micro-pagos M2M (Machine to Machine).
3. **`safety_kernel`**: Bloqueos atómicos con `threading.Lock` para evitar race-conditions en flotas de agentes.
4. **`webhooks`**: Sistema de notificaciones HMAC-SHA256 con retries de backoff exponencial.
5. **`kya`**: (Know Your Agent) Reputación descentralizada mediante DIDs y puntuación ART.
6. **`observability`**: Dashboards en consola, logs en JSON y exportación a Prometheus/OpenTelemetry.

---

## 🌍 Open Source & Comunidad
iAgentPay es 100% Open Source (MIT). Construido para la próxima generación de la economía autónoma.

¿Quieres contribuir?
1. Haz un Fork del proyecto.
2. Crea tu rama (`git checkout -b feature/AmazingFeature`).
3. Haz Commit (`git commit -m 'Add some AmazingFeature'`).
4. Haz Push (`git push origin feature/AmazingFeature`).
5. Abre un Pull Request.
