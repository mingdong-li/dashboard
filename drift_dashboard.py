import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time


# python -m venv venv
# source venv/bin/activate


def fetch_rate_history(token_name='SOL'):
    rates =  {'deposit': [], 'borrow': []}  # 示例数据
    for x in ['deposit', 'borrow']:
        print(f"Fetching {x} rate history...")

        url = "https://data.api.drift.trade/stats/{name}/rateHistory/{mode}".format(name=token_name, mode=x) 

        response = requests.get(url)        
        if response.status_code == 200:
            data = response.json()
            # df = pd.DataFrame(data)

            for entry in data['rates']:
                # 计算每日复利的 APY
                
                apy = (1 + float(entry[1]) / 365) ** 365 - 1

                format = '%Y-%m-%d %H:%M:%S'
                # value为传入的值为时间戳(整形)，如：1332888820
                value = time.localtime(entry[0])
                ## 经过localtime转换后变成
                ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
                # 最后再经过strftime函数转换为正常日期格式。
                dt = time.strftime(format, value)

                rates[x].append({
                    "date": dt,
                    x: float(entry[1]),
                    x+"_apy": apy  # 有些数据可能没有 borrowRate
                })

            print(f"{x.capitalize()} rate history fetched successfully.")

                
        else:
            print("Error:", response.status_code)

    deposit_rates = pd.DataFrame(rates['deposit'])
    borrow_rates = pd.DataFrame(rates['borrow'])

    # res = pd.concat([deposit_rates, borrow_rates], axis=1, sort=False)
    # res = pd.merge(deposit_rates, borrow_rates, on='date', how='outer')
    # res.dropna(axis=0,subset = ["deposit_apy", "borrow_apy"], how='any')
    return deposit_rates, borrow_rates


# Set page config
st.set_page_config(page_title="Drift Protocol Rate History", layout="wide")

# Title
st.title("Drift Protocol Rate History Dashboard")

# Sidebar controls
st.sidebar.header("Settings")
token_name = st.sidebar.selectbox(
    "Select Token",
    options=["zBTC","USDC", "SOL","JLP","wBTC","jitoSOL"])
days_to_fetch = st.sidebar.slider("Days to Fetch", 1, 90, 30)


df_deposit, df_borrow = fetch_rate_history(token_name)

if df_borrow is not None and df_deposit is not None:
    # Create two columns
    col1, col2 = st.columns([3, 1])  
    with col1:
        st.subheader("Deposit & Borrow APY")

        fig = make_subplots()

        # Borrow APY
        fig.add_trace(
            go.Scatter(
                x=df_borrow["date"],
                y=df_borrow["borrow_apy"],
                name="Borrow APY",
                mode="lines+markers",
                line=dict(color="red"),
                marker=dict(symbol="diamond", size=6),
                hovertemplate="<b>%{y:.4%}</b><br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ),
        )

        # Deposit APY
        fig.add_trace(
            go.Scatter(
                x=df_deposit["date"],
                y=df_deposit["deposit_apy"],
                name="Deposit APY",
                mode="lines+markers",
                line=dict(color="green"),
                marker=dict(symbol="circle", size=6),
                hovertemplate="<b>%{y:.4%}</b><br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ),
        )

        fig.update_layout(
        title=f"{token_name} Deposit & Borrow APY",
        xaxis_title="Date",
        yaxis_title="APY",
        legend_title_text="APY Type",
        hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Latest Data ({name})".format(name=token_name))


        # Show latest borrow APY
        latest_borrow = df_borrow.iloc[-1]
        st.metric(
            "Latest Borrow APY",
            f"{latest_borrow['borrow_apy']:.4%}",
            help="Annual Percentage Yield for borrowing"
        )

        # Show latest deposit APY
        latest_deposit = df_deposit.iloc[-1]
        st.metric(
            "Latest Deposit APY",
            f"{latest_deposit['deposit_apy']:.4%}",
            help="Annual Percentage Yield for deposits"
        )



        # Show number of data points
        st.metric(
            "Data Points",
            len(df_deposit),
            help="Number of data points in current view"
        )

        # Raw data expander
        with st.expander("Show Raw Data"):
            st.dataframe(df_borrow[['date', 'borrow_apy']].sort_values('date', ascending=False))
            st.dataframe(df_deposit[['date', 'deposit_apy']].sort_values('date', ascending=False))
else:
    st.warning("No data available. Please check your connection or try again later.")



# Add some info
st.sidebar.markdown("""
**How to Use:**
- Hover over the chart to see values at specific points
- Select market index and time range in the sidebar
- Latest values are shown on the right
""")