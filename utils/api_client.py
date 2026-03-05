import requests
from typing import Optional, List, Dict
import time

class OpenF1Client:
    """Client per interagire con l'API OpenF1"""
    
    BASE_URL = "https://api.openf1.org/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'F1-Dashboard/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
        """Esegue una richiesta all'API con rate limiting"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                time.sleep(1)
                return self._make_request(endpoint, params)
            else:
                print(f"Errore API: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Errore di connessione: {e}")
            return None
    
    def get_meetings(self, year: Optional[int] = None) -> Optional[List[Dict]]:
        """Ottiene la lista dei meeting (gare) per un anno"""
        params = {'year': year} if year else {}
        return self._make_request('meetings', params)
    
    def get_session(self, meeting_key: int, session_name: str) -> Optional[List[Dict]]:
        """Ottiene informazioni su una sessione specifica"""
        params = {
            'meeting_key': meeting_key,
            'session_name': session_name
        }
        return self._make_request('sessions', params)
    
    def get_drivers(self, session_key: Optional[int] = None) -> Optional[List[Dict]]:
        """Ottiene lista piloti"""
        params = {'session_key': session_key} if session_key else {}
        return self._make_request('drivers', params)
    
    def get_laps(self, session_key: int, driver_number: Optional[int] = None) -> Optional[List[Dict]]:
        """Ottiene dati dei giri"""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return self._make_request('laps', params)
    
    def get_position(self, session_key: int, driver_number: Optional[int] = None) -> Optional[List[Dict]]:
        """Ottiene posizioni in gara"""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return self._make_request('position', params)
    
    def get_stints(self, session_key: int) -> Optional[List[Dict]]:
        """Ottiene stint (strategie gomme)"""
        params = {'session_key': session_key}
        return self._make_request('stints', params)
    
    def get_pit_stops(self, session_key: int) -> Optional[List[Dict]]:
        """Ottiene pit stop"""
        params = {'session_key': session_key}
        return self._make_request('pit', params)
    
    def get_car_data(self, session_key: int, driver_number: int) -> Optional[List[Dict]]:
        """Ottiene telemetria base (velocità)"""
        params = {
            'session_key': session_key,
            'driver_number': driver_number
        }
        return self._make_request('car_data', params)
    
    def get_race_control(self, session_key: int) -> Optional[List[Dict]]:
        """Ottiene messaggi race control (safety car, bandiere, etc)"""
        params = {'session_key': session_key}
        return self._make_request('race_control', params)
