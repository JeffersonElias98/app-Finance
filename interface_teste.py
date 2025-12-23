import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# --- CONFIGURAÇÃO ---
# Ícone da aba agora é o conjunto
st.set_page_config(page_title="Money Balance", page_icon="⚖️💰", layout="centered")
ARQUIVO_LOCAL = "dados.csv"

# --- CSS PARA LOGO E RESPONSIVIDADE ---
st.markdown("""
<style>
    /* 1. Garante espaço no topo para não cortar o cabeçalho */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2rem;
    }

    /* 2. Cabeçalho Flexível */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
    }

    /* 3. Técnica para sobrepor os emojis (Logo) */
    .logo-wrapper {
        position: relative;
        width: 60px;
        height: 60px;
        display: flex;
        justify-content: center;
        align-items: flex-end; /* Alinha a balança na base */
        margin-right: 10px;
    }
    .logo-scale {
        font-size: 3rem;
        line-height: 1;
        z-index: 1;
    }
    .logo-money {
        position: absolute;
        top: 5px; /* Ajuste fino da posição do dinheiro */
        font-size: 1.4rem;
        z-index: 2; /* Fica na frente da balança */
    }

    /* 4. Título do App Responsivo (Diminui em telas pequenas) */
    .app-name {
        font-family: sans-serif;
        font-weight: 700;
        /* A fonte varia entre 1.5rem e 2.2rem dependendo da largura da tela */
        font-size: clamp(1.5rem, 5vw, 2.2rem);
        white-space: nowrap;
    }

    /* 5. Correção da Navegação */
    div[data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* Garante que os botões tenham um tamanho mínimo para não serem esmagados */
    div[data-testid="column"] button {
         min-width: 50px;
    }
    /* Título do mês responsivo */
    .month-title {
         white-space: nowrap;
         margin: 0;
         text-align: center;
         font-weight: bold;
         color: #4CAF50;
         /* A fonte varia entre 1.1rem e 1.5rem */
         font-size: clamp(1.1rem, 4vw, 1.5rem);
    }
    
    /* Ajustes gerais dos cards */
    .valor-destaque { font-weight: bold; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def carregar_dados():
    if not os.path.exists(ARQUIVO_LOCAL):
        return []
    try:
        df = pd.read_csv(ARQUIVO_LOCAL)
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df.to_dict('records')
    except:
        return []

def salvar_dados_arquivo(dados_lista):
    if len(dados_lista) > 0:
        pd.DataFrame(dados_lista).to_csv(ARQUIVO_LOCAL, index=False)
    else:
        with open(ARQUIVO_LOCAL, "w") as f:
            f.write("ID,SeriesID,Data,Descrição,Categoria,Valor,Tipo,Status\n")

# --- LÓGICA DE SALVAMENTO ---
def processar_salvamento():
    desc = st.session_state.new_desc
    val = st.session_state.new_valor
    cat = st.session_state.new_cat
    tipo = st.session_state.new_tipo
    freq = st.session_state.new_freq
    data = st.session_state.new_data
    
    if not desc:
        st.error("Digite uma descrição!")
        return

    qtd = 1
    if freq == 'Parcelado': 
        qtd = st.session_state.new_qtd_parc
    elif freq == 'Fixo Mensal': 
        qtd = 12 
    
    id_serie = str(uuid.uuid4())
    val_final = val
    if freq == "Parcelado":
        val_final = val / qtd
    
    sinal = 1 if tipo == "Receita" else -1
    
    novos = []
    for i in range(qtd):
        dt = pd.to_datetime(data) + pd.DateOffset(months=i)
        desc_final = desc
        if freq == "Parcelado":
            desc_final = f"{desc} ({i+1}/{qtd})"
        
        novos.append({
            "ID": str(uuid.uuid4()), "SeriesID": id_serie, "Data": dt.date(),
            "Descrição": desc_final, "Categoria": cat, "Valor": val_final * sinal,
            "Tipo": tipo, "Status": "Pendente"
        })

    st.session_state['dados'].extend(novos)
    salvar_dados_arquivo(st.session_state['dados'])
    st.toast("Salvo com sucesso!", icon="✅")
    
    st.session_state.new_desc = ""
    st.session_state.new_valor = 0.00

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state: st.session_state['dados'] = carregar_dados()
if 'data_nav' not in st.session_state: st.session_state['data_nav'] = date.today()
if 'item_exclusao' not in st.session_state: st.session_state['item_exclusao'] = None

CATEGORIAS = sorted([
    "Alimentação", "Educação", "Investimentos", "Lazer", "Moradia", 
    "Carro", "Outros", "Salário", "Saúde", "Serviços", 
    "Transporte", "Vestuário", "Extra"
])

# --- CABEÇALHO COM LOGO SOBREPOSTO ---
st.markdown("""
    <div class="app-header">
        <div class="logo-wrapper">
            <span class="logo-scale">⚖️</span>
            <span class="logo-money">💰</span>
        </div>
        <span class="app-name">Money Balance</span>
    </div>
""", unsafe_allow_html=True)

st.divider()

# --- NAVEGAÇÃO RESPONSIVA ---
# Ajustei as proporções para dar mais espaço ao texto central
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if st.button("◀", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) - pd.DateOffset(months=1)).date()
        st.rerun()
with c2:
    meses = {1:"JAN", 2:"FEV", 3:"MAR", 4:"ABR", 5:"MAI", 6:"JUN", 7:"JUL", 8:"AGO", 9:"SET", 10:"OUT", 11:"NOV", 12:"DEZ"}
    m, y = st.session_state['data_nav'].month, st.session_state['data_nav'].year
    # Usa a classe CSS responsiva
    st.markdown(f"<h3 class='month-title'>{meses[m]} / {y}</h3>", unsafe_allow_html=True)
with c3:
    if st.button("▶", use_container_width=True):
        st.session_state['data_nav'] = (pd.to_datetime(st.session_state['data_nav']) + pd.DateOffset(months=1)).date()
        st.rerun()

# --- ÁREA DE CADASTRO ---
with st.expander("➕ Nova Transação", expanded=False):
    c_form1, c_form2 = st.columns(2)
    with c_form1:
        st.selectbox("Tipo", ["Despesa", "Receita"], key="new_tipo")
        st.number_input("Valor", min_value=0.0, step=10.0, key="new_valor")
        st.date_input("Data", value=date.today(), key="new_data")
    with c_form2:
        st.selectbox("Categoria", CATEGORIAS, key="new_cat")
        st.text_input("Descrição", key="new_desc")
        st.selectbox("Frequência", ["Único", "Parcelado", "Fixo Mensal"], key="new_freq")
    
    if st.session_state.new_freq == "Parcelado":
        st.number_input("Nº Parcelas", min_value=2, value=2, key="new_qtd_parc")
    
    if st.button("💾 Salvar Lançamento", type="primary", use_container_width=True):
        processar_salvamento()
        st.rerun()

# --- FILTRAGEM E EXIBIÇÃO ---
if len(st.session_state['dados']) > 0:
    df = pd.DataFrame(st.session_state['dados'])
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    mask = (pd.to_datetime(df['Data']).dt.year == y) & (pd.to_datetime(df['Data']).dt.month == m)
    df_mes = df[mask].sort_values(by="Data", ascending=False)

    # Totais
    rec = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
    desp = df_mes[df_mes['Valor'] < 0]['Valor'].sum()
    saldo = rec + desp
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", f"R$ {rec:,.2f}")
    c2.metric("Despesas", f"R$ {desp:,.2f}")
    c3.metric("Saldo", f"R$ {saldo:,.2f}")
    st.divider()

    # Exclusão Inteligente
    if st.session_state['item_exclusao']:
        item = st.session_state['item_exclusao']
        st.warning(f"Apagar: **{item['Descrição']}**?")
        col_del1, col_del2, col_del3, col_del4 = st.columns(4)
        if col_del1.button("Só Este"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if x['ID'] != item['ID']]
            salvar_dados_arquivo(st.session_state['dados'])
            st.session_state['item_exclusao'] = None
            st.rerun()
        if col_del2.button("Este e Futuros"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if not (x['SeriesID'] == item['SeriesID'] and x['Data'] >= item['Data'])]
            salvar_dados_arquivo(st.session_state['dados'])
            st.session_state['item_exclusao'] = None
            st.rerun()
        if col_del3.button("Série Toda"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if x['SeriesID'] != item['SeriesID']]
            salvar_dados_arquivo(st.session_state['dados'])
            st.session_state['item_exclusao'] = None
            st.rerun()
        if col_del4.button("Cancelar"):
            st.session_state['item_exclusao'] = None
            st.rerun()
        st.divider()

    # Listagem Minimalista
    if not df_mes.empty:
        for idx, row in df_mes.iterrows():
            with st.container(border=True):
                c_info, c_val, c_btn = st.columns([3, 1.5, 0.6])
                
                with c_info:
                    icon = "🟢" if row['Tipo'] == "Receita" else "🔴"
                    st.markdown(f"**{icon} {row['Descrição']}**")
                    st.caption(f"{row['Categoria']} • {row['Data'].strftime('%d/%m')}")
                
                with c_val:
                    cor = "green" if row['Valor'] > 0 else "red"
                    st.markdown(f"<span style='color:{cor}; font-weight:bold;'>R$ {row['Valor']:,.2f}</span>", unsafe_allow_html=True)
                    if row['Status'] == 'Pago': st.caption("✅ Pago")
                    else: st.caption("⏳ Pendente")

                with c_btn:
                    if st.button("🗑️", key=f"del_{row['ID']}", use_container_width=True):
                        st.session_state['item_exclusao'] = row.to_dict()
                        st.rerun()
    else:
        st.info("Nenhum lançamento neste mês.")
else:
    st.info("Banco de dados vazio.")

# --- RODAPÉ ---
st.markdown("<br><br><div style='text-align: center; color: gray; font-size: 12px;'>made by JEFFERSON ELIAS</div>", unsafe_allow_html=True)
