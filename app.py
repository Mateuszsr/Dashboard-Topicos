import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PERSONALIZADO
# ============================================================
st.markdown("""
<style>

[data-testid="metric-container"] {
    background-color: #f9fafc;
    border: 1px solid #e6e9ef;
    padding: 15px;
    border-radius: 12px;
}

[data-testid="metric-container"] label {
    color: #6b7280 !important;
}

[data-testid="metric-container"] div {
    color: #111827 !important;
    font-weight: 700;
}

h1 {
    color: #1f4e79;
    border-bottom: 3px solid #1f4e79;
    padding-bottom: 8px;
}

h2 { color: #1f2937; }
h3 { color: #374151; }

</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÃO DE CARREGAMENTO
# ============================================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("base_dashboard.csv")

        # Datas
        for col in ["data_pedido", "data_cadastro"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Numéricos
        for col in ["quantidade", "preco_parcial", "total_pedido", "preco", "estoque"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Missing
        df.fillna(0, inplace=True)
        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# ============================================================
# KPIs
# ============================================================
def calcular_kpis(df):
    total_receita = df["preco_parcial"].sum()
    total_pedidos = df["id_pedido"].nunique()
    clientes = df["id_cliente"].nunique()
    quantidade = df["quantidade"].sum()
    ticket = total_receita / total_pedidos if total_pedidos else 0

    return total_receita, total_pedidos, clientes, quantidade, ticket

# ============================================================
# APP PRINCIPAL
# ============================================================
def main():

    st.title("📊 Dashboard Analítico de Vendas")
    st.caption("Autor: Mateus Ramos | Projeto de Análise de Dados")

    df = load_data()

    if df is None:
        st.stop()

# ============================================================
# SIDEBAR FILTROS
# ============================================================

    st.sidebar.header("🔎 Filtros")

    if "data_pedido" in df.columns:
        data = st.sidebar.date_input(
            "Período",
            [df["data_pedido"].min(), df["data_pedido"].max()]
        )

        if len(data) == 2:
            df = df[(df["data_pedido"] >= pd.to_datetime(data[0])) &
                    (df["data_pedido"] <= pd.to_datetime(data[1]))]

    produto = st.sidebar.selectbox("Produto", ["Todos"] + sorted(df["nome_produto"].unique()))
    if produto != "Todos":
        df = df[df["nome_produto"] == produto]

    categoria = st.sidebar.selectbox("Categoria", ["Todas"] + sorted(df["categoria"].unique()))
    if categoria != "Todas":
        df = df[df["categoria"] == categoria]

    estado = st.sidebar.selectbox("Estado", ["Todos"] + sorted(df["uf"].unique()))
    if estado != "Todos":
        df = df[df["uf"] == estado]

    sexo = st.sidebar.selectbox("Sexo", ["Todos"] + sorted(df["sexo"].unique()))
    if sexo != "Todos":
        df = df[df["sexo"] == sexo]

    st.sidebar.markdown("---")
    st.sidebar.info(f"Registros filtrados: {len(df):,}")

# ============================================================
# KPIs VISUAIS
# ============================================================

    st.subheader("Indicadores Principais")

    total_receita, total_pedidos, clientes, quantidade, ticket = calcular_kpis(df)

    def moeda(x):
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Receita Total", moeda(total_receita))
    c2.metric("Pedidos", f"{total_pedidos:,}")
    c3.metric("Clientes", f"{clientes:,}")
    c4.metric("Qtd Vendida", f"{int(quantidade):,}")
    c5.metric("Ticket Médio", moeda(ticket))

# ============================================================
# GRÁFICOS
# ============================================================

    st.divider()
    st.subheader("Visualizações")

    # Receita ao longo do tempo
    receita_data = df.groupby(df["data_pedido"].dt.date)["preco_parcial"].sum().reset_index()

    fig = px.line(
        receita_data,
        x="data_pedido",
        y="preco_parcial",
        title="Receita ao Longo do Tempo",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

    # Receita por categoria
    cat = df.groupby("categoria")["preco_parcial"].sum().reset_index()

    fig2 = px.bar(cat, x="categoria", y="preco_parcial", title="Receita por Categoria")
    st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)

    # Top receita
    top = df.groupby("nome_produto")["preco_parcial"].sum().sort_values(ascending=False).head(10).reset_index()

    fig3 = px.bar(top, x="preco_parcial", y="nome_produto", orientation="h",
                  title="Top 10 Produtos por Receita")
    col1.plotly_chart(fig3, use_container_width=True)

    # Top quantidade
    qtd = df.groupby("nome_produto")["quantidade"].sum().sort_values(ascending=False).head(10).reset_index()

    fig4 = px.bar(qtd, x="quantidade", y="nome_produto", orientation="h",
                  title="Top 10 Produtos por Quantidade")
    col2.plotly_chart(fig4, use_container_width=True)

    # Receita por estado
    estado_df = df.groupby("uf")["preco_parcial"].sum().reset_index()

    fig5 = px.bar(estado_df, x="uf", y="preco_parcial", title="Receita por Estado")
    st.plotly_chart(fig5, use_container_width=True)

    # Receita por sexo
    sexo_df = df.groupby("sexo")["preco_parcial"].sum().reset_index()

    fig6 = px.pie(sexo_df, names="sexo", values="preco_parcial", title="Receita por Sexo", hole=0.4)
    st.plotly_chart(fig6, use_container_width=True)

    # Distribuição pedidos
    pedidos = df.groupby("id_pedido")["preco_parcial"].sum().reset_index()

    fig7 = px.histogram(pedidos, x="preco_parcial", nbins=40, title="Distribuição de Valores de Pedido")
    st.plotly_chart(fig7, use_container_width=True)

# ============================================================
# INSIGHTS AUTOMÁTICOS
# ============================================================

    st.divider()
    st.subheader("Insights Automáticos")

    col1, col2, col3 = st.columns(3)

    # Produto mais vendido
    produto_top = df.groupby("nome_produto")["quantidade"].sum().idxmax()
    col1.success(f"Produto mais vendido:\n**{produto_top}**")

    # Categoria mais lucrativa
    cat_top = df.groupby("categoria")["preco_parcial"].sum().idxmax()
    col2.info(f"Categoria mais lucrativa:\n**{cat_top}**")

    # Estado líder
    estado_top = df.groupby("uf")["preco_parcial"].sum().idxmax()
    col3.warning(f"Estado com maior receita:\n**{estado_top}**")

# ============================================================
# RODAPÉ
# ============================================================

    st.markdown("---")
    st.caption("Dashboard desenvolvido para análise de vendas — Dados simulados para fins acadêmicos")

# ============================================================
if __name__ == "__main__":
    main()
