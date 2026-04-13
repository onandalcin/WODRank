import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

# --- CONFIGURAR IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Configure a GEMINI_API_KEY nos Secrets do Streamlit.")

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
def limpar_tempo_display(t):
    t_str = str(t).split('.')[0] 
    if ':' in t_str:
        partes = t_str.split(':')
        if len(partes) >= 2:
            return f"{int(partes[-2]):02d}:{int(partes[-1]):02d}"
    return t_str

def formatar_tabela_bonita(df):
    if df.empty: return df
    df['Tempo'] = df['Tempo'].apply(limpar_tempo_display)
    df = df.sort_values("Segundos").reset_index(drop=True)
    posicoes = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(df))]
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    if pos == 3: return 90
    return max(10, 90 - (pos - 3))

def ler_quadro_ia(imagem):
    try:
        # Forçamos o modelo com o prefixo completo
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = """
        Extraia nomes e resultados deste quadro de Crossfit.
        Regras de Formatação:
        1. Saída: NOME TEMPO (ex: PAULO 19:20)
        2. Se houver '+' (ex: 19' + 20), extraia como '19:20'.
        3. Se houver apenas um número após o nome, assuma como minutos.
        4. Ignore nomes que tenham apenas um traço '-' ou 'CAP'.
        5. Use apenas letras maiúsculas para os nomes.
        """
        
        response = model.generate_content([prompt, imagem])
        return response.text
    except Exception as e:
        # Se o erro 404 persistir, tentamos o modelo pro como alternativa automática
        try:
            model_alt = genai.GenerativeModel('models/gemini-pro-vision')
            response = model_alt.generate_content([prompt, imagem])
            return response.text
        except:
            return f"Erro técnico na API do Google: {e}"

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    col1, col2 = st.columns(2)
    with col1: data_treino = st.date_input("Data", datetime.now())
    with col2: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])

    arquivo_foto = st.file_uploader("📷 Escanear Quadro Branco", type=['jpg', 'jpeg', 'png'])
    if arquivo_foto:
        img = Image.open(arquivo_foto)
        st.image(img, caption="Foto carregada", use_container_width=True)
        if st.button("🤖 EXTRAIR DADOS"):
            with st.spinner("IA processando imagem..."):
                st.session_state.texto_input = ler_quadro_ia(img)

    txt_input = st.text_area("Lista Final (NOME TEMPO):", value=st.session_state.get("texto_input", ""), height=200)
    
    if st.button("GERAR PRÉVIA DO RANKING"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    p = l.rsplit(' ', 1)
                    nome = p[0].upper().strip()
                    tempo_raw = p[1].replace("'", ":").replace("+", ":").strip()
                    m, s = map(int, tempo_raw.split(':')[:2])
                    dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": f"{m:02d}:{s:02d}", "Segundos": m*60+s})
                except: continue
            st.session_state.ready_to_save = dados
            st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("🚀 CONFIRMAR E SALVAR"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Salvo com sucesso!")
            st.cache_data.clear()
            st.session_state.show_preview = False

with aba2:
    st.markdown("### 🔍 Histórico por Turma")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            data_sel = st.selectbox("Escolha o dia:", sorted(df_hist["Data"].unique(), reverse=True))
            df_dia = df_hist[df_hist["Data"] == data_sel].copy()
            if "Horario" in df_dia.columns:
                h_disp = ["Todos"] + sorted([str(h) for h in df_dia["Horario"].dropna().unique()])
                h_filtro = st.selectbox("Filtrar Horário:", h_disp)
                if h_filtro != "Todos": df_dia = df_dia[df_dia["Horario"].astype(str) == h_filtro]
            st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)
    except: st.info("Sem registros.")

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            lista_acum = []
            for d in df_geral["Data"].unique():
                dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
                dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
                lista_acum.append(dia[['Nome', 'Pontos']])
            rank = pd.concat(lista_acum).groupby("Nome").agg(PTS=('Pontos', 'sum'), WDS=('Nome', 'count')).sort_values("PTS", ascending=False).reset_index()
            rank.insert(0, '#', [f"{i+1}º" for i in range(len(rank))])
            st.dataframe(rank.style.highlight_max(axis=0, subset=['PTS'], color='#FEF3C7'), use_container_width=True, hide_index=True)
    except: st.info("Sem dados suficientes.")
