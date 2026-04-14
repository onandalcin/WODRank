import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

@st.cache_data(ttl=0) # Totalmente em tempo real
def ler_dados_planilha():
    try:
        url_ignora_cache = f"{URL_PLANILHA_CSV}&t={int(time.time())}"
        return pd.read_csv(url_ignora_cache)
    except:
        return pd.DataFrame()

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    # Padrão Internacional: 94, 93, 92...
    pontuacao = 95 - (pos - 2)
    return max(80, pontuacao)

def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.copy().sort_values("Segundos").reset_index(drop=True)
    posicoes = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(df))]
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="180"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

# Aba 1 e Aba 2 permanecem com a lógica de limpeza de nomes...
with aba1:
    st.markdown("### 📝 Registrar Treino")
    c1, c2 = st.columns(2)
    with c1: data_treino = st.date_input("Data do WOD", datetime.now())
    with c2: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])
    
    txt_input = st.text_area("NOME MINUTOS SEGUNDOS", height=150)
    
    if st.button("🚀 SALVAR"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                partes = l.replace("'", " ").replace(":", " ").strip().split()
                if len(partes) >= 1:
                    nome = " ".join([p for p in partes if not p.isdigit()]).upper().strip()
                    nums = [p for p in partes if p.isdigit()]
                    m, s = (int(nums[0]), int(nums[1]) if len(nums)>1 else 0) if nums else (0, 0)
                    seg = m*60 + s if nums else 99999
                    t_str = f"{m:02d}:{s:02d}" if nums else "CAP"
                    dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": t_str, "Segundos": seg})
            if requests.post(URL_GOOGLE_SCRIPT, json=dados).status_code == 200:
                st.success("Salvo!"); st.cache_data.clear()

with aba2:
    st.markdown("### 🔍 Histórico")
    df_hist = ler_dados_planilha()
    if not df_hist.empty:
        data_sel = st.selectbox("Dia:", sorted(df_hist["Data"].unique(), reverse=True))
        df_dia = df_hist[df_hist["Data"] == data_sel].copy()
        st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    df_geral = ler_dados_planilha()
    if not df_geral.empty:
        df_geral['Nome'] = df_geral['Nome'].str.upper().str.strip()
        lista_acum = []
        # O pulo do gato: Cálculo diário
        for d in df_geral["Data"].unique():
            dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
            dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
            lista_acum.append(dia[['Nome', 'Pontos']])
        
        rank = pd.concat(lista_acum).groupby("Nome").agg(PTS=('Pontos', 'sum'), WDS=('Nome', 'count')).reset_index()
        rank = rank.sort_values(by=['PTS', 'WDS'], ascending=[False, False]).reset_index(drop=True)
        
        pos_elite = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(rank))]
        rank.insert(0, '#', pos_elite)
        st.dataframe(rank, use_container_width=True, hide_index=True)
