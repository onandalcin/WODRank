import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="wide", page_icon="🏆")

# --- CSS AVANÇADO (LATARIA PREMIUM) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        /* Estilo dos Cards de Métricas */
        [data-testid="stMetricValue"] { font-size: 28px; font-weight: 900; color: #FF4B4B; }
        
        /* Botões Arredondados e Modernos */
        .stButton>button {
            border-radius: 12px;
            background: linear-gradient(145deg, #1e1e1e, #2a2a2a);
            color: white;
            border: none;
            padding: 10px 24px;
            font-weight: 700;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            background: #FF4B4B;
            box-shadow: 0 6px 20px rgba(255, 75, 75, 0.4);
        }

        /* Tabs Personalizadas */
        .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            font-weight: 700;
            color: #888;
            border-radius: 8px;
            padding: 8px 20px;
        }
        .stTabs [aria-selected="true"] { color: #FF4B4B !important; border-bottom: 3px solid #FF4B4B !important; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (IDENTIDADE VISUAL) ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.title("WOD Ranking Pro")
    st.markdown("---")
    st.markdown("### 📣 Slogan")
    st.info("*Onde cada repetição conta.*")
    st.markdown("---")
    st.caption("v2.0 | Pro Dashboard")

# --- LÓGICA DE DADOS ---
def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    if pos == 3: return 90
    return max(10, 90 - (pos - 3))

def formatar_tabela_bonita(df):
    df = df.sort_values("Segundos").reset_index(drop=True)
    df.index += 1
    df['Pos'] = [f"{i}º" for i in df.index]
    if len(df) >= 1: df.loc[1, 'Pos'] = "🥇"
    if len(df) >= 2: df.loc[2, 'Pos'] = "🥈"
    if len(df) >= 3: df.loc[3, 'Pos'] = "🥉"
    return df[['Pos', 'Nome', 'Tempo']]

# --- CONTEÚDO PRINCIPAL ---
st.title("🚀 Dashboard de Performance")

aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR WOD", "📅 HISTÓRICO", "🔥 ELITE WODRANK"])

with aba1:
    col_input, col_preview = st.columns([1, 1], gap="large")
    
    with col_input:
        st.markdown("### 📥 Entrada de Dados")
        data_treino = st.date_input("Data do Treino", datetime.now())
        txt_input = st.text_area("Resultados (Formato: Nome Tempo)", height=250, placeholder="PEDRO 12:40\nANA 13:05")
        btn_preview = st.button("👁️ Visualizar Ranking")

    with col_preview:
        if btn_preview and txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    p = l.rsplit(' ', 1)
                    nome, tempo = p[0].upper(), p[1].replace("'", ":")
                    m, s = map(int, tempo.split(':'))
                    dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Nome": nome, "Tempo": tempo, "Segundos": m*60+s})
                except: continue
            
            if dados:
                st.session_state.ready_to_save = dados
                preview_df = formatar_tabela_bonita(pd.DataFrame(dados))
                st.markdown("### 📊 Prévia do Ranking")
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
                
                if st.button("🚀 CONFIRMAR E SALVAR"):
                    requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    st.success("✅ Sincronizado com o Google Sheets!")
                    st.balloons()

with aba2:
    st.markdown("### 🔍 Consulta de Treinos")
    if st.button("🔄 Sincronizar Histórico"): st.cache_data.clear()
    
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        datas = df_hist["Data"].unique()
        data_sel = st.selectbox("Selecione o dia do WOD:", datas[::-1])
        
        # Filtro
