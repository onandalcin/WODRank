import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="wide", page_icon="🏆")

# --- DESIGN SYSTEM ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: #0E1117; color: #E0E0E0; }}
        [data-testid="stSidebar"] {{ background-color: #161B22; border-right: 1px solid #30363D; }}
        .stButton>button {{
            width: 100%; border-radius: 12px;
            background: linear-gradient(90deg, #FF4B4B 0%, #CC3333 100%);
            color: white; border: none; padding: 12px; font-weight: 700;
            text-transform: uppercase; transition: 0.3s all;
        }
        .stButton>button:hover {{ transform: scale(1.02); box-shadow: 0 0 15px rgba(255, 75, 75, 0.4); }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        .stTabs [aria-selected="true"] {{ color: #FF4B4B !important; border-bottom: 2px solid #FF4B4B !important; }}
        [data-testid="stMetricValue"] {{ color: #FF4B4B; font-weight: 800; }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.markdown("### 🔥 PERFORMANCE")
    st.write("Cada segundo conta na busca pela elite.")
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

# --- DASHBOARD ---
st.markdown("<h1 style='color: white;'>WOD Ranking <span style='color: #FF4B4B;'>Pro</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8B949E; margin-top: -20px;'>Onde cada repetição conta.</p>", unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🏆 ELITE WODRANK"])

# --- REGISTRO ---
with aba1:
    col_l, col_r = st.columns([1, 1], gap="large")
    with col_l:
        st.markdown("### 📥 Entrada")
        data_treino = st.date_input("Data do WOD", datetime.now())
        txt_input = st.text_area("Lista (NOME TEMPO)", height=200)
        
        if st.button("GERAR PRÉVIA"):
            if txt_input:
                dados = []
                # CORREÇÃO AQUI: String literal fechada corretamente
                linhas = txt_input.strip().split('\n')
                for l in linhas:
                    try:
                        p = l.rsplit(' ', 1)
                        nome, tempo = p[0].upper(), p[1].replace("'", ":")
                        m, s = map(int, tempo.split(':'))
                        dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Nome": nome, "Tempo": tempo, "Segundos": m*60+s})
                    except: continue
                if dados:
                    st.session_state.ready_to_save = dados
                    st.session_state.show_preview = True
    
    with col_r:
        if st.session_state.get("show_preview"):
            st.markdown("### 👀 Preview")
            st.table(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)))
            if st.button("🚀 SALVAR NO BANCO"):
                requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                st.success("Sincronizado!")
                st.balloons()
                st.session_state.show_preview = False

# --- HISTÓRICO ---
with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Escolha a Data:", datas)
            st.table(formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel]))
    except: st.info("Aguardando registros...")

# --- ELITE RANK ---
with aba3:
    st.markdown("### 🔥 Tabela da Elite")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Atletas", df_geral["Nome"].nunique())
            c2.metric("WODs", len(df_geral["Data"].unique()))
            c3.metric("Líder", df_geral.groupby("Nome").size().idxmax())

            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia
