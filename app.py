import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES DEFINITIVAS ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CUSTOM CSS (A LATARIA) ---
st.markdown("""
    <style>
        /* Fundo do App */
        .main { background-color: #f8f9fa; }
        
        /* Estilização dos Botões */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #1E1E1E;
            color: white;
            border: none;
            font-weight: bold;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #FF4B4B;
            color: white;
            border: none;
        }

        /* Input de Texto */
        .stTextArea textarea {
            border-radius: 10px !important;
            border: 1px solid #ddd !important;
        }

        /* Tabelas */
        .stDataFrame, .stTable {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        /* Tabs (Abas) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #eeeeee;
            border-radius: 5px 5px 0 0;
            padding: 10px 20px;
            font-weight: bold;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FF4B4B !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 20px; border-bottom: 3px solid #FF4B4B; padding-bottom: 20px; margin-bottom: 30px;'>
        <img src='{URL_LOGO}' style='max-height: 90px; width: auto; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2));'>
        <div>
            <h1 style='margin: 0; font-size: 32px; color: #1E1E1E; font-family: sans-serif;'>WOD Ranking Pro</h1>
            <p style='margin: 0; font-size: 18px; font-style: italic; color: #FF4B4B; font-weight: 500;'>Onde cada repetição conta.</p>
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
aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE WODRANK"])

with aba1:
    with st.container():
        st.markdown("### 📝 Entrada de Dados")
        col_data, col_vazio = st.columns([1,1])
        data_treino = col_data.date_input("Data do Treino", datetime.now())
        
        txt_input = st.text_area("Lista de Resultados", height=150, placeholder="Ex: JOÃO 15:30\nMARIA 16:45")
        
        if st.button("GERAR PRÉVIA DO RANKING"):
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
        st.subheader(f"📊 Resultado: {data_treino.strftime('%d/%m/%Y')}")
        st.table(st.session_state.display_df)
        if st.button("💾 CONFIRMAR E ENVIAR PARA NUVEM"):
            with st.spinner("Sincronizando..."):
                requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                st.success("✅ Tudo pronto! Pontos computados.")
                del st.session_state.display_df

with aba2:
    st.markdown("### 🔍 Consulta de Treinos")
    if st.button("🔄 ATUALIZAR BANCO DE DADOS"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        datas = df_hist["Data"].unique()
        data_sel = st.selectbox("Selecione o dia do WOD:", datas[::-1])
        st.table(formatar_ranking(df_hist[df_hist["Data"] == data_sel]))
    except: st.info("Nenhum dado encontrado.")

with aba3:
    st.markdown("### 🏆 Top Performance Acumulada")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            df_concat = pd.concat(lista_acumulada)
            rank_final = df_concat.groupby("Nome").agg(Total_Pontos=('Pontos', 'sum'), WODs=('Nome', 'count')).sort_values("Total_Pontos", ascending=False).reset_index()
            
            def trofeu_rank(i):
                if i == 0: return "🏆 CAMPEÃO"
                if i == 1: return "🥈 VICE"
                if i == 2: return "🥉 3º LUGAR"
                return f"{i+1}º"

            rank_final['Rank'] = [trofeu_rank(i) for i in range(len(rank_final))]
            rank_final = rank_final[['Rank', 'Nome', 'WODs', 'Total_Pontos']]
            rank_final.columns = ['RANK', 'ATLETA', 'FREQ.', 'PONTOS']
            
            st.dataframe(rank_final.style.highlight_max(axis=0, subset=['PONTOS'], color='#ffeeba'), use_container_width=True, hide_index=True)
            st.success("A constância é a sua maior aliada no Elite WODRank.")
    except: st.info("Inicie os registros para ver a elite.")
