import streamlit as st
import sqlite3
import pandas as pd
import time
import plotly.express as px
from datetime import datetime

# Page Config (Neutral or Spanish default)
st.set_page_config(
    page_title="iAgentPay Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Styling for "Premium" Look & Localization ---
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stMetricValue {
        color: #00FF94 !important;
        font-family: 'Courier New', monospace;
    }
    .stMetricLabel {
        color: #AAAAAA !important;
    }
    
    /* HIDE STREAMLIT UNTRANSLATED ELEMENTS */
    /* This is critical to prevent English menus from showing */
    #MainMenu {visibility: hidden;}  /* Three-dot menu */
    header {visibility: hidden;}     /* Top bar */
    footer {visibility: hidden;}     /* "Made with Streamlit" */
    
    /* Specifically hide the Deploy button if visible */
    [data-testid="stDeployButton"] {
        display: none;
    }
    .stDeployButton {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Internationalization (i18n) ---
LANG = {
    "Español": {
        "title": "🤖 Centro de Control AgentPay",
        "status": "**Estado:** 🟢 Sistema Online | **Red:** Multi-Chain Activa",
        "refresh": "🔄 Actualizar Datos",
        "no_data": "⚠️ Aún no hay historial de transacciones. ¡Inicia tus agentes!",
        "total_vol": "Volumen Total (ETH)",
        "total_txs": "Transacciones Totales",
        "success_rate": "Tasa de Éxito",
        "last_active": "Última Actividad",
        "vol_chart_title": "Transacciones por Minuto (TPM)",
        "status_chart_title": "Desglose por Estado",
        "ledger_title": "📝 Libro Mayor en Vivo",
        "telemetry_title": "🌍 Nodos Activos (Telemetría)",
        "telemetry_info": "ℹ️ Rastreando solo Nodo Local. Despliega un 'Nodo Colector' para estadísticas globales.",
        "col_hash": "ID Rastreo (Hash)",
        "col_time": "Tiempo",
        "col_amount": "Monto (ETH)",
        "col_status": "Estado",
        "sidebar_lang": "Idioma / Language"
    },
    "English": {
        "title": "🤖 AgentPay Control Center",
        "status": "**Status:** 🟢 System Online | **Network:** Multi-Chain Active",
        "refresh": "🔄 Refresh Data",
        "no_data": "⚠️ No transaction history found yet. Start your agents!",
        "total_vol": "Total Volume (ETH)",
        "total_txs": "Total Transactions",
        "success_rate": "Success Rate",
        "last_active": "Last Active",
        "vol_chart_title": "Transactions per Minute (TPM)",
        "status_chart_title": "Tx Status Breakdown",
        "ledger_title": "📝 Live Transaction Ledger",
        "telemetry_title": "🌍 Active Client Nodes (Telemetry)",
        "telemetry_info": "ℹ️ Currently tracking Local Node only. Deploy 'Collector Node' to see global user stats.",
        "col_hash": "Trace ID (Hash)",
        "col_time": "Time",
        "col_amount": "Amount (ETH)",
        "col_status": "Status",
        "sidebar_lang": "Language / Idioma"
    }
}

# Language Selector (Default: Español)
# Note: Streamlit selectbox default is index 0
l_options = ["Español", "English"]
selected_lang = st.sidebar.selectbox("🌐 Idioma / Language", l_options, index=0)
T = LANG[selected_lang]

# --- Database Connection ---
DB_PATH = "agent_history.db"

def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        # Assuming table is named 'transactions' with cols: timestamp, tx_hash, recipient, amount, status
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
        conn.close()
        
        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
    except Exception as e:
        return pd.DataFrame()

# --- Main App ---
st.title(T["title"])
st.markdown(T["status"])

# Auto-Refresh Button
if st.button(T["refresh"]):
    st.cache_data.clear()

df = load_data()

if df.empty:
    st.warning(T["no_data"])
else:
    # --- KPI Metrics ---
    total_vol = df['amount'].sum()
    total_txs = len(df)
    success_rate = (len(df[df['status'] == 'CONFIRMED']) / total_txs) * 100 if total_txs > 0 else 0
    last_active = df['datetime'].max().strftime('%H:%M:%S')

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(T["total_vol"], f"Ξ {total_vol:.4f}")
    col2.metric(T["total_txs"], f"{total_txs}")
    col3.metric(T["success_rate"], f"{success_rate:.1f}%")
    col4.metric(T["last_active"], f"{last_active}")

    # --- Layout: Charts ---
    st.markdown("---")
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader(f"📈 {T['vol_chart_title']}")
        # Group by minute for HFT view, or hour for long term
        df_grouped = df.set_index('datetime').resample('1min')['amount'].count().reset_index()
        fig = px.area(df_grouped, x='datetime', y='amount', 
                      title=T['vol_chart_title'],
                      template="plotly_dark",
                      color_discrete_sequence=['#00FF94'])
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader(f"📊 {T['status_chart_title']}")
        fig2 = px.pie(df, names='status', title=T['status_chart_title'], 
                      hole=0.4, 
                      color_discrete_map={'CONFIRMED':'#00FF94', 'PENDING':'#FFC107', 'FAILED':'#FF5252'})
        st.plotly_chart(fig2, use_container_width=True)

    # --- Recent Transactions Table ---
    st.markdown("---")
    st.subheader(T["ledger_title"])
    
    # Styling the dataframe
    st.dataframe(
        df[['datetime', 'tx_hash', 'recipient', 'amount', 'status']].sort_values(by='datetime', ascending=False),
        column_config={
            "tx_hash": T["col_hash"],
            "datetime": T["col_time"],
            "amount": st.column_config.NumberColumn(T["col_amount"], format="%.5f"),
            "status": st.column_config.TextColumn(T["col_status"]),
        },
        use_container_width=True,
        hide_index=True
    )

    # --- Telemetry Section (The "Who is using it?" question) ---
    st.markdown("---")
    st.subheader(T["telemetry_title"])
    st.info(T["telemetry_info"])
    st.code(f"Current Node ID: {df['recipient'].unique()[0] if not df.empty else 'Unknown'}", language="text")
