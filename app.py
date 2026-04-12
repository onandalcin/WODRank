import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="WOD Ranking Histórico", layout="centered")

# Título e Logo
st.title("🏆 WOD Ranking & Histórico")

# --- ÁREA DE ENTRADA DE DADOS ---
with st.expander("➕ Registrar Treino de Hoje"):
    data_treino = st.date_input("Data do Treino", datetime.now())
    txt_input = st.text_area("Cole os nomes e tempos (Ex: Paulo 28:07)", height=150)
    btn_salvar = st.button("Salvar no Histórico")

# --- LÓGICA DE PROCESSAMENTO ---
if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=["Data", "Nome", "Tempo", "Segundos"])

if btn_salvar and txt_input:
    novos_dados = []
    linhas = txt_input.strip().split('\n')
    for linha in linhas:
        partes = linha.rsplit(' ', 1)
        if len(partes) == 2:
            nome, tempo = partes
            try:
                # Trata MM:SS ou MM'SS
                t_limpo = tempo.replace("'", ":")
                m, s = map(int, t_limpo.split(':'))
                segundos = m * 60 + s
                novos_dados.append({
                    "Data": data_treino.strftime("%d/%m/%Y"),
                    "Nome": nome.upper(),
                    "Tempo": tempo,
                    "Segundos": segundos
                })
            except: continue
    
    if novos_dados:
        df_hoje = pd.DataFrame(novos_dados)
        st.session_state.historico = pd.concat([st.session_state.historico, df_hoje], ignore_index=True)
        st.success("Dados salvos com sucesso!")

# --- EXIBIÇÃO ---
if not st.session_state.historico.empty:
    todas_datas = st.session_state.historico["Data"].unique()
    data_selecionada = st.selectbox("📅 Selecione o dia para ver o Ranking:", todas_datas[::-1])
    
    # Filtrar e Rankear
    df_dia = st.session_state.historico[st.session_state.historico["Data"] == data_selecionada].copy()
    df_dia = df_dia.sort_values(by="Segundos").reset_index(drop=True)
    df_dia.index += 1  # Numeração do Ranking 1, 2, 3...
    
    st.subheader(f"🥇 Ranking de {data_selecionada}")
    # Mostrar a tabela com a coluna de índice (Ranking) visível
    st.table(df_dia[["Nome", "Tempo"]])
else:
    st.info("Nenhum dado registrado ainda. Use o campo acima para começar!")

st.sidebar.write("### Instruções")
st.sidebar.info("1. Digite o Nome e o Tempo.\n2. Clique em Salvar.\n3. O ranking será gerado e numerado automaticamente.")
