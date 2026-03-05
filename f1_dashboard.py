import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏎️ F1 Data Hub - 2023-2026 (OpenF1 + Historical)")

@st.cache_data(ttl=300)
def fetch_df(endpoint, **params):
    try:
        url = f"https://api.openf1.org/v1/{endpoint}"
        resp = requests.get(url, params=params)
        return pd.DataFrame(resp.json()) if resp.ok else pd.DataFrame()
    except:
        return pd.DataFrame()

# Sidebar year selector (2023-2026)
year = st.sidebar.selectbox("Year", [2026, 2025, 2024, 2023], index=0)
st.sidebar.info("Data: OpenF1 API [18 endpoints][web:11]")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Sessions", "Standings", "Laps/Pits", "Telemetry", "Pit Stops"])

with tab1:
    sessions = fetch_df("sessions", year=year)
    if not sessions.empty:
        st.subheader(f"Sessions {year}")
        st.dataframe(sessions[['session_name', 'date_start', 'circuit_short_name']].head(20))
        st.bar_chart(sessions['session_name'].value_counts())

with tab2:
    standings = fetch_df("drivers_standings", session_key="latest")  # Current season
    st.subheader("Driver Standings")
    if not standings.empty:
        st.bar_chart(standings.set_index('position')['points_current'])
        st.dataframe(standings)

with tab3:
    laps = fetch_df("laps", year=year, limit=1000)
    if not laps.empty:
        st.subheader(f"Top Laps {year}")
        st.line_chart(laps, x='lap_number', y='lap_duration')
        st.dataframe(laps.head())

with tab4:
    # Car telemetry sample (throttle, speed)
    car_data = fetch_df("car_data", year=year, limit=500)
    if not car_data.empty:
        st.subheader(f"Telemetry Sample {year}")
        st.line_chart(car_data, x='date', y=['speed', 'throttle'])
        st.dataframe(car_data.head())

with tab5:
    pits = fetch_df("pit", year=year, limit=200)
    if not pits.empty:
        st.subheader(f"Pit Stops {year}")
        st.scatter_chart(pits, x='lap_number', y='stop_duration', color='driver_number')
        st.dataframe(pits)
