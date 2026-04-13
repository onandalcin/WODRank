import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CSS MOBILE-FIRST (LATARIA OTIMIZADA) ---
st.markdown(f"""
    <style>
        /* Ajuste de Margens Mobile */
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }}
        
        /* Fontes adaptáveis */
        h1 {{ font-size: 24px !important; text-align: center; }}
        h3 {{ font-size: 18px !important; }}
        
        /* Botões Estilo Mobile */
        .stButton>button {{
            width: 100%;
            height: 50px;
            border-radius: 12px;
            font-size: 16px;
            text-transform: uppercase;
            background-color: #FF4B4B;
            font-weight: bold;
        }}

        /* Inputs mais altos para toque */
        .stTextArea textarea {{
            font-size: 16px !important;
        }}

        /* Estilização das Abas para Mobile */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 5px;
        }}
        .stTabs [data-baseweb="tab"] {{
            padding-left: 10px;
            padding-right: 10px;
            font-size: 12px;
        }}

        /* Esconder o menu do Streamlit para parecer App */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- LOGO CENTRALIZADA (AUMENTADA EM 3X) ---
# Alterado de width="80" para height="240" (aprox. 3x a altura visual anterior de 80px)
st.markdown(f'<div style="text-align: center; margin-top: -20px; margin-bottom: 20px;"><img src="{URL_LOGO}" height="240"></div>', unsafe_allow_html=True)
st.markdown("<h1 style='margin-bottom: 0;'>Elite WODRank</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 14px;'>Cada repetição conta.</p>", unsafe_allow_html=True)

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

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 RANKING"])

with aba1:
    st.markdown("### 📥 Adicionar Resultados")
    data_treino = st.date_input("Data", datetime.now())
    txt_input = st.text_area("Lista (NOME TEMPO)", height=150, placeholder="Ex: NEYMAR 12:45")
    
    if st.button("VISUALIZAR"):
        if txt_input:
            dados = []
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

    if st.session_state.get("show_preview"):
        st.markdown("---")
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("💾 SALVAR TUDO"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Salvo!")
            st.balloons()
            st.session_state.show_preview = False

with aba2:
    st.markdown("### 🔍 Consultar")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st
