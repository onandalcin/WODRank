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

# Configuração da Página para o WhatsApp reconhecer a logo
st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

# --- CONFIGURAR IA (GEMINI) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Adicione a GEMINI_API_KEY nos Secrets do Streamlit.")

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

def ler_quadro_ia(imagem):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Extraia os nomes e tempos deste quadro de CrossFit. Formato: NOME TEMPO. Ignore '+500' ou similares."
        response = model.generate_content([prompt, imagem])
        return response.text
    except Exception as e:
        return f"Erro na leitura: {str(e)}"

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    col_d, col_h = st.columns(2)
    with col_d: data_treino = st.date_input("Data", datetime.now())
    with col_h: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])

    # Botão de Foto igual ao anexo
    foto = st.file_uploader("📷 Escanear Quadro Branco", type=['jpg', 'jpeg', 'png'])
    if foto:
        img = Image.open(foto)
        st.image(img, caption="Quadro detectado", use_container_width=True)
        if st.button("🤖 LER NOMES E TEMPOS"):
            with st.spinner("IA processando imagem..."):
                st.session_state.texto_ia = ler_quadro_ia(img)

    txt_input = st.text_area("Lista Final (Edite se necessário)", value=st.session_state.get("texto_ia", ""), height=150)
    
    if st.button("GERAR PRÉVIA"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    p = l.rsplit(' ', 1)
                    nome, tempo = p[0].upper(), p[1].replace("'", ":").replace('"', ":")
                    m, s = map(int, tempo.split(':')[:2])
                    dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": f"{m:02d}:{s:02d}", "Segundos": m*60+s})
                except: continue
            st.session_state.ready_to_save = dados
            st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("🚀 CONFIRMAR E SALVAR"):
            requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            st.success("Salvo com sucesso!")
            st.session_state.show_preview = False
            st.cache_data.clear()

with aba2:
    st.markdown("### 🔍 Histórico")
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            data_sel = st.selectbox("Dia:", sorted(df_hist["Data"].unique(), reverse=True))
            st.dataframe(formatar_tabela_bonita(df_hist[df_hist["Data"] == data_sel]), use_container_width=True, hide_index=True)
    except: st.info("Sem dados.")

with aba3:
    st.markdown("### 🏆 Elite")
    # ... (lógica do ranking de elite mantida)
