import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="wide", page_icon="🏆")

# --- DESIGN SYSTEM (LATARIA CUSTOMIZADA) ---
st.markdown(f"""
    <style>
        /* Fundo Geral */
        .stApp {{
            background-color: #0E1117;
            color: #E0E0E0;
        }}
        
        /* Sidebar Estilizada */
        [data-testid="stSidebar"] {{
            background-color: #161B22;
            border-right: 1px solid #30363D;
        }}
        
        /* Estilo dos Títulos e Textos */
        h1, h2, h3 {{
            font-family: 'Inter', sans-serif;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }}
        
        /* Custom Card (Efeito de Profundidade) */
        .div-card {{
            background-color: #1C2128;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #30363D;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            margin-bottom: 20px;
        }}

        /* Botão Principal */
        .stButton>button {{
            width: 100%;
            border-radius: 12px;
            background: linear-gradient(90deg, #FF4B4B 0%, #CC3333 100%);
            color: white;
            border: none;
            padding: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: 0.3s all;
        }}
        .stButton>button:hover {{
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(255, 75, 75, 0.4);
        }}

        /* Tabs (Abas) Customizadas */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 24px;
            background-color: transparent;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            background-color: transparent;
            border: none;
            color: #8B949E;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            color: #FF4B4B !important;
            border-bottom: 2px solid #FF4B4B !important;
        }}
        
        /* Métricas */
        [data-testid="stMetricValue"] {{
            color: #FF4B4B;
            font-weight: 800;
        }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🔥 PERFORMANCE")
    st.write("Bem-vindo à Elite. Aqui, cada repetição é registrada e cada segundo é disputado.")
    st.divider()
    st.caption("Onan Dal Cin | Petroleum Engineer")

# --- FUNÇÕES ---
def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.sort_values("Segundos").reset_index(drop=True)
    df.index += 1
    df['Pos'] = [f"{i}º" for i in df.index]
    if len(df) >= 1: df.loc[1, 'Pos'] = "🥇"
    if len(df) >= 2: df.loc[2, 'Pos'] = "🥈"
    if len(df) >= 3: df.loc[3, 'Pos'] = "🥉"
    return df[['Pos', 'Nome', 'Tempo']]

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    if pos == 3: return 90
    return max(10, 90 - (pos - 3))

# --- DASHBOARD PRINCIPAL ---
st.markdown("<h1 style='color: white;'>WOD Ranking <span style='color: #FF4B4B;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8B949E; margin-top: -20px;'>Onde cada repetição conta.</p>", unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🏆 ELITE WODRANK"])

# --- REGISTRO ---
with aba1:
    col_l, col_r = st.columns([1, 1], gap="large")
    with col_l:
        st.markdown("### 📥 Input")
        data_treino = st.date_input("Data do WOD", datetime.now())
        txt_input = st.text_area("Lista de Resultados", height=200, placeholder="DICA: NOME TEMPO (ex: PAULO 12:45)")
        if st.button("VISUALIZAR RANKING"):
            if txt_input:
                dados = []
                for l in txt_input.strip().split('\n
