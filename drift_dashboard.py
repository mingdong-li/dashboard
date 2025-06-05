import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import asyncio

from data_fectch import fetch_rate_cur, fetch_rate_history

# python -m venv ../drift-v2-streamlit/venv
# source ../drift-v2-streamlit/venv/bin/activate


if __name__ == "__main__":
    # Set page config
    st.set_page_config(page_title="Drift Protocol Rate History", layout="wide")

    # Title
    st.title("Drift Protocol Rate History Dashboard")

    # Sidebar controls
    st.sidebar.header("Settings")
    token_name = st.sidebar.selectbox(
        "Select Token",
        options=["zBTC","USDC", "SOL","JLP","wBTC","jitoSOL"])
    days_to_fetch = st.sidebar.slider("Days to Fetch", 1, 30, 30)

    df_deposit, df_borrow = fetch_rate_history(token_name)
    cur_d, cur_b = asyncio.run(fetch_rate_cur(token_name))
    df_deposit = pd.concat([df_deposit, cur_d], ignore_index=True)
    df_borrow = pd.concat([df_borrow, cur_b], ignore_index=True)



    if df_borrow is not None and df_deposit is not None:
        # Create two columns
        col1, col2 = st.columns([3, 1])  
        with col1:
            st.subheader("Deposit & Borrow APY (Time Zone: UTC+8)")

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