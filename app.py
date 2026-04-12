import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ranking Diário", layout="centered")

st.title("🏆 Ranking do Treino")

# Área para inserir os dados manualmente de forma simples
st.subheader("Registrar Tempos")
txt_input = st.text_area("Cole os nomes e tempos (Ex: Paulo 28:07)", 
                         help="Pode copiar e colar ou digitar um por linha.")

if txt_input:
    linhas = txt_input.strip().split('\n')
    dados = []
    for linha in linhas:
        partes = linha.rsplit(' ', 1)
        if len(partes) == 2:
            nome, tempo = partes
            # Converte MM:SS para segundos para poder ordenar
            try:
                m, s = map(int, tempo.replace("'", ":").split(':'))
                total_segundos = m * 60 + s
                dados.append({"Nome": nome, "Tempo": tempo, "segundos": total_segundos})
            except:
                continue

    if dados:
        df = pd.DataFrame(dados)
        # Ordena do menor tempo para o maior
        df = df.sort_values(by="segundos").reset_index(drop=True)
        df.index += 1 # Começa o ranking do 1
        
        st.subheader("🥇 Resultado Final")
        st.table(df[["Nome", "Tempo"]])
    else:
        st.warning("Formato inválido. Use: Nome Tempo (Ex: Paulo 28:07)")

st.divider()
st.info("Dica: No futuro, adicionaremos a leitura automática da foto aqui!")
