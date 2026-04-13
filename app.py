import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="wide", page_icon="🏆")

# --- DESIGN SYSTEM LIGHT (LIMPO E PROFISSIONAL) ---
st.markdown(f"""
    <style>
        /* Fundo e Texto Geral */
        .stApp {{
            background-color: #FFFFFF;
            color: #2D3436;
        }}
        
        /* Sidebar Leve */
        [data-testid="stSidebar"] {{
            background-color: #F8F9FA;
            border-right: 1px solid #E9ECEF;
        }}

        /* Títulos */
        h1, h2, h3 {{
            color: #1E1E1E;
            font-weight: 700 !important;
        }}

        /* Botão de Ação (Vermelho Profissional) */
        .stButton>button {{
            width: 100%;
            border-radius: 8px;
            background-color: #FF4B4B;
            color: white;
            border: none;
            padding: 10px;
            font-weight: 600;
            transition: 0.2s all;
        }}
        .stButton>button:hover {{
            background-color: #D63031;
            box-shadow: 0 4px 12px rgba(255, 75, 75, 0.2);
        }}

        /* Tabs (Abas) */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 20px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #636E72;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            color: #FF4B4B !important;
            border-bottom-color: #FF4B4B !important;
        }}

        /* Cards de Métricas */
        [data-testid="stMetricValue"] {{
            color: #1E1E1E;
            font-weight: 700;
        }}
        
        /* Tabelas */
        .stTable {{
            background-color: #FFFFFF;
            border-radius: 10px;
        }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.markdown("<h2 style='text-align: center; font-size: 20px;'>Dashboard Pro</h2>", unsafe_allow_html=True)
    st.divider()
    st.write("**Onan Dal Cin**")
    st.caption("Engenheiro de Petróleo")
    st.info("💡 A constância no treino gera resultados acumulados.")

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

# --- CORPO DO APP ---
st.title("🏆 Elite WODRank")
st.markdown("Acompanhamento de performance e ranking acumulado.")

aba1, aba2, aba3 = st.tabs(["➕ REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE RANK"])

with aba1:
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        st.subheader("Entrada de Dados")
        data_treino = st.date_input("Data do WOD", datetime.now())
        txt_input = st.text_area("Lista (NOME TEMPO)", height=200, placeholder="Ex:\nJOÃO 12:40\nMARIA 13:15")
        if st.button("Gerar Prévia"):
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

    with col_r:
        if st.session_state.get("show_preview"):
            st.subheader("Prévia do Ranking")
            st.table(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)))
            if st.button("Salvar Resultados"):
                requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                st.success("Resultados enviados com sucesso!")
                st.balloons()
                st.session_state.show_preview = False

with aba2:
    st.subheader("Consultar Treinos Anteriores")
    if st.button("Sincronizar Planilha"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Selecione a Data:", datas)
            st.table(formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel]))
    except: st.info("Buscando dados...")

with aba3:
    st.subheader("Ranking de Elite (Acumulado)")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Atletas", df_geral["Nome"].nunique())
            c2.metric("WODs Totais", len(df_geral["Data"].unique()))
            c3.metric("Recordista Presença", df_geral.groupby("Nome").size().idxmax())

            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            rank_final = pd.concat(lista_acumulada).groupby("Nome").agg(
                PONTOS=('Pontos', 'sum'), WODS=('Nome', 'count')
            ).sort_values("PONTOS", ascending=False).reset_index()
            
            rank_final.insert(0, '#', [f"{i+1}º" for i in range(len(rank_final))])
            
            # Tabela Estilizada (Dourado para o primeiro)
            st.dataframe(
                rank_final.style.highlight_max(axis=0, subset=['PONTOS'], color='#FEF3C7'),
                use_container_width=True, hide_index=True
            )
    except: st.info("Ranking será gerado após o registro.")
