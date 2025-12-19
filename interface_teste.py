import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import uuid
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Minhas Finanças", page_icon="💰", layout="wide")
ARQUIVO_LOCAL = "dados.csv"

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
    try:
        if len(dados_lista) > 0:
            pd.DataFrame(dados_lista).to_csv(ARQUIVO_LOCAL, index=False)
        else:
            with open(ARQUIVO_LOCAL, "w") as f:
                f.write("ID,SeriesID,Data,Descrição,Categoria,Valor,Tipo,Status\n")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# --- CALLBACKS ---
def salvar_lancamento():
    descricao = st.session_state.get('form_desc', '')
    valor = st.session_state.get('form_valor', 0.0)
    categoria = st.session_state.get('form_cat', '')
    tipo = st.session_state.get('form_tipo', 'Despesa')
    freq = st.session_state.get('form_freq', 'Único')
    data_ref = st.session_state.get('form_data', date.today())
    pago = st.session_state.get('form_pago', False)
    
    if not descricao:
        st.error("Erro: Descrição obrigatória!")
        return

    qtd = 1
    if freq == 'Parcelado':
        qtd = st.session_state.get('form_qtd_parc', 2)
    elif freq == 'Fixo Mensal':
        qtd = st.session_state.get('form_qtd_fixo', 60)

    id_serie = str(uuid.uuid4())
    val_final = valor
    if freq == "Parcelado":
        val_final = valor / qtd
    
    status = "Pago" if pago else "Pendente"
    sinal = 1 if tipo == "Receita" else -1
    
    novos = []
    for i in range(qtd):
        dt = pd.to_datetime(data_ref) + pd.DateOffset(months=i)
        desc_final = descricao
        if freq == "Parcelado":
            desc_final = f"{descricao} ({i+1}/{qtd})"
        
        novos.append({
            "ID": str(uuid.uuid4()), "SeriesID": id_serie, "Data": dt.date(),
            "Descrição": desc_final, "Categoria": categoria, "Valor": val_final * sinal,
            "Tipo": tipo, "Status": status
        })

    st.session_state['dados'].extend(novos)
    salvar_dados_arquivo(st.session_state['dados'])
    st.toast("Lançamento salvo!", icon="✅")

    st.session_state['form_desc'] = ""
    st.session_state['form_valor'] = 0.00
    st.session_state['form_freq'] = "Único"
    st.session_state['form_pago'] = False
    st.session_state['form_qtd_parc'] = 2
    st.session_state['form_qtd_fixo'] = 60

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state:
    st.session_state['dados'] = carregar_dados()
if 'item_exclusao' not in st.session_state:
    st.session_state['item_exclusao'] = None
if 'data_navegacao' not in st.session_state:
    st.session_state['data_navegacao'] = date.today()
if 'privacidade' not in st.session_state:
    st.session_state['privacidade'] = False

if 'lista_categorias' not in st.session_state:
    padrao = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Serviços", "Salário", "Investimentos", "Outros"]
    if len(st.session_state['dados']) > 0:
        existentes = list(set([d['Categoria'] for d in st.session_state['dados']]))
        st.session_state['lista_categorias'] = sorted(list(set(padrao + existentes)))
    else:
        st.session_state['lista_categorias'] = padrao

# --- BARRA LATERAL ---
st.sidebar.header("📝 Novo Lançamento")
st.sidebar.date_input("Data", st.session_state['data_navegacao'], key="form_data") 
st.sidebar.text_input("Descrição", placeholder="Ex: Mercado", key="form_desc")
st.sidebar.number_input("Valor (R$)", min_value=0.00, step=10.00, format="%.2f", key="form_valor")
st.sidebar.selectbox("Categoria", st.session_state['lista_categorias'], key="form_cat")
st.sidebar.radio("Tipo", ["Despesa", "Receita"], horizontal=True, key="form_tipo")
st.sidebar.markdown("---")
recorrencia = st.sidebar.radio("Frequência:", ["Único", "Parcelado", "Fixo Mensal"], key="form_freq")

if recorrencia == "Parcelado":
    st.sidebar.number_input("Nº de Parcelas", min_value=2, value=2, key="form_qtd_parc")
elif recorrencia == "Fixo Mensal":
    st.sidebar.number_input("Meses", min_value=2, value=60, key="form_qtd_fixo")

st.sidebar.checkbox("Já pago?", False, key="form_pago")
st.sidebar.button("💾 Salvar Lançamento", on_click=salvar_lancamento, type="primary")

with st.sidebar.expander("⚙️ Categorias"):
    nova = st.text_input("Nova:", key="nova_cat_input")
    def add_cat():
        n = st.session_state.get('nova_cat_input')
        if n and n not in st.session_state['lista_categorias']:
            st.session_state['lista_categorias'].append(n)
            st.session_state['lista_categorias'].sort()
            st.session_state['nova_cat_input'] = ""
    st.button("➕ Add", on_click=add_cat)
    rem = st.selectbox("Apagar:", st.session_state['lista_categorias'], key="del_cat_select")
    def del_cat():
        r = st.session_state.get('del_cat_select')
        if len(st.session_state['lista_categorias']) > 1:
            st.session_state['lista_categorias'].remove(r)
    st.button("🗑️ Del", on_click=del_cat)

# --- ÁREA PRINCIPAL ---
st.title("💰 Controle Financeiro")

c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
with c_nav1:
    if st.button("◀ Anterior", use_container_width=True):
        st.session_state['data_navegacao'] = (pd.to_datetime(st.session_state['data_navegacao']) - pd.DateOffset(months=1)).date()
        st.rerun()
with c_nav2:
    meses_pt = {1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"}
    m = st.session_state['data_navegacao'].month
    y = st.session_state['data_navegacao'].year
    st.markdown(f"<h2 style='text-align: center; margin: 0; color: #4CAF50;'>{meses_pt[m]} / {y}</h2>", unsafe_allow_html=True)
with c_nav3:
    if st.button("Próximo ▶", use_container_width=True):
        st.session_state['data_navegacao'] = (pd.to_datetime(st.session_state['data_navegacao']) + pd.DateOffset(months=1)).date()
        st.rerun()

st.divider()

if st.session_state['item_exclusao']:
    item = st.session_state['item_exclusao']
    with st.container():
        st.warning(f"Apagar: **{item['Descrição']}**?")
        c1, c2, c3, c4 = st.columns(4)
        save = False
        if c1.button("Só Este"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if x['ID'] != item['ID']]
            save = True
        if c2.button("Este e Futuros"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if not (x['SeriesID'] == item['SeriesID'] and x['Data'] >= item['Data'])]
            save = True
        if c3.button("Série Toda"):
            st.session_state['dados'] = [x for x in st.session_state['dados'] if x['SeriesID'] != item['SeriesID']]
            save = True
        if c4.button("Cancelar"):
            st.session_state['item_exclusao'] = None
            st.rerun()
        if save:
            salvar_dados_arquivo(st.session_state['dados'])
            st.session_state['item_exclusao'] = None
            st.rerun()

# DADOS E VISUALIZAÇÃO
if len(st.session_state['dados']) > 0:
    df = pd.DataFrame(st.session_state['dados'])
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    mask = (pd.to_datetime(df['Data']).dt.year == y) & (pd.to_datetime(df['Data']).dt.month == m)
    df_filtrado = df[mask].sort_values(by="Data").copy()
    
    if not df_filtrado.empty:
        
        # 1. BOTÃO OLHO (Topo da Tabela)
        col_vazia, col_olho = st.columns([15, 1])
        with col_olho:
            icone = "🙈" if st.session_state['privacidade'] else "👁️"
            if st.button(icone, help="Privacidade"):
                st.session_state['privacidade'] = not st.session_state['privacidade']
                st.rerun()

        # 2. TABELA DE DADOS
        df_filtrado["Excluir?"] = False
        if st.session_state['privacidade']:
            df_display = df_filtrado.copy()
            df_display['Valor'] = "••••••"
            st.dataframe(df_display, column_config={"ID": None, "SeriesID": None, "Tipo": None, "Excluir?": None, "Data": st.column_config.DateColumn("Dia", format="DD/MM"), "Valor": st.column_config.TextColumn("Valor"), "Categoria": st.column_config.TextColumn("Categoria"), "Status": st.column_config.TextColumn("Status")}, hide_index=True, use_container_width=True)
        else:
            df_editado = st.data_editor(df_filtrado, column_config={"ID": None, "SeriesID": None, "Tipo": None, "Excluir?": st.column_config.CheckboxColumn("🗑️", width="small"), "Data": st.column_config.DateColumn("Dia", format="DD/MM"), "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"), "Categoria": st.column_config.SelectboxColumn("Categoria", options=st.session_state['lista_categorias'], required=True), "Status": st.column_config.SelectboxColumn("Status", options=["Pago", "Pendente"], required=True)}, hide_index=True, use_container_width=True, key=f"ed_{m}_{y}")
            
            itens_ex = df_editado[df_editado["Excluir?"] == True]
            if not itens_ex.empty:
                st.session_state['item_exclusao'] = itens_ex.iloc[0].to_dict()
                st.rerun()

            cols = ["Data", "Descrição", "Valor", "Categoria", "Status"]
            if not df_editado[cols].equals(df_filtrado[cols]):
                mudou = False
                for idx, row in df_editado.iterrows():
                    for item in st.session_state['dados']:
                        if item['ID'] == row['ID']:
                            if (item['Status'] != row['Status'] or item['Valor'] != row['Valor'] or item['Descrição'] != row['Descrição'] or item['Data'] != row['Data'] or item['Categoria'] != row['Categoria']):
                                item.update({'Data': row['Data'], 'Descrição': row['Descrição'], 'Valor': row['Valor'], 'Categoria': row['Categoria'], 'Status': row['Status']})
                                mudou = True
                            break
                if mudou:
                    salvar_dados_arquivo(st.session_state['dados'])
                    st.toast("Salvo!")

        # 3. TOTAIS
        st.divider()
        rec = df_filtrado[df_filtrado['Valor'] > 0]['Valor'].sum()
        desp = df_filtrado[df_filtrado['Valor'] < 0]['Valor'].sum()
        def fmt(v): return "••••••" if st.session_state['privacidade'] else f"R$ {v:,.2f}"
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", fmt(rec))
        c2.metric("Despesas", fmt(desp))
        c3.metric("Saldo Líquido", fmt(rec+desp))

        # 4. GRÁFICO COMPACTO
        if not st.session_state['privacidade']:
            df_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa'].copy()
            if not df_despesas.empty:
                st.divider()
                st.subheader("📊 Distribuição de Despesas")
                
                df_despesas['Valor_Abs'] = df_despesas['Valor'].abs()
                df_chart = df_despesas.groupby('Categoria')['Valor_Abs'].sum().reset_index()
                
                # Ajuste de Layout: Proporção [1.5, 2] para o gráfico não esticar muito
                c_graf, c_dados = st.columns([1.5, 2])
                
                with c_graf:
                    fig = px.pie(
                        df_chart, 
                        values='Valor_Abs', 
                        names='Categoria', 
                        hole=0.6,
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        height=350 # REDUZI A ALTURA AQUI
                    )
                    fig.update_layout(margin=dict(t=10, b=10, l=0, r=0), showlegend=False)
                    fig.update_traces(textinfo='percent+label', textfont_size=10)
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_dados:
                    df_chart = df_chart.sort_values(by="Valor_Abs", ascending=False)
                    for i, r in df_chart.iterrows():
                        percent = (r['Valor_Abs'] / df_despesas['Valor_Abs'].sum()) * 100
                        st.markdown(f"<span style='font-size: 0.9em;'>**{r['Categoria']}**</span>", unsafe_allow_html=True)
                        st.progress(int(percent))
                        st.markdown(f"<span style='font-size: 0.8em; color: gray;'>R$ {r['Valor_Abs']:,.2f} ({percent:.1f}%)</span>", unsafe_allow_html=True)

    else:
        st.info(f"Sem lançamentos em {meses_pt[m]}/{y}.")
else:
    st.info("Vazio.")

# --- RODAPÉ ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    .footer {position: relative; left: 0; bottom: 0; width: 100%; text-align: center; color: gray; font-family: 'Courier New', Courier, monospace; font-size: 14px; letter-spacing: 2px; opacity: 0.6;}
    </style>
    <div class="footer">made by JEFFERSON ELIAS</div>
    """,
    unsafe_allow_html=True
)