import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Money Balance", page_icon="⚖️💰", layout="centered")
ARQUIVO_LOCAL = "dados.csv"

# --- CSS AVANÇADO PARA FORÇAR LAYOUT HORIZONTAL NO MOBILE ---
st.markdown("""
<style>
    /* Ajuste de Topo */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem; }

    /* Cabeçalho */
    .app-header { display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    .logo-wrapper { position: relative; width: 50px; height: 50px; display: flex; justify-content: center; align-items: flex-end; margin-right: 8px; }
    .logo-scale { font-size: 2.5rem; line-height: 1; z-index: 1; }
    .logo-money { position: absolute; top: 2px; font-size: 1.2rem; z-index: 2; }
    .app-name { font-family: sans-serif; font-weight: 700; font-size: clamp(1.2rem, 4vw, 2rem); white-space: nowrap; }

    /* Título do Mês Responsivo */
    .month-title { 
        white-space: nowrap; 
        margin: 0; 
        text-align: center; 
        font-weight: bold; 
        color: #4CAF50; 
        font-size: clamp(0.9rem, 4vw, 1.4rem); /* Diminui a fonte se a tela for pequena */
    }

    /* ============================================================
       A MÁGICA DO MOBILE (Regras para telas menores que 640px)
    ============================================================ */
    @media (max-width: 640px) {
        
        /* 1. FORÇA as colunas a ficarem lado a lado (Horizontal) */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important; 
            flex-wrap: nowrap !important;
            gap: 2px !important; /* Diminui espaço entre colunas */
        }
        
        /* 2. Permite que as colunas encolham para caber na tela */
        div[data-testid="column"] {
            min-width: 0px !important;
            flex: 1 1 auto !important;
            padding: 0 !important;
        }

        /* 3. Ajusta botões para serem compactos no celular */
        button {
            padding: 0.2rem 0.5rem !important;
            min-height: 0px !important;
            height: auto !important;
            font-size: 0.8rem !important;
        }
        
        /* 4. Métricas (Saldo/Receita) menores para caberem 3 na linha */
        div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
        div[data-testid="stMetricValue"] { font-size: 0.9rem !important; }
        
        /* Esconde elementos desnecessários do Streamlit para ganhar espaço */
        div[data-testid="stToolbar"] { display: none; }
        footer { display: none; }
    }
    
    /* Estilo dos Radio Buttons como "Botões" */
    div[role="radiogroup"] {
        display: flex;
        gap: 10px;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def carregar_dados():
    if not os.path.exists(ARQUIVO_LOCAL): return []
    try:
        df = pd.read_csv(ARQUIVO_LOCAL)
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df.to_dict('records')
    except: return []

def salvar_dados_arquivo(dados_lista):
    if len(dados_lista) > 0:
        pd.DataFrame(dados_lista).to_csv(ARQUIVO_LOCAL, index=False)
    else:
        with open(ARQUIVO_LOCAL, "w") as f:
            f.write("ID,SeriesID,Data,Descrição,Categoria,Valor,Tipo,Status\n")

def cb_processar_salvamento():
    desc = st.session_state.new_desc
    val = st.session_state.new_valor
    cat = st.session_state.new_cat
    tipo = st.session_state.new_tipo
    freq = st.session_state.new_freq
    data = st.session_state.new_data
    
    if not desc:
        st.error("Erro: Descrição vazia")
        return

    qtd = 1
    if freq == 'Parcelado': qtd = st.session_state.new_qtd_parc
    elif freq == 'Fixo Mensal': qtd = 12 
    
    id_serie = str(uuid.uuid4())
    val_final = val / qtd if freq == "Parcelado" else val
    sinal = 1 if tipo == "Receita" else -1
    
    novos = []
    for i in range(qtd):
        dt = pd.to_datetime(data) + pd.DateOffset(months=i)
        desc_f = f"{desc} ({i+1}/{qtd})" if freq == "Parcelado" else desc
        novos.append({
            "ID": str(uuid.uuid4()), "SeriesID": id_serie, "Data": dt.date(),
            "Descrição": desc_f, "Categoria": cat, "Valor": val_final * sinal,
            "Tipo": tipo, "Status": "Pendente"
        })

    st.session_state['dados'].extend(novos)
    salvar_dados_arquivo(st.session_state['dados'])
    
    # Limpa inputs
    st.session_state.new_desc = ""
    st.session_state.new_valor = 0.0
    st.session_state.expander_aberto = False

def cb_excluir(item):
    st.session_state['dados'] = [x for x in st.session_state['dados'] if x['ID'] != item['ID']]
    salvar_dados_arquivo(st.session_state['dados'])
    st.session_state['item_exclusao'] = None

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state: st.session_state['dados'] = carregar_dados()
if 'data_nav' not in st.session_state: st.session_state['data_nav'] = date.today()
if 'item_exclusao' not in st.session_state: st.session_state['item_exclusao'] = None
if 'expander_aberto' not in st.session_state: st.session_state.expander_aberto = False

CATEGORIAS = sorted(["Alimentação", "Educação", "Investimentos", "Lazer", "Moradia", "Carro", "Outros", "Salário", "Saúde", "Serviços", "Transporte", "Vestuário", "Extra"])

# --- CABEÇALHO ---
st.markdown('<div class="app-header"><div class="logo-wrapper"><span class="logo-scale">⚖️</span><span class="logo-money">💰</span></div><span class="app-name">Money Balance</span></div>', unsafe_allow_html=True)
st.divider()

# --- NAVEGAÇÃO (Forçada Horizontal no CSS) ---
# Usando colunas mais apertadas para as setas [1, 5, 1]
c1, c2, c3 = st.columns([1, 5, 1])
with c1:
    if st.button("◀", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) - pd.DateOffset(months=1)).date()
        st.rerun()
with c2:
    meses = {1:"JAN", 2:"FEV", 3:"MAR", 4:"ABR", 5:"MAI", 6:"JUN", 7:"JUL", 8:"AGO", 9:"SET", 10:"OUT", 11:"NOV", 12:"DEZ"}
    m, y = st.session_state['data_nav'].month, st.session_state['data_nav'].year
    st.markdown(f"<h3 class='month-title'>{meses[m]} / {y}</h3>", unsafe_allow_html=True)
with c3:
    if st.button("▶", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) + pd.DateOffset(months=1)).date()
        st.rerun()

# --- FORMULÁRIO ---
with st.expander("➕ Nova Transação", expanded=st.session_state.expander_aberto):
    # SOLUÇÃO DO TECLADO: Usar Radio horizontal
    st.write("**Tipo:**")
    st.radio("Tipo Transação", ["Despesa", "Receita"], horizontal=True, label_visibility="collapsed", key="new_tipo")
    
    # Colunas para Data e Valor (Lado a lado no mobile)
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        st.number_input("Valor (R$)", min_value=0.0, step=10.0, key="new_valor")
    with c_f2:
        st.date_input("Data", value=date.today(), key="new_data")
        
    st.selectbox("Categoria", CATEGORIAS, key="new_cat")
    st.text_input("Descrição", key="new_desc")
    
    st.write("**Frequência:**")
    st.radio("Frequência Repetição", ["Único", "Parcelado", "Fixo Mensal"], horizontal=True, label_visibility="collapsed", key="new_freq")
    
    if st.session_state.new_freq == "Parcelado":
        st.number_input("Nº Parcelas", min_value=2, value=2, key="new_qtd_parc")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("💾 Salvar", type="primary", use_container_width=True, on_click=cb_processar_salvamento)

# --- EXIBIÇÃO ---
if len(st.session_state['dados']) > 0:
    df = pd.DataFrame(st.session_state['dados'])
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    mask = (pd.to_datetime(df['Data']).dt.year == y) & (pd.to_datetime(df['Data']).dt.month == m)
    df_mes = df[mask].sort_values(by="Data", ascending=False)

    rec = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
    desp = df_mes[df_mes['Valor'] < 0]['Valor'].sum()
    
    st.divider()
    # TOTAIS (Forçado Horizontal no CSS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {rec:,.2f}")
    c2.metric("Despesas", f"R$ {desp:,.2f}")
    c3.metric("Saldo", f"R$ {rec+desp:,.2f}")
    st.divider()

    if st.session_state['item_exclusao']:
        item = st.session_state['item_exclusao']
        st.warning(f"Apagar: **{item['Descrição']}**?")
        cd1, cd2, cd3, cd4 = st.columns(4)
        if cd1.button("Só Este"): cb_excluir(item); st.rerun()
        if cd2.button("Este+Fut"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if not (x['SeriesID'] == item['SeriesID'] and x['Data'] >= item['Data'])]
            salvar_dados_arquivo(st.session_state['dados']); st.session_state['item_exclusao'] = None; st.rerun()
        if cd3.button("Série"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if x['SeriesID'] != item['SeriesID']]
            salvar_dados_arquivo(st.session_state['dados']); st.session_state['item_exclusao'] = None; st.rerun()
        if cd4.button("Sair"): st.session_state['item_exclusao'] = None; st.rerun()

    for idx, row in df_mes.iterrows():
        with st.container(border=True):
            # No container de cada item, mantemos proporções que funcionam
            ci, cv, cb = st.columns([3, 1.5, 0.6])
            with ci:
                st.markdown(f"**{'🟢' if row['Tipo'] == 'Receita' else '🔴'} {row['Descrição']}**")
                st.caption(f"{row['Categoria']} • {row['Data'].strftime('%d/%m')}")
            with cv:
                cor = "green" if row['Valor'] > 0 else "red"
                st.markdown(f"<span style='color:{cor}; font-weight:bold;'>R$ {row['Valor']:,.0f}</span>", unsafe_allow_html=True)
                st.caption("✅" if row['Status'] == 'Pago' else "⏳")
            with cb:
                if st.button("🗑️", key=f"del_{row['ID']}", use_container_width=True):
                    st.session_state['item_exclusao'] = row.to_dict()
                    st.rerun()
else:
    st.info("Sem dados neste mês.")

st.markdown("<br><div style='text-align: center; color: gray; font-size: 12px;'>made by JEFFERSON ELIAS</div>", unsafe_allow_html=True)
