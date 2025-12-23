import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Money Balance", page_icon="⚖️💰", layout="centered")
ARQUIVO_LOCAL = "dados.csv"

# --- CSS: COMPACTO, LADO A LADO E SEGURO ---
st.markdown("""
<style>
    /* 1. Ajuste de Topo */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 5rem;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* 2. CABEÇALHO */
    .app-header { display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    .logo-wrapper { position: relative; width: 50px; height: 50px; display: flex; justify-content: center; align-items: flex-end; margin-right: 10px; }
    .logo-scale { font-size: 2.5rem; line-height: 1; z-index: 1; }
    .logo-money { position: absolute; top: 0px; font-size: 1.2rem; z-index: 2; }
    .app-name { 
        font-family: sans-serif; font-weight: 700; 
        font-size: clamp(1.4rem, 5vw, 1.8rem); 
        white-space: nowrap; 
    }

    /* 3. REGRAS PARA CELULAR (Telas pequenas) */
    @media (max-width: 640px) {
        
        /* FORÇA LINHA HORIZONTAL nos blocos de colunas */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 5px !important;
        }

        /* COLUNAS: Permite encolher para caber */
        div[data-testid="column"] {
            min-width: 0 !important;
            padding: 0 !important;
        }

        /* --- AJUSTE DA NAVEGAÇÃO (SETAS E MÊS) --- */
        /* Força botões pequenos */
        button[kind="secondary"] {
            padding: 0 !important;
            min-height: 35px !important;
            line-height: 1 !important; 
        }
        /* Título do Mês Compacto */
        h3 { 
            font-size: 1rem !important; 
            white-space: nowrap !important;
            margin: 0 !important;
        }

        /* --- AJUSTE DOS SALDOS (RECEITA/DESPESA/SALDO) --- */
        /* Reduz drásticamente a fonte para caber 3 lado a lado */
        div[data-testid="stMetricLabel"] { 
            font-size: 0.65rem !important; /* Texto "Receita" pequeno */
        }
        div[data-testid="stMetricValue"] { 
            font-size: 0.85rem !important; /* Valor "R$ 100" pequeno */
            font-weight: 700 !important;
        }

        /* Esconde rodapé */
        footer { display: none; }
    }
    
    /* Container de Categorias com rolagem (Sem teclado) */
    .category-container {
        max-height: 150px;
        overflow-y: auto;
        border: 1px solid #444;
        padding: 5px;
        border-radius: 8px;
        background-color: #262730;
    }
    /* Estilo Radio Buttons */
    div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 8px; }
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

def cb_alternar_status(item_id):
    for d in st.session_state['dados']:
        if d['ID'] == item_id:
            d['Status'] = "Pago" if d['Status'] == "Pendente" else "Pendente"
            break
    salvar_dados_arquivo(st.session_state['dados'])

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state: st.session_state['dados'] = carregar_dados()
if 'data_nav' not in st.session_state: st.session_state['data_nav'] = date.today()
if 'item_exclusao' not in st.session_state: st.session_state['item_exclusao'] = None
if 'expander_aberto' not in st.session_state: st.session_state.expander_aberto = False

CATEGORIAS = sorted(["Alimentação", "Educação", "Investimentos", "Lazer", "Moradia", "Carro", "Outros", "Salário", "Saúde", "Serviços", "Transporte", "Vestuário", "Extra"])

# --- TOPO ---
st.markdown('<div class="app-header"><div class="logo-wrapper"><span class="logo-scale">⚖️</span><span class="logo-money">💰</span></div><span class="app-name">Money Balance</span></div>', unsafe_allow_html=True)
st.divider()

# --- NAVEGAÇÃO ---
# Proporção [1, 6, 1] dá muito espaço para o mês e pouco para as setas
c1, c2, c3 = st.columns([1, 6, 1])
with c1:
    if st.button("◀", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) - pd.DateOffset(months=1)).date()
        st.rerun()
with c2:
    meses = {1:"JAN", 2:"FEV", 3:"MAR", 4:"ABR", 5:"MAI", 6:"JUN", 7:"JUL", 8:"AGO", 9:"SET", 10:"OUT", 11:"NOV", 12:"DEZ"}
    m, y = st.session_state['data_nav'].month, st.session_state['data_nav'].year
    st.markdown(f"<h3 style='text-align: center; margin: 0; padding-top: 5px; color: #4CAF50;'>{meses[m]} / {y}</h3>", unsafe_allow_html=True)
with c3:
    if st.button("▶", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) + pd.DateOffset(months=1)).date()
        st.rerun()

# --- FORMULÁRIO ---
with st.expander("➕ Nova Transação", expanded=st.session_state.expander_aberto):
    st.write("**Tipo:**")
    st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, label_visibility="collapsed", key="new_tipo")
    
    col_a, col_b = st.columns(2)
    with col_a: st.number_input("Valor", min_value=0.0, step=10.0, key="new_valor")
    with col_b: st.date_input("Data", value=date.today(), key="new_data")
        
    st.write("**Categoria:**")
    st.markdown('<div class="category-container">', unsafe_allow_html=True)
    st.radio("Categoria", CATEGORIAS, key="new_cat", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    # SALDOS (Forçados lado a lado pelo CSS)
    # Importante: Proporção igual
    c_rec, c_desp, c_saldo = st.columns([1, 1, 1])
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
            # Layout do card mantido
            ci, cv, cb = st.columns([3, 1.5, 1.2])
            with ci:
                st.markdown(f"**{'🟢' if row['Tipo'] == 'Receita' else '🔴'} {row['Descrição']}**")
                st.caption(f"{row['Categoria']} • {row['Data'].strftime('%d/%m')}")
            with cv:
                cor = "green" if row['Valor'] > 0 else "red"
                st.markdown(f"<span style='color:{cor}; font-weight:bold;'>R$ {row['Valor']:,.0f}</span>", unsafe_allow_html=True)
            with cb:
                c1, c2 = st.columns(2)
                with c1:
                    icon_status = "✅" if row['Status'] == "Pago" else "⏳"
                    st.button(icon_status, key=f"st_{row['ID']}", on_click=cb_alternar_status, args=(row['ID'],))
                with c2:
                    if st.button("🗑️", key=f"del_{row['ID']}"):
                        st.session_state['item_exclusao'] = row.to_dict()
                        st.rerun()
else:
    st.info("Sem dados neste mês.")

st.markdown("<br><div style='text-align: center; color: gray; font-size: 12px;'>made by JEFFERSON ELIAS</div>", unsafe_allow_html=True)
