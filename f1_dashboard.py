import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🚀 Live F1 Data Hub - OpenF1")

@st.cache_data(ttl=60)
def fetch_df(endpoint, **params):
    try:
        url = f"https://api.openf1.org/v1/{endpoint}"
        resp = requests.get(url, params=params)
        return pd.DataFrame(resp.json())
    except:
        return pd.DataFrame()

tab1, tab2, tab3 = st.tabs(["Standings", "Positions", "Laps"])

with tab1:
    df = fetch_df("drivers_standings", session_key="latest")
    if not df.empty:
        st.bar_chart(df.set_index("position")["points_current"])
        st.dataframe(df)

with tab2:
    df = fetch_df("position", session_key="latest")
    if not df.empty:
        st.line_chart(df.set_index("date")["position"])
        st.dataframe(df.head(200))

with tab3:
    df = fetch_df("laps", session_key="latest", limit=500)
    if not df.empty:
        fig = px.scatter(df, x="lap_duration", y="driver_number")
        st.plotly_chart(fig)
        st.dataframe(df)
