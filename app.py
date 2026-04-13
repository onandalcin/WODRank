import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

# Layout 'centered' para foco total no conteúdo
st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- DESIGN SYSTEM LIGHT CENTRALIZADO ---
st.markdown(f"""
    <style>
        .stApp {{
            background-color: #FFFFFF;
            color: #2D3436;
        }}
        
        /* Centralização da Logo */
        .logo-container {{
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }}

        /* Botão de Ação */
        .stButton>button {{
            width: 100%;
            border-radius: 8px;
            background-color: #FF4B4B;
            color: white;
            border: none;
            padding: 12px;
            font-weight: 700;
            transition: 0.3s all;
        }}
        .stButton>button:hover {{
            background-color: #D63031;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
        }}

        /* Abas */
        .stTabs [data-baseweb="tab-list"] {{
            justify-content: center;
            gap: 15px;
        }}
        .stTabs [aria-selected="true"] {{
            color: #FF4B4B !important;
            border-bottom-color: #FF4B4B !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO CENTRAL ---
st.markdown(f"""
    <div class="logo-container">
        <img src="{URL_LOGO}" style="max-height: 100px;">
    </div>
    <h1 style='text-align: center; color: #1E1E1E; margin-bottom: 5px;'>Elite WODRank</h1>
    <p style='text-align: center; color: #636E72; font-style: italic; margin-bottom: 30px;'>Onde cada repetição conta.</p>
""", unsafe_allow_html=True)

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

# --- DASHBOARD CENTRAL ---
aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🏆 ELITE RANK"])

with aba1:
    st.markdown("### 📥 Registrar Treino")
    data_treino = st.date_input("Data do WOD", datetime.now())
    txt_input = st.text_area("Resultados (NOME TEMPO)", height=150, placeholder="Ex: JOÃO 12:45")
    
    if st.button("GERAR PRÉVIA"):
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
        st.subheader("Prévia do Ranking")
        st.table(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)))
        if st.button("🚀 SALVAR RESULTADOS"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Sincronizado com sucesso!")
            st.balloons()
            st.session_state.show_preview = False

with aba2:
    st.markdown("### 🔍 Histórico por Data")
    if st.button("🔄 Sincronizar"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Escolha o dia:", datas)
            st.table(formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel]))
    except: st.info("Buscando dados na planilha...")

with aba3:
    st.markdown("### 🔥 Top Performance Acumulada")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            # Métricas centrais
            m1, m2, m3 = st.columns(3)
            m1.metric("Atletas", df_geral["Nome"].nunique())
            m2.metric("WODs", len(df_geral["Data"].unique()))
            m3.metric("Frequência", f"{len(df_geral)/df_geral['Nome'].nunique():.1f}")

            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            rank_final = pd.concat(lista_acumulada).groupby("Nome").agg(
                PONTOS=('Pontos', 'sum'), WODS=('Nome', 'count')
            ).sort_values("PONTOS", ascending=False).reset_index()
            
            rank_final.insert(0, '#', [f"{i+1}º" for i in range(len(rank_final))])
            
            st.dataframe(
                rank_final.style.highlight_max(axis=0, subset=['PONTOS'], color='#FEF3C7'),
                use_container_width=True, hide_index=True
            )
            st.caption("PONTUAÇÃO: 1º(100), 2º(95), 3º(90), demais -1pt por posição.")
    except: st.info("O ranking aparecerá aqui após o primeiro registro.")
