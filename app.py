import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

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

# --- ABAS ---
aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Modo Rápido (Entrada Manual)")
    
    col1, col2 = st.columns(2)
    with col1:
        data_treino = st.date_input("Data do WOD", datetime.now())
    with col2:
        horarios_box = ["06:00", "07:00", "16:20", "17:40", "18:30"]
        horario_sel = st.selectbox("Horário da Turma", horarios_box)

    st.markdown("---")
    txt_input = st.text_area("Digite: NOME MINUTOS SEGUNDOS", height=250, 
                             placeholder="Exemplo baseado na sua foto:\nGAMES 18 35\nPAULO 19 20\nCAMILA 18 23")
    
    if st.button("GERAR PRÉVIA DO RANKING"):
        if txt_input:
            dados = []
            linhas = txt_input.strip().split('\n')
            for l in linhas:
                try:
                    # Limpa símbolos comuns que você vê no quadro
                    limpo = l.replace("'", " ").replace(":", " ").replace("+", " ").strip()
                    partes = limpo.split()
                    
                    if len(partes) >= 2:
                        # Pega tudo que não é número como Nome
                        nome = " ".join([p for p in partes if not p.isdigit()]).upper()
                        # Pega apenas os números para o Tempo
                        nums = [p for p in partes if p.isdigit()]
                        
                        minutos = int(nums[0])
                        segundos = int(nums[1]) if len(nums) > 1 else 0
                        
                        dados.append({
                            "Data": data_treino.strftime("%d/%m/%Y"),
                            "Horario": horario_sel,
                            "Nome": nome,
                            "Tempo": f"{minutos:02d}:{segundos:02d}",
                            "Segundos": minutos*60 + segundos
                        })
                except: continue
            
            if dados:
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True

    if st.session_state.get("show_preview"):
        st.markdown("#### Revisão do Pódio")
        df_previa = pd.DataFrame(st.session_state.ready_to_save)
        st.dataframe(formatar_tabela_bonita(df_previa), use_container_width=True, hide_index=True)
        
        if st.button("🚀 SALVAR NA PLANILHA"):
            res = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
            if res.status_code == 200:
                st.success("✅ Salvo!")
                st.balloons()
                st.session_state.show_preview = False
                st.cache_data.clear()

with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear()
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            data_sel = st.selectbox("Escolha o dia:", sorted(df_hist["Data"].unique(), reverse=True))
            df_dia = df_hist[df_hist["Data"] == data_sel].copy()
            if "Horario" in df_dia.columns:
                h_disp = ["Todos"] + sorted([str(h) for h in df_dia["Horario"].dropna().unique()])
                h_filtro = st.selectbox("Filtrar por Horário:", h_disp)
                if h_filtro != "Todos":
                    df_dia = df_dia[df_dia["Horario"].astype(str) == h_filtro]
            st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)
    except: st.info("Aguardando registros...")

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
