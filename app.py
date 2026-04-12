import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/SUA_CHAVE/pub?output=csv"

# Link da sua Logomarca (Pode ser um link do Imgur, Instagram ou uma URL de imagem)
# Se não tiver uma agora, deixei um ícone de troféu padrão.
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/3112/3112946.png" 

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CABEÇALHO (LOGO E SLOGAN) ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image(URL_LOGO, width=100)
with col2:
    st.title("WOD Ranking Pro")
    st.markdown("*Superando limites, um segundo de cada vez.*") # Seu Slogan aqui

st.divider()

# Função para formatar o ranking com medalhas
def formatar_ranking(df):
    df = df.sort_values("Segundos").reset_index(drop=True)
    df.index += 1
    df['Pos'] = [f"{i}º" for i in df.index]
    if len(df) >= 1: df.loc[1, 'Pos'] = "🥇 1º"
    if len(df) >= 2: df.loc[2, 'Pos'] = "🥈 2º"
    if len(df) >= 3: df.loc[3, 'Pos'] = "🥉 3º"
    return df[['Pos', 'Nome', 'Tempo']]

aba1, aba2 = st.tabs(["➕ Registrar Treino", "📅 Histórico / Arquivo"])

# --- ABA 1: REGISTRAR ---
with aba1:
    st.subheader("Registrar Novo Treino")
    data_treino = st.date_input("Data do Treino", datetime.now())
    txt_input = st.text_area("Cole os tempos (Ex: PAULO 28:07)", height=150)
    
    if st.button("Gerar Ranking"):
        if txt_input:
            dados_hoje = []
            for linha in txt_input.strip().split('\n'):
                try:
                    partes = linha.rsplit(' ', 1)
                    nome, tempo = partes[0].upper(), partes[1].replace("'", ":")
                    m, s = map(int, tempo.split(':'))
                    dados_hoje.append({"Data": data_treino.strftime("%d/%m/%Y"), "Nome": nome, "Tempo": tempo, "Segundos": m*60+s})
                except: continue
            
            if dados_hoje:
                st.session_state.ready_to_save = dados_hoje
                st.session_state.display_df = formatar_ranking(pd.DataFrame(dados_hoje))
        else:
            st.error("Insira os dados.")

    if "display_df" in st.session_state:
        st.divider()
        st.subheader(f"📊 Prévia: {data_treino.strftime('%d/%m/%Y')}")
        st.table(st.session_state.display_df)
        
        if st.button("💾 CONFIRMAR E SALVAR NA PLANILHA"):
            with st.spinner("Salvando..."):
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    if res.status_code == 200:
                        st.success("✅ Dados registrados no histórico!")
                        del st.session_state.display_df
                    else: st.error("Erro no servidor.")
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: HISTÓRICO ---
with aba2:
    st.subheader("Arquivo de Treinos")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()

    try:
        df_historico = pd.read_csv(URL_PLANILHA_CSV)
        if not df_historico.empty:
            datas_disponiveis = df_historico["Data"].unique()
            data_sel = st.selectbox("Selecione uma data:", datas_disponiveis[::-1])
            ranking_dia = df_historico[df_historico["Data"] == data_sel].copy()
            st.table(formatar_ranking(ranking_dia))
        else:
            st.info("Planilha vazia.")
    except:
        st.error("Erro ao ler histórico. Verifique o link CSV.")
