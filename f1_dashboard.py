import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from utils.api_client import OpenF1Client
from utils.data_processing import process_race_data, calculate_statistics

# Configurazione pagina
st.set_page_config(
    page_title="F1 Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .stSelectbox, .stMultiSelect {
        color: #38bdf8;
    }
    h1, h2, h3 {
        color: #38bdf8;
    }
    .metric-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

# Inizializza client API
@st.cache_resource
def init_client():
    return OpenF1Client()

client = init_client()

# Sidebar - Filtri
st.sidebar.title("🏎️ F1 Dashboard")
st.sidebar.markdown("---")

# Selezione anno
year = st.sidebar.selectbox(
    "📅 Seleziona Anno",
    options=[2026, 2025, 2024, 2023],
    index=0
)

# Ottieni lista gare per l'anno selezionato
@st.cache_data(ttl=3600)
def get_races(year):
    return client.get_meetings(year=year)

races = get_races(year)

if races:
    race_names = [race['meeting_name'] for race in races]
    selected_race = st.sidebar.selectbox(
        "🏁 Seleziona Gara",
        options=race_names
    )
    
    # Trova il meeting_key della gara selezionata
    race_key = next((r['meeting_key'] for r in races if r['meeting_name'] == selected_race), None)
    
    # Selezione sessione
    session_type = st.sidebar.selectbox(
        "⏱️ Tipo Sessione",
        options=["Race", "Qualifying", "Sprint", "Practice 1", "Practice 2", "Practice 3"]
    )
    
    # Opzioni visualizzazione
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Visualizzazioni")
    show_standings = st.sidebar.checkbox("Classifiche", value=True)
    show_laptimes = st.sidebar.checkbox("Tempi sul Giro", value=True)
    show_positions = st.sidebar.checkbox("Evoluzione Posizioni", value=False)
    show_telemetry = st.sidebar.checkbox("Telemetria", value=False)
    
    # Header principale
    st.title(f"🏎️ F1 Dashboard - {year}")
    st.markdown(f"### {selected_race}")
    
    # Carica dati della sessione
    @st.cache_data(ttl=3600)
    def load_session_data(race_key, session):
        session_data = client.get_session(race_key, session)
        if session_data:
            session_key = session_data[0]['session_key']
            
            # Carica dati multipli
            laps = client.get_laps(session_key=session_key)
            positions = client.get_position(session_key=session_key)
            drivers = client.get_drivers(session_key=session_key)
            
            return {
                'session_key': session_key,
                'laps': laps,
                'positions': positions,
                'drivers': drivers
            }
        return None
    
    with st.spinner(f"Caricamento dati {session_type}..."):
        data = load_session_data(race_key, session_type)
    
    if data and data['laps']:
        # Converti in DataFrame
        df_laps = pd.DataFrame(data['laps'])
        df_drivers = pd.DataFrame(data['drivers'])
        
        # Metriche principali
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏁 Giri Totali", len(df_laps['lap_number'].unique()))
        
        with col2:
            st.metric("👥 Piloti", len(df_drivers))
        
        with col3:
            if 'lap_duration' in df_laps.columns:
                fastest_lap = df_laps[df_laps['lap_duration'].notna()]['lap_duration'].min()
                st.metric("⚡ Giro Veloce", f"{fastest_lap:.3f}s")
        
        with col4:
            total_laps = len(df_laps)
            st.metric("📊 Giri Registrati", total_laps)
        
        st.markdown("---")
        
        # Classifiche
        if show_standings:
            st.subheader("🏆 Classifiche Mondiali")
            
            @st.cache_data(ttl=3600)
            def get_standings(year):
                # Simulazione classifiche (OpenF1 non ha endpoint standings diretto)
                # In produzione, useresti un'altra API o calcoli dai risultati
                drivers_standings = [
                    {"position": 1, "driver": "Max Verstappen", "team": "Red Bull Racing", "points": 575},
                    {"position": 2, "driver": "Lewis Hamilton", "team": "Mercedes", "points": 523},
                    {"position": 3, "driver": "Charles Leclerc", "team": "Ferrari", "points": 456},
                    {"position": 4, "driver": "Lando Norris", "team": "McLaren", "points": 398},
                    {"position": 5, "driver": "Carlos Sainz", "team": "Ferrari", "points": 367},
                ]
                return pd.DataFrame(drivers_standings)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 👤 Classifica Piloti")
                standings_df = get_standings(year)
                st.dataframe(
                    standings_df,
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                fig = px.bar(
                    standings_df.head(10),
                    x='points',
                    y='driver',
                    orientation='h',
                    title='Top 10 Piloti',
                    color='points',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#f1f5f9',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Tempi sul giro
        if show_laptimes and 'lap_duration' in df_laps.columns:
            st.markdown("---")
            st.subheader("⏱️ Analisi Tempi sul Giro")
            
            # Filtra per pilota
            available_drivers = df_laps['driver_number'].unique()
            selected_drivers = st.multiselect(
                "Seleziona Piloti da Confrontare",
                options=sorted(available_drivers),
                default=sorted(available_drivers)[:3] if len(available_drivers) >= 3 else sorted(available_drivers)
            )
            
            if selected_drivers:
                df_filtered = df_laps[df_laps['driver_number'].isin(selected_drivers)]
                df_filtered = df_filtered[df_filtered['lap_duration'].notna()]
                
                # Grafico tempi sul giro
                fig = go.Figure()
                
                for driver in selected_drivers:
                    driver_data = df_filtered[df_filtered['driver_number'] == driver]
                    fig.add_trace(go.Scatter(
                        x=driver_data['lap_number'],
                        y=driver_data['lap_duration'],
                        mode='lines+markers',
                        name=f"Pilota #{driver}",
                        line=dict(width=2),
                        marker=dict(size=6)
                    ))
                
                fig.update_layout(
                    title='Tempi sul Giro per Pilota',
                    xaxis_title='Numero Giro',
                    yaxis_title='Tempo (secondi)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#f1f5f9',
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiche per pilota
                st.markdown("#### 📈 Statistiche Dettagliate")
                stats_cols = st.columns(len(selected_drivers))
                
                for idx, driver in enumerate(selected_drivers):
                    driver_laps = df_filtered[df_filtered['driver_number'] == driver]['lap_duration']
                    with stats_cols[idx]:
                        st.markdown(f"**Pilota #{driver}**")
                        st.metric("Giro Medio", f"{driver_laps.mean():.3f}s")
                        st.metric("Giro Veloce", f"{driver_laps.min():.3f}s")
                        st.metric("Consistenza", f"{driver_laps.std():.3f}s")
        
        # Evoluzione posizioni
        if show_positions and data['positions']:
            st.markdown("---")
            st.subheader("📍 Evoluzione Posizioni in Gara")
            
            df_positions = pd.DataFrame(data['positions'])
            
            if not df_positions.empty and 'position' in df_positions.columns:
                # Seleziona piloti da visualizzare
                pos_drivers = st.multiselect(
                    "Seleziona Piloti",
                    options=sorted(df_positions['driver_number'].unique()),
                    default=sorted(df_positions['driver_number'].unique())[:5]
                )
                
                if pos_drivers:
                    df_pos_filtered = df_positions[df_positions['driver_number'].isin(pos_drivers)]
                    
                    fig = go.Figure()
                    
                    for driver in pos_drivers:
                        driver_pos = df_pos_filtered[df_pos_filtered['driver_number'] == driver]
                        fig.add_trace(go.Scatter(
                            x=driver_pos['date'],
                            y=driver_pos['position'],
                            mode='lines',
                            name=f"Pilota #{driver}",
                            line=dict(width=3)
                        ))
                    
                    fig.update_layout(
                        title='Evoluzione Posizioni durante la Gara',
                        xaxis_title='Tempo',
                        yaxis_title='Posizione',
                        yaxis=dict(autorange='reversed'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#f1f5f9',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # Telemetria
        if show_telemetry:
            st.markdown("---")
            st.subheader("🔧 Dati Telemetrici")
            st.info("💡 La telemetria dettagliata (velocità, marce, RPM) richiede dati da fonti aggiuntive come FastF1")
            
            # Qui potresti integrare FastF1 per telemetria dettagliata
            st.code("""
# Esempio integrazione FastF1 per telemetria
import fastf1

session = fastf1.get_session(2024, 'Monza', 'R')
session.load()
laps = session.laps
telemetry = laps.pick_driver('VER').get_telemetry()
            """)
        
        # Dati raw
        with st.expander("📋 Visualizza Dati Raw"):
            st.dataframe(df_laps.head(100), use_container_width=True)
    
    else:
        st.warning("⚠️ Nessun dato disponibile per questa sessione")
        st.info("💡 I dati potrebbero non essere ancora disponibili per gare future o sessioni non ancora iniziate")

else:
    st.error("❌ Impossibile caricare le gare per l'anno selezionato")

# Footer
st.markdown("---")
st.markdown("""
    

        
🏎️ Dashboard F1 - Powered by OpenF1 API | Creato con Streamlit


        
Dati storici dal 2023 • Real-time disponibile


    

""", unsafe_allow_html=True)
