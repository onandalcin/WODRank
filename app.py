import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="wide", page_icon="🏆")

# --- LATARIA PREMIUM (CSS) ---
st.markdown("""
    <style>
        [data-testid="stMetricValue"] { font-size: 24px; font-weight: 900; color: #FF4B4B; }
        .stButton>button {
            border-radius: 10px;
            background: #1e1e1e;
            color: white;
            font-weight: 700;
            width: 100%;
        }
        .stButton>button:hover { background: #FF4B4B; border-color: #FF4B4B; }
        .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>WOD Ranking Pro</h2>", unsafe_allow_html=True)
    st.info("💡 **Dica:** A constância é a chave para subir no Elite WODRank.")
    st.divider()
    st.caption("Onde cada repetição conta.")

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

# --- CONTEÚDO PRINCIPAL ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR WOD", "📅 HISTÓRICO", "🔥 ELITE WODRANK"])

# ABA 1: REGISTRO
with aba1:
    st.markdown("### 📥 Entrada de Resultados")
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        data_treino = st.date_input("Data do Treino", datetime.now())
        txt_input = st.text_area("Cole aqui (Ex: NOME 10:00)", height=200)
        btn_preview = st.button("Gerar Prévia")

    with col2:
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
                st.table(formatar_tabela_bonita(pd.DataFrame(dados)))
                if st.button("💾 CONFIRMAR E SALVAR"):
                    requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    st.success("✅ Sincronizado!")
                    st.balloons()

# ABA 2: HISTÓRICO
with aba2:
    st.markdown("### 🔍 Consulta por Data")
    if st.button("🔄 Atualizar Banco de Dados"):
        st.cache_data.clear()
    
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = df_hist["Data"].unique()
            data_sel = st.selectbox("Selecione o dia:", datas[::-1])
            res_dia = formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel])
            st.table(res_dia)
        else:
            st.info("Nenhum dado registrado.")
    except Exception as e:
        st.warning("Aguardando conexão com a planilha ou novos registros.")

# ABA 3: ELITE WODRANK
with aba3:
    st.markdown("### 🏆 Top Performance Acumulada")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            # Cards de resumo
            c1, c2, c3 = st.columns(3)
            c1.metric("Atletas Ativos", df_geral["Nome"].nunique())
            c2.metric("Total de WODs", len(df_geral["Data"].unique()))
            
            # Lógica de Pontos
            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            rank_final = pd.concat(lista_acumulada).groupby("Nome").agg(
                PONTOS=('Pontos', 'sum'), FREQ=('Nome', 'count')
            ).sort_values("PONTOS", ascending=False).reset_index()
            
            rank_final.insert(0, 'RANK', [f"#{i+1}" for i in range(len(rank_final))])
            
            st.dataframe(
                rank_final.style.highlight_max(axis=0, subset=['PONTOS'], color='#FFD700'),
                use_container_width=True, hide_index=True
            )
            st.info("Regra: 1º(100), 2º(95), 3º(90). Demais caem 1pt por posição.")
        else:
            st.info("O Elite WODRank aparecerá após os registros.")
    except Exception as e:
        st.error("Erro ao carregar o ranking. Verifique o link da planilha.")
