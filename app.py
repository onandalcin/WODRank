import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbyf22E2JWzgI3RchzVJNPmjlFKvi2B7oY_HQONeh92HIQ_EpZc6ysKHkeus6V4nxMHT/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

# --- CONFIGURAR IA (GEMINI) ---
# Substitua pela sua chave ou use st.secrets para segurança
API_KEY = "SUA_CHAVE_AQUI" 
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

# --- CSS (MANTIDO O ANTERIOR) ---
st.markdown(f"""
    <style>
        .block-container {{ padding: 1rem 0.8rem; }}
        h1 {{ font-size: 26px !important; text-align: center; }}
        .stButton>button {{
            width: 100%; height: 52px; border-radius: 12px;
            font-size: 16px; text-transform: uppercase;
            background-color: #1E1E1E; color: white; font-weight: bold;
        }}
        .stButton>button:hover {{ background-color: #FF4B4B; color: white; }}
        #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="240"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.sort_values("Segundos").reset_index(drop=True)
    posicoes = []
    for i in range(1, len(df) + 1):
        if i == 1: posicoes.append("1º 🥇")
        elif i == 2: posicoes.append("2º 🥈")
        elif i == 3: posicoes.append("3º 🥉")
        else: posicoes.append(f"{i}º")
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

def ler_quadro_com_ia(imagem):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = """
    Analise esta foto de um quadro de horários de CrossFit. 
    Extraia os nomes dos alunos e seus respectivos tempos.
    Retorne APENAS uma lista no formato: NOME TEMPO
    Exemplo:
    PAULO 28:07
    EDSON 27:50
    Se houver anotações como +500 ou +4, ignore e coloque apenas o tempo principal ou ignore a linha se estiver ilegível.
    """
    response = model.generate_content([prompt, imagem])
    return response.text

# --- INTERFACE ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Resultados")
    data_treino = st.date_input("Data do WOD", datetime.now())
    
    # Opção de Upload de Foto
    foto_quadro = st.file_uploader("📷 Escanear Quadro Branco", type=['jpg', 'jpeg', 'png'])
    
    if foto_quadro:
        img = Image.open(foto_quadro)
        st.image(img, caption="Foto carregada", use_container_width=True)
        if st.button("🤖 LER FOTO COM IA"):
            with st.spinner("IA analisando o quadro..."):
                texto_extraido = ler_quadro_com_ia(img)
                st.session_state.texto_input = texto_extraido
                st.success("Leitura concluída! Verifique os dados abaixo.")

    # Área de texto (preenchida manualmente ou pela IA)
    valor_padrao = st.session_state.get("texto_input", "")
    txt_input = st.text_area("Lista Final (NOME TEMPO)", value=valor_padrao, height=200)
    
    if st.button("GERAR PRÉVIA"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    p = l.rsplit(' ', 1)
                    nome, tempo = p[0].upper(), p[1].replace("'", ":").replace('"', ":")
                    m, s = map(int, tempo.split(':')[:2])
                    dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Nome": nome, "Tempo": f"{m:02d}:{s:02d}", "Segundos": m*60+s})
                except: continue
            if dados:
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.markdown("---")
        df_previa = pd.DataFrame(st.session_state.ready_to_save)
        st.dataframe(formatar_tabela_bonita(df_previa), use_container_width=True, hide_index=True)
        if st.button("🚀 SALVAR NO BANCO DE DADOS"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("✅ Sincronizado!")
            st.balloons()
            st.session_state.show_preview = False
            if "texto_input" in st.session_state: del st.session_state.texto_input

# --- ABAS DE HISTÓRICO E ELITE (MANTIDAS IGUAIS) ---
# ... (restante do código que você já tem para aba2 e aba3)
