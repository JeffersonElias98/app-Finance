import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Money Balance", page_icon="⚖️💰", layout="centered")
ARQUIVO_LOCAL = "dados.csv"

# --- CSS "NUCLEAR" PARA MOBILE ---
st.markdown("""
<style>
    /* 1. ESPAÇO NO TOPO (Para não cortar o logo) */
    .block-container {
        padding-top: 4rem !important; /* Aumentei bastante para garantir */
        padding-bottom: 3rem;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* 2. CABEÇALHO */
    .app-header { display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
    .logo-wrapper { position: relative; width: 55px; height: 55px; display: flex; justify-content: center; align-items: flex-end; margin-right: 10px; }
    .logo-scale { font-size: 3rem; line-height: 1; z-index: 1; }
    .logo-money { position: absolute; top: 2px; font-size: 1.4rem; z-index: 2; }
    .app-name { 
        font-family: sans-serif; 
        font-weight: 700; 
        font-size: clamp(1.5rem, 5vw, 2.2rem); 
        white-space: nowrap; 
    }

    /* 3. FORÇAR COLUNAS LADO A LADO (PC E MOBILE) */
    
    /* Isso afeta TODAS as colunas do app */
    div[data-testid="column"] {
        display: flex;
        flex-direction: column; /* Conteúdo dentro da coluna fica vertical */
        min-width: 0 !important; /* PERMITE ENCOLHER (Crucial para mobile) */
    }

    /* Regras específicas para telas pequenas (Celular) */
    @media (max-width: 640px) {
        
        /* PROIBIR QUEBRA DE LINHA nas linhas horizontais */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.5rem !important; /* Espaço pequeno entre colunas */
            align-items: center !important;
        }

        /* Ajuste dos botões de seta para não sumirem */
        div[data-testid="column"] button {
            padding: 0px !important;
            min-width: 40px !important;
            height: 40px !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Título do mês no celular */
        .month-title { font-size: 1.1rem !important; }

        /* MÉTRICAS (Receita, Despesa, Saldo) */
        /* Força os textos a diminuírem para caber 3 na linha */
        div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
        div[data-testid="stMetricValue"] { font-size: 0.85rem !important; }
        
        /* Esconder rodapé padrão do Streamlit */
        footer { display: none; }
    }

    /* Estilo dos Radio Buttons */
    div[role="radiogroup"] { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
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
        st.error("Descrição vazia")
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

# --- NAVEGAÇÃO ---
# Proporção [1, 4, 1] garante que o meio tenha mais espaço, mas as pontas existam
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if st.button("◀", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) - pd.DateOffset(months=1)).date()
        st.rerun()
with c2:
    meses = {1:"JAN", 2:"FEV", 3:"MAR", 4:"ABR", 5:"MAI", 6:"JUN", 7:"JUL", 8:"AGO", 9:"SET", 10:"OUT", 11:"NOV", 12:"DEZ"}
    m, y = st.session_state['data_nav'].month, st.session_state['data_nav'].year
    st.markdown(f"<h3 class='month-title' style='text-align: center; margin: 0; color: #4CAF50;'>{meses[m]} / {y}</h3>", unsafe_allow_html=True)
with c3:
    if st.button("▶", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) + pd.DateOffset(months=1)).date()
        st.rerun()

# --- FORMULÁRIO ---
with st.expander("➕ Nova Transação", expanded=st.session_state.expander_aberto):
    st.write("**Tipo:**")
    st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, label_visibility="collapsed", key="new_tipo")
    
    col_a, col_b = st.columns(2)
    with col_a: st.number_input("Valor (R$)", min_value=0.0, step=10.0, key="new_valor")
    with col_b: st.date_input("Data", value=date.today(), key="new_data")
        
    st.selectbox("Categoria", CATEGORIAS, key="new_cat")
    st.text_input("Descrição", key="new_desc")
    
    st.write("**Frequência:**")
    st.radio("Frequência", ["Único", "Parcelado", "Fixo Mensal"], horizontal=True, label_visibility="collapsed", key="new_freq")
    
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
    
    # SALDOS - FORÇADOS NA MESMA LINHA PELO CSS
    c_rec, c_desp, c_saldo = st.columns(3)
    c_rec.metric("Receitas", f"R$ {rec:,.2f}")
    c_desp.metric("Despesas", f"R$ {desp:,.2f}")
    c_saldo.metric("Saldo", f"R$ {rec+desp:,.2f}")
    
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
