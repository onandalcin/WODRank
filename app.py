import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/SUA_CHAVE/pub?output=csv"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered")

# Função para formatar o ranking com medalhas
def formatar_ranking(df):
    df = df.sort_values("Segundos").reset_index(drop=True)
    # Cria a coluna de posição (1º, 2º...)
    df.index += 1
    df['Pos'] = [f"{i}º" for i in df.index]
    
    # Adiciona medalhas no Top 3
    df.loc[1, 'Pos'] = "🥇 1º"
    if len(df) >= 2: df.loc[2, 'Pos'] = "🥈 2º"
    if len(df) >= 3: df.loc[3, 'Pos'] = "🥉 3º"
    
    return df[['Pos', 'Nome', 'Tempo']]

aba1, aba2 = st.tabs(["➕ Registrar Treino", "📅 Histórico / Arquivo"])

with aba1:
    st.title("🏆 Novo Ranking")
    data_treino = st.date_input("Data do Treino", datetime.now())
    txt_input = st.text_area("Cole os tempos (Ex: PAULO 28:07)", height=150)
    
    if st.button("Gerar Ranking do Dia"):
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
                        st.success("✅ Salvo no histórico!")
                        del st.session_state.display_df
                    else: st.error("Erro no servidor.")
                except Exception as e: st.error(f"Erro: {e}")

with aba2:
    st.title("📂 Arquivo de Treinos")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()

    try:
        df_historico = pd.read_csv(URL_PLANILHA_CSV)
        if not df_historico.empty:
            datas_disponiveis = df_historico["Data"].unique()
            data_sel = st.selectbox("Selecione uma data:", datas_disponiveis[::-1])
            
            # Filtra e formata o ranking do passado
            ranking_dia = df_historico[df_historico["Data"] == data_sel].copy()
            st.table(formatar_ranking(ranking_dia))
        else:
            st.info("Planilha vazia.")
    except:
        st.error("Erro ao ler histórico. Verifique o link CSV.")
