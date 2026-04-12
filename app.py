import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
# COLE AQUI o link que você copiou no Passo 1 (Publicar na Web)
URL_PLANILHA = "SEU_LINK_AQUI_TERMINADO_EM_OUTPUT_CSV"

st.set_page_config(page_title="WOD Ranking Oficial", layout="centered")
st.title("🏆 WOD Ranking & Histórico")

# Função para carregar dados da planilha
def carregar_dados():
    try:
        return pd.read_csv(URL_PLANILHA)
    except:
        return pd.DataFrame(columns=["Data", "Nome", "Tempo", "Segundos"])

# --- INTERFACE DE ENTRADA ---
with st.expander("➕ Registrar Treino de Hoje"):
    data_treino = st.date_input("Data", datetime.now())
    txt_input = st.text_area("Formato: NOME TEMPO (ex: PAULO 28:07)")
    
    if st.button("Gerar Ranking do Dia"):
        linhas = txt_input.strip().split('\n')
        dados_hoje = []
        for linha in linhas:
            try:
                partes = linha.rsplit(' ', 1)
                nome, tempo = partes[0].upper(), partes[1].replace("'", ":")
                m, s = map(int, tempo.split(':'))
                dados_hoje.append({"Nome": nome, "Tempo": tempo, "Segundos": m*60+s})
            except: continue
        
        if dados_hoje:
            df_dia = pd.DataFrame(dados_hoje).sort_values("Segundos").reset_index(drop=True)
            df_dia.index += 1
            st.session_state.temp_df = df_dia
            st.success("Ranking calculado abaixo!")

# --- EXIBIÇÃO ---
if "temp_df" in st.session_state:
    st.subheader(f"🥇 Ranking do Dia")
    st.table(st.session_state.temp_df[["Nome", "Tempo"]])
    
    # Instrução para o dono do App
    st.info("💡 Para salvar permanentemente: como estamos na versão grátis, copie os dados acima para sua planilha do Google. No próximo nível, faremos o botão 'Salvar' escrever direto lá!")

st.divider()
st.write("📖 **Acesso ao Banco de Dados:**")
st.link_button("Abrir Planilha do Google", URL_PLANILHA.replace("/pub?output=csv", ""))
