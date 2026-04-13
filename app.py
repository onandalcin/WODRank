import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
# URL ATUALIZADA CONFORME SUA SOLICITAÇÃO
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

# Configuração da página para o WhatsApp usar sua logo
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
    
    # Limpeza de milissegundos para exibição
    def limpar_tempo(t):
        t_str = str(t).split('.')[0] 
        if ':' in t_str:
            partes = t_str.split(':')
            if len(partes) >= 2:
                return f"{int(partes[-2]):02d}:{int(partes[-1]):02d}"
        return t_str

    df['Tempo'] = df['Tempo'].apply(limpar_tempo)
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
    st.markdown("### 📝 Registrar Treino")
    
    col1, col2 = st.columns(2)
    with col1:
        data_treino = st.date_input("Data do WOD", datetime.now())
    with col2:
        horarios_box = ["06:00", "07:00", "16:20", "17:40", "18:30"]
        horario_sel = st.selectbox("Horário da Turma", horarios_box)

    st.markdown("---")
    txt_input = st.text_area("Lista (NOME TEMPO)", height=200, placeholder="Ex:\nJOÃO 12:45\nMARIA 13:20")
    
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
        st.markdown(f"**Revisão: Turma das {horario_sel}**")
        df_previa = pd.DataFrame(st.session_state.ready_to_save)
        st.dataframe(formatar_tabela_bonita(df_previa), use_container_width=True, hide_index=True)
        
        if st.button("🚀 CONFIRMAR E SALVAR"):
            with st.spinner("Enviando..."):
                try:
                    res = requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save)
                    if res.status_code == 200:
                        st.success("✅ Gravado com sucesso!")
                        st.balloons()
                        st.session_state.show_preview = False
                        st.cache_data.clear()
                    else:
                        st.error("Erro na resposta do servidor.")
                except:
                    st.error("Erro de conexão.")

with aba2:
    st.markdown("### 🔍 Histórico por Turma")
    if st.button("🔄 ATUALIZAR DADOS"): 
        st.cache_data.clear()
        
    try:
        df_hist = pd.read_csv(URL_PLANILHA_CSV)
        if not df_hist.empty:
            # 1. Selecionar o Dia
            datas = sorted(df_hist["Data"].unique(), reverse=True)
            data_sel = st.selectbox("Escolha o dia:", datas)
            
            # Filtro inicial por dia
            df_dia = df_hist[df_hist["Data"] == data_sel].copy()
            
            # 2. Selecionar o Horário (Filtro novo)
            horarios_disponiveis = ["Todos"] + sorted(df_dia["Horario"].unique().tolist())
            horario_filtro = st.selectbox("Filtrar por Horário:", horarios_disponiveis)
            
            # Aplica o filtro de horário se não for "Todos"
            if horario_filtro != "Todos":
                df_final = df_dia[df_dia["Horario"] == horario_filtro].copy()
                st.markdown(f"#### 🏆 Ranking das {horario_filtro}")
            else:
                df_final = df_dia
                st.markdown(f"#### 🏆 Ranking Geral - {data_sel}")
            
            # Exibe a tabela com as medalhas e sem milissegundos
            st.dataframe(formatar_tabela_bonita(df_final), use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.info("Aguardando registros na planilha...")

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
    except:
        st.info("Sem dados suficientes.")
