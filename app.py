import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES DEFINITIVAS ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CUSTOM CSS (OTIMIZADO PARA CELULAR) ---
st.markdown("""
    <style>
        /* Ajuste para preencher melhor a tela do celular */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        
        /* Botões grandes para facilitar o toque (Thumb-friendly) */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 50px;
            background-color: #1E1E1E;
            color: white;
            border: none;
            font-weight: bold;
            font-size: 16px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #FF4B4B;
            color: white;
        }

        /* Inputs de texto otimizados */
        .stTextArea textarea {
            border-radius: 10px !important;
            font-size: 16px !important;
        }

        /* Abas mais fáceis de clicar */
        .stTabs [data-baseweb="tab"] {
            padding: 10px 15px;
            font-size: 14px;
        }
        
        /* Ajuste de títulos para telas pequenas */
        h1 { font-size: 26px !important; }
        
        /* Ocultar elementos desnecessários do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown(f"""
    <div style='display: flex; flex-direction: column; align-items: center; text-align: center; border-bottom: 3px solid #FF4B4B; padding-bottom: 15px; margin-bottom: 20px;'>
        <img src='{URL_LOGO}' style='max-height: 70px; width: auto; margin-bottom: 10px;'>
        <div>
            <h1 style='margin: 0; color: #1E1E1E; font-family: sans-serif;'>WOD Ranking Pro</h1>
            <p style='margin: 0; font-size: 14px; font-style: italic; color: #FF4B4B;'>Onde cada repetição conta.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def formatar_ranking(df):
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

# --- INTERFACE ---
aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar WOD")
    data_treino = st.date_input("Data do Treino", datetime.now())
    txt_input = st.text_area("Resultados", height=150, placeholder="Ex: JOÃO 15:30")
    
    if st.button("GERAR PRÉVIA"):
        if txt_input:
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
                st.session_state.display_df = formatar_ranking(pd.DataFrame(dados))

    if "display_df" in st.session_state:
        st.markdown("---")
        st.dataframe(st.session_state.display_df, use_container_width=True, hide_index=True)
        if st.button("💾 CONFIRMAR E SALVAR"):
            with st.spinner("Enviando..."):
                requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                st.success("✅ Salvo com sucesso!")
                st.balloons()
                del st.session_state.display_df

with aba2:
    st.markdown("### 🔍 Consultar Treinos")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        datas = df_hist["Data"].unique()
        data_sel = st.selectbox("Selecione o dia:", datas[::-1])
        st.dataframe(formatar_ranking(df_hist[df_hist["Data"] == data_sel]), use_container_width=True, hide_index=True)
    except: st.info("Buscando dados...")

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            # Métricas rápidas no topo
            c1, c2 = st.columns(2)
            c1.metric("Atletas", df_geral["Nome"].nunique())
            c2.metric("Total WODs", len(df_geral["Data"].unique()))
            
            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            df_concat = pd.concat(lista_acumulada)
            rank_final = df_concat.groupby("Nome").agg(Total_Pontos=('Pontos', 'sum'), WODs=('Nome', 'count')).sort_values("Total_Pontos", ascending=False).reset_index()
            
            def trofeu_rank(i):
                if i == 0: return "🥇"
                if i == 1: return "🥈"
                if i == 2: return "🥉"
                return f"{i+1}º"

            rank_final['#'] = [trofeu_rank(i) for i in range(len(rank_final))]
            rank_final = rank_final[['#', 'Nome', 'WODs', 'Total_Pontos']]
            rank_final.columns = ['#', 'ATLETA', 'WDS', 'PTS']
            
            st.dataframe(rank_final.style.highlight_max(axis=0, subset=['PTS'], color='#FEF3C7'), use_container_width=True, hide_index=True)
    except: st.info("Aguardando registros.")
