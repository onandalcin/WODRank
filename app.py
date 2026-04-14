import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
URL_GOOGLE_SCRIPT = "https://script.google.com/macros/s/AKfycbwBOPsOjjiqiiSTxbiM5iGXSBuJKN848niP0TTeMkacDEkSFpuYe0meOGX0ASR9yncz/exec"
URL_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3VB9L1Qgp6g4khGsXb1ZrPBJKeHJ-ZWVy8P0j1p5rBY0xZnHR7xiha7hEaE2fViZu8EZ86CVUqxWQ/pub?output=csv"
URL_LOGO = "https://i.postimg.cc/Cx1wQRrv/Logo-dinamico-WODRank-com-haltere.png"

st.set_page_config(page_title="WOD Ranking Pro", layout="centered", page_icon=URL_LOGO)

@st.cache_data(ttl=0)
def ler_dados_planilha():
    try:
        url_ignora_cache = f"{URL_PLANILHA_CSV}&t={int(time.time())}"
        return pd.read_csv(url_ignora_cache)
    except:
        return pd.DataFrame()

def calcular_pontos_dinamico(index_linear):
    pos = index_linear + 1
    if pos == 1: return 100
    if pos == 2: return 95
    pontuacao = 95 - (pos - 2)
    return max(80, pontuacao)

def formatar_segundos_para_tempo(segundos_totais):
    if segundos_totais >= 99999: return "CAP"
    m = int(segundos_totais // 60)
    s = int(segundos_totais % 60)
    return f"{m:02d}:{s:02d}"

def formatar_tabela_bonita(df):
    if df.empty: return df
    df = df.copy().sort_values("Segundos").reset_index(drop=True)
    posicoes = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(df))]
    df.insert(0, 'Pos', posicoes)
    return df[['Pos', 'Nome', 'Tempo']]

# --- INTERFACE ---
st.markdown(f'<div style="text-align: center;"><img src="{URL_LOGO}" height="180"><h1>WOD Ranking Pro</h1></div>', unsafe_allow_html=True)

aba1, aba2, aba3 = st.tabs(["📝 REGISTRAR", "📅 HISTÓRICO", "🔥 ELITE"])

with aba1:
    st.markdown("### 📝 Registrar Treino")
    c1, c2 = st.columns(2)
    with c1: data_treino = st.date_input("Data do WOD", datetime.now())
    with c2: horario_sel = st.selectbox("Horário", ["06:00", "07:00", "16:20", "17:40", "18:30"])
    txt_input = st.text_area("NOME MINUTOS SEGUNDOS", height=150, key="input_wod")
    if st.button("🚀 SALVAR RESULTADOS"):
        if txt_input:
            dados = []
            for l in txt_input.strip().split('\n'):
                try:
                    partes = l.replace("'", " ").replace(":", " ").strip().split()
                    if len(partes) >= 1:
                        nome = " ".join([p for p in partes if not p.isdigit()]).upper().replace("-", "").strip()
                        nums = [p for p in partes if p.isdigit()]
                        if len(nums) >= 1:
                            m, s = int(nums[0]), (int(nums[1]) if len(nums) > 1 else 0)
                            t_str, seg = f"{m:02d}:{s:02d}", m*60 + s
                        else:
                            t_str, seg = "CAP", 99999
                        if nome:
                            dados.append({"Data": data_treino.strftime("%d/%m/%Y"), "Horario": horario_sel, "Nome": nome, "Tempo": t_str, "Segundos": seg})
                except: continue
            if requests.post(URL_GOOGLE_SCRIPT, json=dados).status_code == 200:
                st.success("Salvo!"); st.cache_data.clear(); st.rerun()

with aba2:
    st.markdown("### 🔍 Histórico")
    if st.button("🔄 ATUALIZAR"): st.cache_data.clear(); st.rerun()
    df_h = ler_dados_planilha()
    if not df_h.empty:
        d_sel = st.selectbox("Dia:", sorted(df_h["Data"].unique(), reverse=True))
        df_dia = df_h[df_h["Data"] == d_sel].copy()
        st.dataframe(formatar_tabela_bonita(df_dia), use_container_width=True, hide_index=True)

with aba3:
    st.markdown("### 🏆 Ranking de Elite")
    df_g = ler_dados_planilha()
    if not df_g.empty:
        df_g['Nome'] = df_g['Nome'].astype(str).str.upper().str.strip()
        lista_acum = []
        for d in df_g["Data"].unique():
            dia = df_g[df_g["Data"] == d].copy().sort_values("Segundos").reset_index(drop=True)
            dia['Pontos'] = [calcular_pontos_dinamico(i) for i in range(len(dia))]
            lista_acum.append(dia[['Nome', 'Pontos', 'Segundos']])
        
        # Agregando: Pontos (Soma), Wods (Contagem), Segundos (Soma para desempate)
        df_concat = pd.concat(lista_acum)
        rank = df_concat.groupby("Nome").agg(
            PTS=('Pontos', 'sum'), 
            WDS=('Pontos', 'count'),
            SEC_TOTAL=('Segundos', 'sum')
        ).reset_index()
        
        # ORDENAÇÃO: 
        # 1. Pontos (Descendente)
        # 2. WODs (Descendente)
        # 3. Segundos Totais (ASCENDENTE - Menos tempo é melhor)
        rank = rank.sort_values(by=['PTS', 'WDS', 'SEC_TOTAL'], ascending=[False, False, True]).reset_index(drop=True)

        # Formata o tempo total para exibição
        rank['TEMPO TOTAL'] = rank['SEC_TOTAL'].apply(formatar_segundos_para_tempo)
        
        pos_e = [("1º 🥇" if i==0 else "2º 🥈" if i==1 else "3º 🥉" if i==2 else f"{i+1}º") for i in range(len(rank))]
        rank.insert(0, '#', pos_e)
        
        # Exibe apenas as colunas relevantes
        st.dataframe(rank[['#', 'Nome', 'PTS', 'WDS', 'TEMPO TOTAL']], use_container_width=True, hide_index=True)
