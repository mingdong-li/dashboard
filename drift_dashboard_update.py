import os
import streamlit as st
import plotly.graph_objects as go
import asyncio
import pandas as pd
import datetime
from data_fectch import fetch_rate_cur, fetch_rate_history

st.set_page_config(page_title="Drift Protocol Real-Time APY", layout="wide")
st.title("Drift Protocol Real-Time APY")

if "last_fetch_time" not in st.session_state:
    st.session_state["last_fetch_time"] = datetime.datetime.now()

TOKEN_OPTION = ["zBTC", "USDC", "SOL", "JLP", "wBTC", "jitoSOL"]
token_name = st.sidebar.selectbox(
    "Select Token",
    options=TOKEN_OPTION,
    key="realtime_token"
)
MAX_SAMPLES = 24*30 # save at most the previous 30 days of data, 24 samples per day
last_fetch_time = datetime.datetime.now()


def append_and_limit_csv(cur_d, cur_b, filename, max_samples=MAX_SAMPLES):
    # Remove duplicate 'date' column from cur_b if exists
    if 'date' in cur_b.columns:
        cur_b = cur_b.drop(columns=['date'])
    merged = pd.concat([cur_d.reset_index(drop=True), cur_b.reset_index(drop=True)], axis=1)
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, merged], ignore_index=True)
        if len(df) > max_samples:
            df = df.iloc[-max_samples:]
        df.to_csv(filename, index=False)
    else:
        merged.to_csv(filename, index=False)


# Only fetch and append if last sample is older than 60 mins or file doesn't exist
def should_fetch():
    if len(os.listdir('./data')) == 0:
        return True
    now = datetime.datetime.now()
    last_fetch_time = st.session_state["last_fetch_time"]
    diff = now - last_fetch_time
    
    if diff.total_seconds() > 10:
    # if diff.total_seconds() > 3600:
        st.session_state["last_fetch_time"] = now
        return True
    return False


# Auto-refresh
st_autorefresh = st.experimental_rerun if hasattr(st, "experimental_rerun") else None
st_autorefresh = st_autorefresh or (lambda: None)
st_autorefresh()
# st.experimental_set_query_params(refresh=pd.Timestamp.now().isoformat())
st.query_params = {"refresh": pd.Timestamp.now().isoformat()}



if should_fetch():
    for token_name in TOKEN_OPTION:
        # Fetch current rates of all underlying Assets
        cur_d, cur_b = asyncio.run(fetch_rate_cur(token_name))
        append_and_limit_csv(cur_d, cur_b, filename = "./data/realtime_samples_{token}.csv".format(token=token_name.lower()))


SAMPLE_FILE = "./data/realtime_samples_{token}.csv".format(token=token_name.lower())
# Load data for plotting, history data only load for plot
if os.path.exists(SAMPLE_FILE):
    # some bugs or unclear logic here
    df_saved = pd.read_csv(SAMPLE_FILE)
    df_deposit, df_borrow = fetch_rate_history(token_name, day_fetch=30)

    df_d_saved = df_saved[["date", "deposit_rate", "deposit_apy"]]
    df_b_saved = df_saved[["date", "borrow_rate", "borrow_apy"]]

    cur_d, cur_b = asyncio.run(fetch_rate_cur(token_name))
    df_deposit = pd.concat([df_deposit, df_d_saved], ignore_index=True)
    df_borrow = pd.concat([df_borrow, df_b_saved], ignore_index=True)
else:
    # this cannot be reached, but just in case
    raise FileNotFoundError(f"Sample file {SAMPLE_FILE} does not exist. Please fetch data first.")
    # cur_d, cur_b = asyncio.run(fetch_rate_cur(token_name))
    # df_cur = pd.concat([cur_d, cur_b], axis=1)
    # append_and_limit_csv(cur_d, cur_b)


col1, col2 = st.columns([3, 1])  
with col1:
    fig = go.Figure()
    # Plot Borrow APY (red)
    if "borrow_apy" in df_borrow.columns:
        fig.add_trace(
            go.Scatter(
                x=df_borrow["date"],
                y=df_borrow["borrow_apy"],
                name="Borrow APY",
                mode="lines+markers",
                line=dict(color="red"),
                marker=dict(symbol="diamond", size=6),
                hovertemplate="<b>Borrow APY: %{y:.4%}</b><br>%{x}<extra></extra>",
            ),
        )

        # fig.add_trace(
        #     go.Scatter(
        #         x=df_borrow["date"],
        #         y=df_borrow["borrow_rate"],
        #         name="Borrow Rate",
        #         mode="lines+markers",
        #         line=dict(color="pink"),
        #         marker=dict(symbol="diamond", size=6),
        #         hovertemplate="<b>Borrow Rate: %{y:.4%}</b><br>%{x}<extra></extra>",
        #     ),
        # )

    # Plot Deposit APY (green)
    if "deposit_apy" in df_deposit.columns:
        fig.add_trace(
            go.Scatter(
                x=df_deposit["date"],
                y=df_deposit["deposit_apy"],
                name="Deposit APY",
                mode="lines+markers",
                line=dict(color="green"),
                marker=dict(symbol="circle", size=6),
                hovertemplate="<b>Deposit APY: %{y:.4%}</b><br>%{x}<extra></extra>",
            ),
        )

        # fig.add_trace(
        #     go.Scatter(
        #         x=df_deposit["date"],
        #         y=df_deposit["deposit_rate"],
        #         name="Deposit Rate",
        #         mode="lines+markers",
        #         line=dict(color="teal"),
        #         marker=dict(symbol="diamond", size=6),
        #         hovertemplate="<b>Deposit Rate: %{y:.4%}</b><br>%{x}<extra></extra>",
        #     ),
        # )
        
    fig.update_layout(
        title=f"{token_name} Deposit & Borrow APY (History + previous 10hr)",
        xaxis_title="Date",
        yaxis_title="APY",
        hovermode="x unified",
        legend=dict(x=0, y=1.1, orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

  
with col2:
    st.subheader("Latest Data ({name})".format(name=token_name))

    # Show latest borrow APY if available
    if "borrow_apy" in df_borrow.columns:
        latest_borrow = df_borrow.iloc[-1]
        st.metric(
            "Latest Borrow APY",
            f"{latest_borrow['borrow_apy']:.4%}",
            help="Annual Percentage Yield for borrowing"
        )

    # Show latest deposit APY
    if "deposit_apy" in df_deposit.columns:
        latest_deposit = df_deposit.iloc[-1]
        st.metric(
            "Latest Deposit APY",
            f"{latest_deposit['deposit_apy']:.4%}",
            help="Annual Percentage Yield for deposits"
        )
