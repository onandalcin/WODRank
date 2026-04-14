import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

@st.cache_data(ttl=5) # Cache baixíssimo para você ver a limpeza na hora
def ler_dados_planilha():
    try:
        return pd.read_csv(URL_PLANILHA_CSV)
    except:
        return pd.DataFrame()

# --- LÓGICA DE PONTUAÇÃO (PADRÃO INTERNACIONAL) ---
def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    pontuacao = 95 - (pos - 2)
    return max(80, pontuacao)

def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.copy().sort_values("Segundos").reset_index(drop=True)
    posicoes = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(df))]
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

# --- INTERFACE ---
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="200"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    c1, c2 = st.columns(2)
    with c1: data_treino = st.date_input("Data do WOD", datetime.now())
    with c2: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])

    if "input_texto" not in st.session_state: st.session_state.input_texto = ""
    txt_input = st.text_area("Digite: NOME MINUTOS SEGUNDOS (ou só o nome para CAP)", value=st.session_state.input_texto, height=200, key="campo_entrada")
    
    col_a, col_b = st.columns(2)
    with col_a:
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
                                m, s = int(nums[0]), (int(nums[1]) if len(nums) > 1 else 0)
                                tempo_str, seg_total = f"{m:02d}:{s:02d}", m*60 + s
                            else:
                                tempo_str, seg_total = "CAP", 99999
                            if nome: dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": tempo_str, "Segundos": seg_total})
                    except: continue
                st.session_state.ready_to_save = dados
                st.session_state.show_preview = True
                st.rerun()
    
    with col_b:
        if st.button("🗑️ LIMPAR"):
            st.session_state.input_texto = ""
            if "ready_to_save" in st.session_state: del st.session_state.ready_to_save
            st.session_state.show_preview = False
            st.rerun()

    if st.session_state.get("show_preview") and "ready_to_save" in st.session_state:
        st.dataframe(formatar_tabela_bonita(pd.DataFrame(st.session_state.ready_to_save)), use_container_width=True, hide_index=True)
        if st.button("🚀 SALVAR RESULTADOS"):
            if requests.post(URL_GOOGLE_SCRIPT, json=st.session_state.ready_to_save).status_code == 200:
                st.success("Salvo!")
                st.session_state.input_texto = ""
                st.session_state.show_preview = False
                st.cache_data.clear()
                st.rerun()

with aba2:
    st.markdown("### 🔍 Histórico por Turma")
    if st.button("🔄 RECARREGAR PLANILHA"):
        st.cache_data.clear()
        st.rerun()
    
    df_hist = ler_dados_planilha()
    if not df_hist.empty and "Data" in df_hist.columns:
        datas = sorted(df_hist["Data"].unique(), reverse=True)
        data_sel = st.selectbox("Escolha o dia:", datas)
        df_dia = df_hist[df_hist["Data"] == data_sel].copy()
        
        if "Horario" in df_dia.columns:
            h_disp = sorted([str(h) for h in df_dia["Horario"].dropna().unique()])
            h_opcoes = ["Todos"] + h_disp
            h_filtro = st.selectbox("Filtrar por Horário:", h_opcoes)
            if h_filtro != "Todos":
                df_dia = df_dia[df_dia["Horario"].astype(str) == h_filtro]
        
        st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)
    else:
        st.info("O App está limpo. Aguardando novos registros.")

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
        pos_elite = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(rank))]
        rank.insert(0, '#', pos_elite)
        st.dataframe(rank.style.highlight_max(axis=0, subset=['PTS'], color='#FEF3C7'), use_container_width=True, hide_index=True)
