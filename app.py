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

# --- CONFIGURAR GEMINI IA ---
# DICA: No Streamlit Cloud, salve sua chave em 'Secrets' como GEMINI_API_KEY
API_KEY = st.secrets.get("GEMINI_API_KEY", "SUA_CHAVE_AQUI")
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon="🏆")

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
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="240"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

# --- FUNÇÕES ---
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
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Analise a imagem deste quadro de Crossfit. 
        Extraia os nomes dos alunos e seus respectivos tempos de treino.
        Retorne APENAS uma lista no formato: NOME TEMPO
        Exemplo:
        PAULO 28:07
        EDSON 27:50
        Ignore anotações extras como '+500' ou '+4', pegue apenas o tempo principal.
        """
        response = model.generate_content([prompt, imagem])
        return response.text
    except Exception as e:
        return f"Erro na leitura: {str(e)}"

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    if pos == 3: return 90
    return max(10, 90 - (pos - 3))

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    data_treino = st.date_input("Data do WOD", datetime.now())
    
    # Novo botão para Foto
    arquivo_foto = st.file_uploader("📷 Tirar Foto ou Subir Imagem do Quadro", type=['jpg', 'jpeg', 'png'])
    
    if arquivo_foto:
        img = Image.open(arquivo_foto)
        st.image(img, caption="Imagem carregada", use_container_width=True)
        if st.button("🤖 ESCANEAR QUADRO COM IA"):
            with st.spinner("Analisando caligrafia..."):
                texto_ia = ler_quadro_com_ia(img)
                st.session_state.texto_input = texto_ia
                st.success("Leitura finalizada! Ajuste os dados abaixo se necessário.")

    # Campo de texto (preenchido pela IA ou manual)
    valor_atual = st.session_state.get("texto_input", "")
    txt_input = st.text_area("Dados extraídos (NOME TEMPO)", value=valor_atual, height=200)
    
    if st.button("GERAR PRÉVIA DO RANKING"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    partes = l.rsplit(' ', 1)
                    nome = partes[0].upper()
                    tempo = partes[1].replace("'", ":").replace('"', ":")
                    m, s = map(int, tempo.split(':')[:2])
                    dados.append({
                        "Data": data_treino.strftime("%d/%m/%Y"),
                        "Nome": nome,
                        "Tempo": f"{m:02d}:{s:02d}",
                        "Segundos": m*60+s
                    })
                except: continue
            if dados:
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.markdown("---")
        df_previa = pd.DataFrame(st.session_state.ready_to_save)
        st.dataframe(formatar_tabela_bonita(df_previa), use_container_width=True, hide_index=True)
        if st.button("🚀 SALVAR NO BANCO DE DADOS"):
            with st.spinner("Sincronizando..."):
                requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                st.success("✅ Tudo pronto! Pontos computados.")
                st.balloons()
                st.session_state.show_preview = False
                if "texto_input" in st.session_state: del st.session_state.texto_input

with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Escolha o dia:", datas)
            st.dataframe(formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel]), use_container_width=True, hide_index=True)
    except: st.info("Buscando dados...")

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            lista_acumulada = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acumulada.append(dia[['Nome', 'Pontos']])
            
            rank_final = pd.concat(lista_acumulada).groupby("Nome").agg(
                PTS=('Pontos', 'sum'), WDS=('Nome', 'count')
            ).sort_values("PTS", ascending=False).reset_index()
            
            posicoes_elite = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(rank_final))]
            rank_final.insert(0, '#', posicoes_elite)
            st.dataframe(rank_final.style.highlight_max(axis=0, subset=['PTS'], color='#FEF3C7'), use_container_width=True, hide_index=True)
    except: st.info("Sem dados suficientes.")
