import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analytics App", layout="wide")

# =========================
# 🎨 UI
# =========================
st.markdown("""
<h1 style='text-align: center; font-size: 50px; color: #4CAF50;'>
📊 Interactive Data Analytics Dashboard
</h1>
<p style='text-align: center; font-size: 18px; color: gray;'>
Upload your dataset and get real business insights 🚀
</p>
""", unsafe_allow_html=True)

# Remove footer
st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔥 Load Data
# =========================
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    if len(df) > 100000:
        df = df.sample(100000, random_state=42)
        st.warning("⚡ Using sampled data for faster performance")

    return df


uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx"])

if uploaded_file is not None:

    df = load_data(uploaded_file)

    # =========================
    # 🔍 FILTERS
    # =========================
    st.sidebar.header("🔍 Filters")

    if "Country" in df.columns:
        selected_country = st.sidebar.selectbox(
            "🌍 Select Country",
            ["All"] + list(df["Country"].dropna().unique())
        )
        if selected_country != "All":
            df = df[df["Country"] == selected_country]

    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

        min_date = df["InvoiceDate"].min()
        max_date = df["InvoiceDate"].max()

        date_range = st.sidebar.date_input(
            "📅 Select Date Range",
            [min_date, max_date]
        )

        if len(date_range) == 2:
            df = df[
                (df["InvoiceDate"] >= pd.to_datetime(date_range[0])) &
                (df["InvoiceDate"] <= pd.to_datetime(date_range[1]))
            ]

    # =========================
    # 🧭 TABS
    # =========================
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "👥 Customer Insights", "📈 Business Insights"])

    # =========================
    # 📊 TAB 1: DASHBOARD
    # =========================
    with tab1:

        df_kpi = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

        total_revenue = (df_kpi["Quantity"] * df_kpi["UnitPrice"]).sum()
        customers = df_kpi["CustomerID"].dropna().nunique() if "CustomerID" in df_kpi else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Revenue", f"{total_revenue:.2f}")
        col2.metric("📦 Orders", df.shape[0])
        col3.metric("👥 Customers", customers)

        st.markdown("---")

        # 📈 SALES TREND
        if "InvoiceDate" in df.columns:
            df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

            monthly_sales = df.groupby("Month")["Quantity"].sum().reset_index()

            fig = px.line(monthly_sales, x="Month", y="Quantity",
                          markers=True, title="📈 Monthly Sales Trend")

            st.plotly_chart(fig, use_container_width=True)

        # 💰 REVENUE GROWTH (ADDED)
        if {"Quantity", "UnitPrice"}.issubset(df.columns):

            df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

            revenue_trend = df.groupby("Month")["TotalPrice"].sum().reset_index()
            revenue_trend["Growth %"] = revenue_trend["TotalPrice"].pct_change() * 100

            st.subheader("💰 Revenue Growth")

            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
                x=revenue_trend["Month"],
                y=revenue_trend["TotalPrice"],
                mode='lines',
                line=dict(color='#7DB7FF', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(125,183,255,0.15)',
                
                customdata=revenue_trend["Growth %"],
                hovertemplate=
                "<b>Month:</b> %{x}<br>" +
                "<b>Revenue:</b> %{y}<br>" +
                "<b>Growth:</b> %{customdata:.2f}%<extra></extra>"
            ))

            fig2.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                showlegend=False
            )

            st.plotly_chart(fig2, use_container_width=True)
            
            
            
            
            
            
            
            
        
            
            
            

        # 🏆 TOP PRODUCTS
        if "Description" in df.columns:
            top_products = df.groupby("Description")["Quantity"].sum().sort_values(ascending=False).head(10).reset_index()

            fig = px.bar(top_products, x="Description", y="Quantity",
                         title="🏆 Top Products")

            st.plotly_chart(fig, use_container_width=True)

    # =========================
    # 👥 TAB 2: CUSTOMER INSIGHTS
    # =========================
    with tab2:

        if {"CustomerID", "InvoiceNo", "Quantity", "UnitPrice"}.issubset(df.columns):

            df_clean = df.dropna(subset=["CustomerID"])
            df_clean = df_clean[(df_clean["Quantity"] > 0) & (df_clean["UnitPrice"] > 0)]
            df_clean["TotalPrice"] = df_clean["Quantity"] * df_clean["UnitPrice"]

            customer_rev = df_clean.groupby("CustomerID")["TotalPrice"].sum().sort_values(ascending=False)
            cum_perc = customer_rev.cumsum() / customer_rev.sum()

            fig = go.Figure()
            fig.add_trace(go.Scatter(y=cum_perc, mode="lines"))
            fig.add_hline(y=0.8, line_dash="dash")

            st.plotly_chart(fig, use_container_width=True)

            top_n = (cum_perc <= 0.8).sum()
            total_cust = len(customer_rev)

            st.markdown(f"""
            💡 Top {top_n} customers (~{(top_n/total_cust)*100:.1f}%) generate 80% revenue
            """)

            customer_orders = df_clean.groupby("CustomerID")["InvoiceNo"].nunique()

            new_customers = (customer_orders == 1).sum()
            returning_customers = (customer_orders > 1).sum()

            cust_df = pd.DataFrame({
                "Type": ["New", "Returning"],
                "Count": [new_customers, returning_customers]
            })

            fig = px.pie(cust_df, names="Type", values="Count", hole=0.6,
                         title="👥 Customer Distribution")

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("Customer data not available")

    #=========================
    # 📈 TAB 3: BUSINESS INSIGHTS
    # =========================
    with tab3:

        if {"CustomerID", "InvoiceNo", "Quantity", "UnitPrice"}.issubset(df.columns):

            df_clean = df.dropna(subset=["CustomerID"])
            df_clean = df_clean[(df_clean["Quantity"] > 0) & (df_clean["UnitPrice"] > 0)]
            df_clean["TotalPrice"] = df_clean["Quantity"] * df_clean["UnitPrice"]

            # AOV
            total_revenue = df_clean["TotalPrice"].sum()
            total_orders = df_clean["InvoiceNo"].nunique()
            aov = total_revenue / total_orders if total_orders else 0

            st.metric(" Average Order Value (AOV)", f"{aov:.2f}")

            # Insights
            with st.expander(" View Key Insights"):
                if returning_customers > new_customers:
                    st.success(" Strong repeat customer base.")
                else:
                    st.warning(" Retention needs improvement.")

                if aov > 100:
                    st.success(" Customers spend well per order.")
                else:
                    st.warning(" Improve AOV using upselling.")

            # Decisions
            st.subheader(" Business Recommendations")

            with st.expander("📈 View Actionable Strategies"):
                st.info(" Focus on top 20% customers for maximum revenue impact.")

                if returning_customers > new_customers:
                    st.success(" Invest in loyalty programs.")
                else:
                    st.warning(" Improve retention strategies.")

                if aov > 100:
                    st.success(" Promote premium products.")
                else:
                    st.warning(" Use upselling strategies.")

                st.info(" Optimize marketing campaigns.")
                st.info(" Promote top-performing products.")

            # Download
            st.subheader(" Export Data")

            csv = df_clean.to_csv(index=False).encode('utf-8')

            st.download_button(
                label=" Download Processed Data",
                data=csv,
                file_name="processed_data.csv",
                mime="text/csv"
            )

        else:
            st.warning("Upload proper dataset for insights")
            
            
            