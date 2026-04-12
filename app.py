import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÃO ---
# COLE AQUI o link que você copiou no Passo 1 (URL do app da Web)
URL_GOOGLE_SCRIPT = "SEU_LINK_DO_SCRIPT_AQUI"

st.set_page_config(page_title="WOD Ranking Oficial", layout="centered")
st.title("🏆 WOD Ranking")

# --- ENTRADA DE DADOS ---
with st.expander("➕ Registrar Novo Treino", expanded=True):
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
            st.error("Por favor, insira os dados.")

# --- EXIBIÇÃO E BOTÃO SALVAR ---
if "display_df" in st.session_state:
    st.subheader(f"🥇 Ranking de {data_treino.strftime('%d/%m/%Y')}")
    st.table(st.session_state.display_df[["Nome", "Tempo"]])
    
    if st.button("💾 SALVAR NA PLANILHA"):
        with st.spinner("Enviando para o Google Sheets..."):
            try:
                response = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                if response.status_code == 200:
                    st.success("✅ Dados salvos com sucesso na planilha!")
                    # Limpa os dados para evitar salvar duplicado
                    del st.session_state.display_df
                else:
                    st.error("Erro ao salvar. Verifique a configuração do Script.")
            except Exception as e:
                st.error(f"Falha na conexão: {e}")
