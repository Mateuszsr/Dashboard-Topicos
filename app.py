import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS STYLING
# ============================================================
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
        border-bottom: 3px solid #1f77b4;
    }
    h2 {
        color: #2c3e50;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    h3 {
        color: #34495e;
        margin-top: 20px;
    }
    .divider {
        margin: 30px 0;
        border-top: 2px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# DATA LOADING AND PREPARATION
# ============================================================
@st.cache_data
def load_data(file_path):
    """
    Load CSV data with automatic date parsing and data type conversion.
    Handles missing values and validates schema.
    """
    try:
        # Load CSV
        df = pd.read_csv(file_path)
        
        # Detect and parse date columns
        date_columns = ['data_pedido', 'data_cadastro']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric fields
        numeric_columns = ['quantidade', 'preco_parcial', 'total_pedido', 'preco', 'estoque']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Handle missing values
        df = df.fillna({
            'quantidade': 0,
            'preco_parcial': 0,
            'total_pedido': 0,
            'preco': 0,
            'estoque': 0,
            'nome_produto': 'Unknown',
            'categoria': 'Unknown',
            'uf': 'Unknown',
            'sexo': 'Unknown',
            'faixa_etaria': 'Unknown'
        })
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# ============================================================
# KPI CALCULATION FUNCTIONS
# ============================================================
def calculate_kpis(df):
    """
    Calculate key performance indicators from the dataset.
    """
    total_revenue = df['preco_parcial'].sum()
    total_orders = df['id_pedido'].nunique()
    unique_customers = df['id_cliente'].nunique()
    total_quantity = df['quantidade'].sum()
    avg_ticket = total_revenue / total_orders if total_orders > 0 else 0
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'total_quantity': total_quantity,
        'avg_ticket': avg_ticket
    }

# ============================================================
# ADVANCED INSIGHTS FUNCTIONS
# ============================================================
def calculate_insights(df):
    """
    Compute advanced business insights automatically.
    """
    insights = {}
    
    # Best selling product (by quantity)
    product_quantity = df.groupby('nome_produto')['quantidade'].sum().sort_values(ascending=False)
    insights['best_selling_product'] = product_quantity.index[0] if len(product_quantity) > 0 else "N/A"
    insights['best_selling_quantity'] = product_quantity.iloc[0] if len(product_quantity) > 0 else 0
    
    # Most profitable category
    category_revenue = df.groupby('categoria')['preco_parcial'].sum().sort_values(ascending=False)
    insights['most_profitable_category'] = category_revenue.index[0] if len(category_revenue) > 0 else "N/A"
    insights['category_revenue'] = category_revenue.iloc[0] if len(category_revenue) > 0 else 0
    
    # Highest revenue state
    state_revenue = df.groupby('uf')['preco_parcial'].sum().sort_values(ascending=False)
    insights['highest_revenue_state'] = state_revenue.index[0] if len(state_revenue) > 0 else "N/A"
    insights['state_revenue'] = state_revenue.iloc[0] if len(state_revenue) > 0 else 0
    
    # Highest spending age group
    age_revenue = df.groupby('faixa_etaria')['preco_parcial'].sum().sort_values(ascending=False)
    insights['highest_spending_age'] = age_revenue.index[0] if len(age_revenue) > 0 else "N/A"
    insights['age_revenue'] = age_revenue.iloc[0] if len(age_revenue) > 0 else 0
    
    # Top customer by total spend
    customer_spend = df.groupby(['id_cliente', 'nome_completo'])['preco_parcial'].sum().sort_values(ascending=False)
    if len(customer_spend) > 0:
        top_customer_id, top_customer_name = customer_spend.index[0]
        insights['top_customer_name'] = top_customer_name
        insights['top_customer_spend'] = customer_spend.iloc[0]
    else:
        insights['top_customer_name'] = "N/A"
        insights['top_customer_spend'] = 0
    
    return insights

# ============================================================
# MAIN APPLICATION
# ============================================================
def main():
    # Title
    st.title("📊 Interactive Analytics Dashboard")
    st.markdown("**Complete data analytics platform with real-time insights**")
    
    # Load data
    df = load_data('/home/ubuntu/upload/base_dashboard.csv')
    
    if df is None:
        st.error("Failed to load data. Please check the file path.")
        return
    
    # Display detected columns
    with st.expander("📋 Dataset Schema Information"):
        st.write(f"**Total Rows:** {len(df):,}")
        st.write(f"**Total Columns:** {len(df.columns)}")
        st.write("**Detected Columns:**")
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Data Type': df.dtypes.values,
            'Non-Null Count': df.count().values,
            'Null Count': df.isnull().sum().values
        })
        st.dataframe(col_info, use_container_width=True)
    
    # ============================================================
    # SIDEBAR FILTERS
    # ============================================================
    st.sidebar.header("🔍 Interactive Filters")
    
    # Date range filter
    if 'data_pedido' in df.columns and df['data_pedido'].notna().any():
        min_date = df['data_pedido'].min()
        max_date = df['data_pedido'].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            df = df[(df['data_pedido'] >= pd.to_datetime(date_range[0])) & 
                    (df['data_pedido'] <= pd.to_datetime(date_range[1]))]
    
    # Product name filter
    if 'nome_produto' in df.columns:
        products = ['All'] + sorted(df['nome_produto'].unique().tolist())
        selected_product = st.sidebar.selectbox("Product Name", products)
        if selected_product != 'All':
            df = df[df['nome_produto'] == selected_product]
    
    # Category filter
    if 'categoria' in df.columns:
        categories = ['All'] + sorted(df['categoria'].unique().tolist())
        selected_category = st.sidebar.selectbox("Category", categories)
        if selected_category != 'All':
            df = df[df['categoria'] == selected_category]
    
    # State filter
    if 'uf' in df.columns:
        states = ['All'] + sorted(df['uf'].unique().tolist())
        selected_state = st.sidebar.selectbox("State (UF)", states)
        if selected_state != 'All':
            df = df[df['uf'] == selected_state]
    
    # Gender filter
    if 'sexo' in df.columns:
        genders = ['All'] + sorted(df['sexo'].unique().tolist())
        selected_gender = st.sidebar.selectbox("Gender", genders)
        if selected_gender != 'All':
            df = df[df['sexo'] == selected_gender]
    
    # Minimum revenue threshold
    min_revenue = st.sidebar.number_input(
        "Minimum Revenue Threshold",
        min_value=0.0,
        value=0.0,
        step=100.0
    )
    df = df[df['preco_parcial'] >= min_revenue]
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"**Filtered Records:** {len(df):,}")
    
    # Check if data is empty after filtering
    if len(df) == 0:
        st.warning("⚠️ No data available with the current filters. Please adjust your selection.")
        return
    
    # ============================================================
    # KPI METRICS SECTION
    # ============================================================
    st.markdown("## 📈 Key Performance Indicators")
    
    kpis = calculate_kpis(df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"R$ {kpis['total_revenue']:,.2f}"
        )
    
    with col2:
        st.metric(
            label="🛒 Total Orders",
            value=f"{kpis['total_orders']:,}"
        )
    
    with col3:
        st.metric(
            label="👥 Unique Customers",
            value=f"{kpis['unique_customers']:,}"
        )
    
    with col4:
        st.metric(
            label="📦 Total Quantity Sold",
            value=f"{int(kpis['total_quantity']):,}"
        )
    
    with col5:
        st.metric(
            label="🎯 Average Ticket",
            value=f"R$ {kpis['avg_ticket']:,.2f}"
        )
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ============================================================
    # VISUAL ANALYTICS SECTION
    # ============================================================
    st.markdown("## 📊 Visual Analytics")
    
    # Revenue over time
    if 'data_pedido' in df.columns and df['data_pedido'].notna().any():
        st.markdown("### 📅 Revenue Over Time")
        revenue_time = df.groupby(df['data_pedido'].dt.date)['preco_parcial'].sum().reset_index()
        revenue_time.columns = ['Date', 'Revenue']
        
        fig_time = px.line(
            revenue_time,
            x='Date',
            y='Revenue',
            title='Daily Revenue Trend',
            labels={'Revenue': 'Revenue (R$)', 'Date': 'Date'},
            markers=True
        )
        fig_time.update_layout(
            hovermode='x unified',
            height=400,
            title_font_size=16
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    # Revenue by category
    st.markdown("### 🏷️ Revenue by Category")
    category_revenue = df.groupby('categoria')['preco_parcial'].sum().sort_values(ascending=False).reset_index()
    category_revenue.columns = ['Category', 'Revenue']
    
    fig_category = px.bar(
        category_revenue,
        x='Category',
        y='Revenue',
        title='Revenue Distribution by Category',
        labels={'Revenue': 'Revenue (R$)', 'Category': 'Category'},
        color='Revenue',
        color_continuous_scale='Blues'
    )
    fig_category.update_layout(height=400, title_font_size=16)
    st.plotly_chart(fig_category, use_container_width=True)
    
    # Two columns for top products
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Top 10 Products by Revenue")
        top_products_revenue = df.groupby('nome_produto')['preco_parcial'].sum().sort_values(ascending=False).head(10).reset_index()
        top_products_revenue.columns = ['Product', 'Revenue']
        
        fig_top_revenue = px.bar(
            top_products_revenue,
            y='Product',
            x='Revenue',
            orientation='h',
            title='Top 10 Products by Revenue',
            labels={'Revenue': 'Revenue (R$)', 'Product': 'Product'},
            color='Revenue',
            color_continuous_scale='Greens'
        )
        fig_top_revenue.update_layout(height=500, title_font_size=14)
        st.plotly_chart(fig_top_revenue, use_container_width=True)
    
    with col2:
        st.markdown("### 📦 Top 10 Products by Quantity")
        top_products_quantity = df.groupby('nome_produto')['quantidade'].sum().sort_values(ascending=False).head(10).reset_index()
        top_products_quantity.columns = ['Product', 'Quantity']
        
        fig_top_quantity = px.bar(
            top_products_quantity,
            y='Product',
            x='Quantity',
            orientation='h',
            title='Top 10 Products by Quantity Sold',
            labels={'Quantity': 'Quantity Sold', 'Product': 'Product'},
            color='Quantity',
            color_continuous_scale='Oranges'
        )
        fig_top_quantity.update_layout(height=500, title_font_size=14)
        st.plotly_chart(fig_top_quantity, use_container_width=True)
    
    # Revenue by state and gender
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗺️ Revenue by State")
        state_revenue = df.groupby('uf')['preco_parcial'].sum().sort_values(ascending=False).reset_index()
        state_revenue.columns = ['State', 'Revenue']
        
        fig_state = px.bar(
            state_revenue,
            x='State',
            y='Revenue',
            title='Revenue Distribution by State',
            labels={'Revenue': 'Revenue (R$)', 'State': 'State'},
            color='Revenue',
            color_continuous_scale='Purples'
        )
        fig_state.update_layout(height=400, title_font_size=14)
        st.plotly_chart(fig_state, use_container_width=True)
    
    with col2:
        st.markdown("### 👫 Revenue by Gender")
        gender_revenue = df.groupby('sexo')['preco_parcial'].sum().reset_index()
        gender_revenue.columns = ['Gender', 'Revenue']
        
        fig_gender = px.pie(
            gender_revenue,
            names='Gender',
            values='Revenue',
            title='Revenue Distribution by Gender',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_gender.update_layout(height=400, title_font_size=14)
        st.plotly_chart(fig_gender, use_container_width=True)
    
    # Distribution of order value
    st.markdown("### 📊 Distribution of Order Value")
    
    # Calculate order totals
    order_totals = df.groupby('id_pedido')['preco_parcial'].sum().reset_index()
    order_totals.columns = ['Order ID', 'Order Value']
    
    fig_dist = px.histogram(
        order_totals,
        x='Order Value',
        nbins=50,
        title='Distribution of Order Values',
        labels={'Order Value': 'Order Value (R$)', 'count': 'Frequency'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_dist.update_layout(
        height=400,
        title_font_size=16,
        showlegend=False
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # ============================================================
    # ADVANCED INSIGHTS SECTION
    # ============================================================
    st.markdown("## 🎯 Advanced Business Insights")
    
    insights = calculate_insights(df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏆 Best Selling Product")
        st.info(f"**{insights['best_selling_product']}**")
        st.write(f"Total Quantity Sold: **{int(insights['best_selling_quantity']):,}** units")
        
        st.markdown("### 💎 Most Profitable Category")
        st.success(f"**{insights['most_profitable_category']}**")
        st.write(f"Total Revenue: **R$ {insights['category_revenue']:,.2f}**")
    
    with col2:
        st.markdown("### 🗺️ Highest Revenue State")
        st.warning(f"**{insights['highest_revenue_state']}**")
        st.write(f"Total Revenue: **R$ {insights['state_revenue']:,.2f}**")
        
        st.markdown("### 👥 Highest Spending Age Group")
        st.info(f"**{insights['highest_spending_age']}**")
        st.write(f"Total Revenue: **R$ {insights['age_revenue']:,.2f}**")
    
    with col3:
        st.markdown("### 🌟 Top Customer by Total Spend")
        st.success(f"**{insights['top_customer_name']}**")
        st.write(f"Total Spend: **R$ {insights['top_customer_spend']:,.2f}**")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("**Dashboard created with Streamlit, Plotly, and Pandas** | Data updated in real-time")

# ============================================================
# RUN APPLICATION
# ============================================================
if __name__ == "__main__":
    main()
