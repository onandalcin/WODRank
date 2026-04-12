import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
# 1. Cole aqui o link do Script (o que termina em /exec)
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/SUA_CHAVE_AQUI/exec"

# 2. Cole aqui o link da Planilha Publicada como CSV (o que termina em output=csv)
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/SUA_CHAVE/pub?output=csv"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered")

# Menu de Navegação em Abas
aba1, aba2 = st.tabs(["➕ Registrar Treino", "📅 Histórico / Arquivo"])

# --- ABA 1: REGISTRAR TREINO ---
with aba1:
    st.title("🏆 Novo Ranking")
    data_treino = st.date_input("Data do Treino", datetime.now())
    txt_input = st.text_area("Cole os tempos (Ex: PAULO 28:07)", height=150, key="input_hoje")
    
    if st.button("Gerar Ranking do Dia"):
        if txt_input:
            dados_hoje = []
            for linha in txt_input.strip().split('\n'):
                try:
                    partes = linha.rsplit(' ', 1)
                    nome, tempo = partes[0].upper(), partes[1].replace("'", ":")
                    m, s = map(int, tempo.split(':'))
                    dados_hoje.append({
                        "Data": data_treino.strftime("%d/%m/%Y"),
                        "Nome": nome,
                        "Tempo": tempo,
                        "Segundos": m*60+s
                    })
                except: continue
            
            if dados_hoje:
                df = pd.DataFrame(dados_hoje).sort_values("Segundos").reset_index(drop=True)
                df.index += 1
                st.session_state.ready_to_save = dados_hoje
                st.session_state.display_df = df
        else:
            st.error("Insira os dados antes de gerar.")

    if "display_df" in st.session_state:
        st.divider()
        st.subheader(f"📊 Prévia: {data_treino.strftime('%d/%m/%Y')}")
        st.table(st.session_state.display_df[["Nome", "Tempo"]])
        
        if st.button("💾 CONFIRMAR E SALVAR NA PLANILHA"):
            with st.spinner("Salvando..."):
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    if res.status_code == 200:
                        st.success("✅ Salvo no histórico!")
                        del st.session_state.display_df
                    else: st.error("Erro no servidor Google.")
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: HISTÓRICO / ARQUIVO ---
with aba2:
    st.title("📂 Arquivo de Treinos")
    if st.button("🔄 Atualizar Dados da Planilha"):
        # Força o Streamlit a ler a planilha novamente
        st.cache_data.clear()

    try:
        # Lê a planilha publicada
        df_historico = pd.read_csv(URL_PLANILHA_CSV)
        
        if not df_historico.empty:
            # Filtro por Data
            datas_disponiveis = df_historico["Data"].unique()
            data_selecionada = st.selectbox("Selecione uma data para ver o ranking:", datas_disponiveis[::-1])
            
            # Filtra, ordena e numera o ranking daquele dia
            ranking_dia = df_historico[df_historico["Data"] == data_selecionada].copy()
            ranking_dia = ranking_dia.sort_values("Segundos").reset_index(drop=True)
            ranking_dia.index += 1
            
            st.subheader(f"🥇 Ranking Final de {data_selecionada}")
            st.table(ranking_dia[["Nome", "Tempo"]])
        else:
            st.info("A planilha parece estar vazia.")
            
    except Exception as e:
        st.error("Ainda não há dados suficientes na planilha ou o link CSV está incorreto.")
        st.info("Certifique-se de que você já salvou pelo menos um treino e que o link da planilha está correto.")
