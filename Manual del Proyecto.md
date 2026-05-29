# Manual del Proyecto: iAgent-Pay MVP

## 1. Descripción General
iAgent-Pay es una plataforma de procesamiento de pagos (Nivel Bancario - Tier 1). Permite transacciones, monitorización de historial en tiempo real y avanzadas capacidades de auditoría para operaciones Web3 y transferencias fiat.

El Dashboard principal (Frontend) y el servidor API (Backend) operan en conjunto para proporcionar herramientas administrativas de alto rendimiento.

## 2. Infraestructura y Credenciales

### 🖥️ Servidor VPS (Producción)
- **Dominio:** `iagent-pay.com`
- **IP Pública:** `187.124.76.64`
- **Usuario SSH:** `root`
- **Contraseña SSH:** `Santsantillan2-`

### 🔑 Credenciales del Dashboard de Administrador
- **Master Admin Wallet:** `0x0a094FFeCD1EAa996B6eb582a55400F1702768B2`
*(Esta es la billetera conectada con MetaMask que tiene privilegios maestros para firmar los desafíos criptográficos y acceder al panel de control de administrador).*

### 📁 Rutas Críticas en el Servidor (VPS)
- **Backend (API y App):** `/root/iagent_pay_app/`
- **Archivo Principal del Backend:** `/root/iagent_pay_app/serve_dashboard.py`
- **Base de Datos SQLite:** `/root/iagent_pay_app/agent_history.db`
- **Carpeta del Frontend Dashboard:** `/root/iagent_pay_app/dashboard/` (Aquí viven `admin.html`, `admin.js`, etc.)
- **Logs de Errores:** `/root/iagent_pay_app/dashboard.log`

## 3. Funcionamiento Técnico y Arquitectura

1. **El Backend:** Un script de Python puro (`serve_dashboard.py`) que se ejecuta de forma ininterrumpida. Proporciona una API RESTful robusta, gestiona la base de datos SQLite y maneja la autenticación segura Web3 comprobando firmas matemáticas de MetaMask. Se ejecuta internamente en el puerto `8000`.
2. **Proxy Inverso Nginx:** El servidor Nginx intercepta todo el tráfico de internet hacia tu dominio en los puertos HTTP/HTTPS, valida certificados de seguridad SSL de Certbot, y redirige ese tráfico limpio y seguro al backend local.
3. **El Frontend:** Programado en HTML, CSS y Vanilla JS. Consume las rutas API (`/api/transactions`, `/api/admin/...`) de forma asíncrona. 

## 4. Scripts de Mantenimiento y Automatización (Locales)
Dentro de este respaldo local, encontrarás los scripts de Python que hemos ido programando para operar el servidor de forma remota:

- **`deploy_new_features.py`**: Script automatizado de actualización. Sube la versión más reciente de tus archivos `admin.html`, `admin.js` y `serve_dashboard.py` al VPS a través de SFTP y reinicia el sistema de forma segura sin intervención manual.
- **`relaunch.py` / `patch_backend.py`**: Scripts para reiniciar configuraciones internas o disparar rutinas de simuladores/bots.
- **`bot_simulation_fixed.py`**: La lógica que inyecta pruebas de estrés de alta frecuencia a tu plataforma en producción sin ser bloqueado por los Firewalls.

## 5. Instrucciones para Arrancar/Reiniciar el Servidor Manualmente
Si algún día la interfaz web se paraliza y necesitas conectarte por la consola (`PuTTY` o terminal SSH) y repararlo manualmente, ejecuta los siguientes comandos una vez dentro del servidor:

**1. Matar/Detener la versión actual corriendo:**
```bash
pkill -f "serve_dashboard.py"
```

**2. Navegar a la carpeta correcta:**
```bash
cd /root/iagent_pay_app
```

**3. Volver a arrancar el sistema oculto en segundo plano:**
```bash
nohup /root/iagent_pay_app/venv/bin/python serve_dashboard.py > dashboard.log 2>&1 &
```

*(Si necesitas leer los registros para ver si ocurrió algún error en tiempo real, puedes usar el comando: `cat dashboard.log`)*
