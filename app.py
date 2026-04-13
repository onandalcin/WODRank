import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

# --- AJUSTE PARA O WHATSAPP RECONHECER A LOGO ---
st.set_page_config(
    page_title="WOD Ranking Pro", 
    layout="centered", 
    page_icon=URL_LOGO  # <--- Aqui definimos sua logo como o ícone da página
)

# --- CSS MOBILE-FIRST ---
st.markdown(f"""
    <style>
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}
        h1 {{ font-size: 26px !important; text-align: center; }}
        .stButton>button {{
            width: 100%;
            height: 52px;
            border-radius: 12px;
            font-size: 16px;
            text-transform: uppercase;
            background-color: #1E1E1E;
            color: white;
            font-weight: bold;
            transition: 0.3s;
        }}
        .stButton>button:hover {{ background-color: #FF4B4B; color: white; }}
        .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 10px; }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown(f"""
    <div style="text-align: center; margin-top: -10px; margin-bottom: 10px;">
        <img src="{URL_LOGO}" height="240">
        <h1 style='margin-top: 10px; margin-bottom: 0;'>WOD Ranking Pro</h1>
        <p style='color: #FF4B4B; font-style: italic; font-weight: 500;'>Onde cada repetição conta.</p>
    </div>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def formatar_tabela_bonita(df):
    if df.empty: return df
    
    def limpar_tempo(t):
        t_str = str(t).split('.')[0] 
        if ':' in t_str:
            partes = t_str.split(':')
            if len(partes) >= 2:
                return f"{int(partes[-2]):02d}:{int(partes[-1]):02d}"
        return t_str

    df['Tempo'] = df['Tempo'].apply(limpar_tempo)
    df = df.sort_values("Segundos").reset_index(drop=True)
    
    posicoes = []
    for i in range(len(df)):
        num = i + 1
        if num == 1: posicoes.append("1º 🥇")
        elif num == 2: posicoes.append("2º 🥈")
        elif num == 3: posicoes.append("3º 🥉")
        else: posicoes.append(f"{num}º")
    
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

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
    
    col1, col2 = st.columns(2)
    with col1:
        data_treino = st.date_input("Data do WOD", datetime.now())
    with col2:
        horarios_box = ["06:00", "07:00", "16:20", "17:40", "18:30"]
        horario_sel = st.selectbox("Horário da Turma", horarios_box)

    st.markdown("---")
    txt_input = st.text_area("Lista (NOME TEMPO)", height=150, placeholder="Ex: JOÃO 12:45\nMARIA 13:20")
    
    if st.button("GERAR PRÉVIA DO RANKING"):
        if txt_input:
            dados = []
            linhas = txt_input.strip().split('\n')
            for l in linhas:
                try:
                    p = l.rsplit(' ', 1)
                    nome, tempo = p[0].upper(), p[1].replace("'", ":")
                    m, s = map(int, tempo.split(':'))
                    
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
        st.markdown(f"**Turma das {horario_sel}**")
        df_previa = pd.DataFrame(st.session_state.ready_to_save)
        st.dataframe(formatar_tabela_bonita(df_previa), use_container_width=True, hide_index=True)
        
        if st.button("🚀 CONFIRMAR E ENVIAR"):
            with st.spinner("Sincronizando..."):
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    if res.status_code == 200:
                        st.success(f"✅ Dados das {horario_sel} salvos!")
                        st.balloons()
                        st.session_state.show_preview = False
                        st.cache_data.clear()
                    else:
                        st.error("Erro ao salvar.")
                except:
                    st.error("Falha na conexão.")

with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 ATUALIZAR DADOS"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Escolha o dia:", datas)
            
            df_dia = df_hist[df_hist["Data"] == data_sel].copy()
            st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)
    except:
        st.info("Aguardando registros na planilha...")

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    try:
        df_geral = pd.read_csv(URL_PLANILHA_CSV)
        if not df_geral.empty:
            c1, c2 = st.columns(2)
            c1.metric("Atletas", df_geral["Nome"].nunique())
            c2.metric("Total WODs", len(df_geral["Data"].unique()))
            
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
    except:
        st.info("O ranking será gerado após o primeiro registro.")
