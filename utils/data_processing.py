import pandas as pd
import numpy as np
from typing import Dict, List, Optional

def process_race_data(laps_data: List[Dict]) -> pd.DataFrame:
    """Processa i dati dei giri"""
    df = pd.DataFrame(laps_data)
    
    if df.empty:
        return df
    
    # Converti timestamp
    if 'date_start' in df.columns:
        df['date_start'] = pd.to_datetime(df['date_start'])
    
    # Calcola statistiche aggiuntive
    if 'lap_duration' in df.columns:
        df['lap_duration'] = pd.to_numeric(df['lap_duration'], errors='coerce')
    
    return df

def calculate_statistics(df: pd.DataFrame, driver_number: int) -> Dict:
    """Calcola statistiche per un pilota"""
    driver_laps = df[df['driver_number'] == driver_number]
    
    if driver_laps.empty or 'lap_duration' not in driver_laps.columns:
        return {}
    
    lap_times = driver_laps['lap_duration'].dropna()
    
    if lap_times.empty:
        return {}
    
    stats = {
        'total_laps': len(driver_laps),
        'fastest_lap': lap_times.min(),
        'average_lap': lap_times.mean(),
        'median_lap': lap_times.median(),
        'consistency': lap_times.std(),
        'slowest_lap': lap_times.max()
    }
    
    return stats

def calculate_gap_to_leader(positions_df: pd.DataFrame) -> pd.DataFrame:
    """Calcola il gap rispetto al leader"""
    if positions_df.empty:
        return positions_df
    
    # Ordina per timestamp
    positions_df = positions_df.sort_values('date')
    
    # Trova il leader per ogni timestamp
    leader_positions = positions_df[positions_df['position'] == 1][['date', 'driver_number']]
    
    return positions_df

def aggregate_team_results(laps_df: pd.DataFrame, drivers_df: pd.DataFrame) -> pd.DataFrame:
    """Aggrega risultati per team"""
    # Merge con informazioni piloti per ottenere team
    if 'team_name' not in drivers_df.columns:
        return pd.DataFrame()
    
    merged = laps_df.merge(
        drivers_df[['driver_number', 'team_name']], 
        on='driver_number', 
        how='left'
    )
    
    # Aggrega per team
    team_stats = merged.groupby('team_name').agg({
        'lap_duration': ['mean', 'min', 'count'],
        'driver_number': 'nunique'
    }).reset_index()
    
    return team_stats

def detect_pit_stops(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Rileva pit stop dai dati giri"""
    # Pit stop rilevati da improvvisi aumenti di lap time
    if 'lap_duration' not in laps_df.columns:
        return pd.DataFrame()
    
    laps_df = laps_df.sort_values(['driver_number', 'lap_number'])
    
    # Calcola differenza rispetto al giro precedente
    laps_df['duration_diff'] = laps_df.groupby('driver_number')['lap_duration'].diff()
    
    # Considera pit stop se il tempo aumenta di più di 20 secondi
    pit_stops = laps_df[laps_df['duration_diff'] > 20].copy()
    
    return pit_stops[['driver_number', 'lap_number', 'lap_duration', 'duration_diff']]

def calculate_tire_degradation(laps_df: pd.DataFrame, stint_data: List[Dict]) -> pd.DataFrame:
    """Calcola degrado gomme per stint"""
    if not stint_data:
        return pd.DataFrame()
    
    stint_df = pd.DataFrame(stint_data)
    
    # Per ogni stint, calcola trend tempi giri
    results = []
    
    for _, stint in stint_df.iterrows():
        driver_stint_laps = laps_df[
            (laps_df['driver_number'] == stint['driver_number']) &
            (laps_df['lap_number'] >= stint['lap_start']) &
            (laps_df['lap_number'] <= stint['lap_end'])
        ]
        
        if not driver_stint_laps.empty and 'lap_duration' in driver_stint_laps.columns:
            lap_times = driver_stint_laps['lap_duration'].dropna()
            
            if len(lap_times) > 2:
                # Calcola degrado (differenza tra ultimi 3 e primi 3 giri)
                start_avg = lap_times.head(3).mean()
                end_avg = lap_times.tail(3).mean()
                degradation = end_avg - start_avg
                
                results.append({
                    'driver_number': stint['driver_number'],
                    'compound': stint.get('compound', 'Unknown'),
                    'stint_length': stint['lap_end'] - stint['lap_start'] + 1,
                    'degradation': degradation,
                    'start_time': start_avg,
                    'end_time': end_avg
                })
    
    return pd.DataFrame(results)
