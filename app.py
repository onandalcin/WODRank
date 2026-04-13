import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from difflib import get_close_matches

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

# --- CONFIGURAR IA (Lendo dos Secrets) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Erro: GEMINI_API_KEY não encontrada nos Secrets!")

# --- CSS MOBILE-FIRST ---
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
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="200"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_tempo(t):
    t_str = str(t).split('.')[0].replace("'", ":")
    return t_str

def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.sort_values("Segundos").reset_index(drop=True)
    posicoes = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(df))]
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

def ler_quadro_ia(imagem):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Analise esta imagem de um quadro de CrossFit e extraia os resultados.
        Regras:
        1. Formato de saída: NOME TEMPO (um por linha).
        2. Se houver algo como '19 + 20' ou '19:30 + 5', extraia exatamente como '19:20' ou o tempo total.
        3. Ignore nomes sem tempo (marcados com '-').
        4. Converta nomes para MAIÚSCULAS.
        """
        response = model.generate_content([prompt, imagem])
        return response.text
    except Exception as e:
        return f"Erro na leitura: {e}"

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    col1, col2 = st.columns(2)
    with col1: data_treino = st.date_input("Data", datetime.now())
    with col2: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])

    # --- NOVO: CAMPO DE FOTO ---
    arquivo_foto = st.file_uploader("📷 Tirar foto ou carregar quadro", type=['jpg', 'jpeg', 'png'])
    
    if arquivo_foto:
        img = Image.open(arquivo_foto)
        st.image(img, caption="Quadro carregado", use_container_width=True)
        if st.button("🤖 EXTRAIR DADOS DA FOTO"):
            with st.spinner("IA analisando caligrafia..."):
                texto_extraido = ler_quadro_ia(img)
                st.session_state.texto_input = texto_extraido

    st.markdown("---")
    txt_input = st.text_area("Lista (Edite se necessário):", value=st.session_state.get("texto_input", ""), height=250)
    
    if st.button("GERAR PRÉVIA DO RANKING"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    p = l.rsplit(' ', 1)
                    nome = p[0].upper().strip()
                    # Trata o tempo se vier com + ou '
                    tempo_limpo = p[1].replace("'", ":").replace("+", ":").strip()
                    partes = tempo_limpo.split(':')
                    m = int(partes[0])
                    s = int(partes[1]) if len(partes) > 1 else 0
                    
                    dados.append({
                        "Data": data_treino.strftime("%d/%m/%Y"),
                        "Horario": horario_sel,
                        "Nome": nome,
                        "Tempo": f"{m:02d}:{s:02d}",
                        "Segundos": m*60+s
                    })
                except: continue
            
            if dados:
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("🚀 CONFIRMAR E SALVAR"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Salvo com sucesso!")
            st.cache_data.clear()
            st.session_state.show_preview = False

# --- AS ABAS 2 E 3 CONTINUAM IGUAIS AO SEU CÓDIGO ANTERIOR ---
