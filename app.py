import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CABEÇALHO ---
st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 20px; margin-bottom: 20px;'>
        <img src='{URL_LOGO}' style='max-height: 80px;'>
        <div>
            <h1 style='margin: 0;'>WOD Ranking Pro</h1>
            <p style='margin: 0; font-style: italic;'>Onde cada repetição conta. </p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def formatar_ranking(df):
    df = df.sort_values("Segundos").reset_index(drop=True)
    df.index += 1
    df['Pos'] = [f"{i}º" for i in df.index]
    if len(df) >= 1: df.loc[1, 'Pos'] = "🥇 1º"
    if len(df) >= 2: df.loc[2, 'Pos'] = "🥈 2º"
    if len(df) >= 3: df.loc[3, 'Pos'] = "🥉 3º"
    return df[['Pos', 'Nome', 'Tempo']]

def calcular_pontos(pos):
    if "1º" in pos: return 10
    if "2º" in pos: return 7
    if "3º" in pos: return 5
    return 1

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["➕ Registrar", "📅 Histórico", "🌎 Ranking Geral"])

with aba1:
    st.subheader("Registrar Treino")
    data_treino = st.date_input("Data", datetime.now())
    txt_input = st.text_area("Formato: NOME TEMPO", height=150)
    
    if st.button("Gerar Ranking"):
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
        st.table(st.session_state.display_df)
        if st.button("💾 SALVAR NA PLANILHA"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Salvo!")
            del st.session_state.display_df

with aba2:
    st.subheader("Arquivo por Dia")
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        datas = df_hist["Data"].unique()
        data_sel = st.selectbox("Escolha a data:", datas[::-1])
        st.table(formatar_ranking(df_hist[df_hist["Data"] == data_sel]))
    except: st.error("Erro ao carregar histórico.")

with aba3:
    st.subheader("🏆 Ranking Geral (Pontuação Acumulada)")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            # Processa o ranking de cada dia para atribuir pontos
            lista_pontos = []
            for d in df_geral["Data"].unique():
                dia = formatar_ranking(df_geral[df_geral["Data"] == d])
                dia['Pontos'] = dia['Pos'].apply(calcular_pontos)
                lista_pontos.append(dia[['Nome', 'Pontos']])
            
            # Soma tudo
            ranking_acumulado = pd.concat(lista_pontos).groupby("Nome").sum().sort_values("Pontos", ascending=False)
            ranking_acumulado.index.name = "Atleta"
            
            # Mostra o top do ranking geral
            st.dataframe(ranking_acumulado, use_container_width=True)
            st.info("Critério: 1º (10pts), 2º (7pts), 3º (5pts), Outros (1pt).")
    except: st.info("Salve o primeiro treino para ver o ranking geral.")
