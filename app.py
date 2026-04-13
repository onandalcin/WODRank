import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

# --- FUNÇÃO DE LEITURA COM AUTO-LIMPEZA ---
@st.cache_data(ttl=10)
def ler_dados_planilha():
    try:
        return pd.read_csv(URL_PLANILHA_CSV)
    except:
        return pd.DataFrame()

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
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="200"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

# --- FUNÇÕES DE FORMATAÇÃO ---
def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.copy()
    # Ordena por segundos (quem fez em menos tempo primeiro, CAPs ficam por último)
    df = df.sort_values("Segundos").reset_index(drop=True)
    
    posicoes = []
    for i in range(len(df)):
        if i == 0: posicoes.append("1º 🥇")
        elif i == 1: posicoes.append("2º 🥈")
        elif i == 2: posicoes.append("3º 🥉")
        else: posicoes.append(f"{i+1}º")
        
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    if pos == 3: return 90
    return max(10, 90 - (pos - 3)) # Mínimo de 10 pontos

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

    if "input_texto" not in st.session_state:
        st.session_state.input_texto = ""

    txt_input = st.text_area("Digite: NOME MINUTOS SEGUNDOS", 
                             value=st.session_state.input_texto,
                             height=200, 
                             placeholder="Ex: PAULO 19 20\nALEX (sem tempo)",
                             key="campo_entrada")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("GERAR PRÉVIA"):
            if txt_input:
                dados = []
                st.session_state.input_texto = txt_input
                for l in txt_input.strip().split('\n'):
                    try:
                        limpo = l.replace("'", " ").replace(":", " ").replace("+", " ").strip()
                        partes = limpo.split()
                        if len(partes) >= 1:
                            nome = " ".join([p for p in partes if not p.isdigit()]).upper()
                            nums = [p for p in partes if p.isdigit()]
                            
                            if len(nums) >= 1:
                                m = int(nums[0])
                                s = int(nums[1]) if len(nums) > 1 else 0
                                tempo_str = f"{m:02d}:{s:02d}"
                                seg_total = m*60 + s
                            else:
                                tempo_str = "CAP"
                                seg_total = 99999 # Para ficar no fim da lista
                            
                            if nome:
                                dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": tempo_str, "Segundos": seg_total})
                    except: continue
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True
                st.rerun()
    
    with c2:
        if st.button("🗑️ LIMPAR"):
            st.session_state.input_texto = ""
            if "ready_to_save" in st.session_state: del st.session_state.ready_to_save
            st.session_state.show_preview = False
            st.rerun()

    if st.session_state.get("show_preview") and "ready_to_save" in st.session_state:
        st.markdown("---")
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("🚀 SALVAR RESULTADOS"):
            if requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save).status_code == 200:
                st.success("Salvo com sucesso!")
                st.session_state.input_texto = ""
                st.session_state.show_preview = False
                st.cache_data.clear()
                st.rerun()

with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 RECARREGAR"):
        st.cache_data.clear()
        st.rerun()
    
    df_hist = ler_dados_planilha()
    if not df_hist.empty and "Data" in df_hist.columns:
        datas = sorted(df_hist["Data"].unique(), reverse=True)
        data_sel = st.selectbox("Escolha o dia:", datas)
        df_dia = df_hist[df_hist["Data"] == data_sel].copy()
        
        if "Horario" in df_dia.columns:
            h_disp = ["Todos"] + sorted([str(h) for h in df_dia["Horario"].dropna().unique()])
            h_filtro = st.selectbox("Filtrar Horário:", h_disp)
            if h_filtro != "Todos":
                df_dia = df_dia[df_dia["Horario"].astype(str) == h_filtro]
        
        st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)
    else:
        st.info("Planilha vazia ou em atualização.")

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    df_geral = ler_dados_planilha()
    if not df_geral.empty and "Data" in df_geral.columns:
        lista_acum = []
        for d in df_geral["Data"].unique():
            dia = df_geral[df_geral["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
            dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
            lista_acum.append(dia[['Nome', 'Pontos']])
        
        rank = pd.concat(lista_acum).groupby("Nome").agg(PTS=('Pontos', 'sum'), WDS=('Nome', 'count')).sort_values("PTS", ascending=False).reset_index()
        
        pos_elite = []
        for i in range(len(rank)):
            if i == 0: pos_elite.append("1º 🥇")
            elif i == 1: pos_elite.append("2º 🥈")
            elif i == 2: pos_elite.append("3º 🥉")
            else: pos_elite.append(f"{i+1}º")
            
        rank.insert(0, '#', pos_elite)
        st.dataframe(rank.style.highlight_max(axis=0, subset=['PTS'], color='#FEF3C7'), use_container_width=True, hide_index=True)
