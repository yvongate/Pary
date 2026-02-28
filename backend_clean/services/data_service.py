"""
Service de gestion des données (CSV de football-data.co.uk)
Téléchargement et chargement des fixtures et résultats
"""
import os
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings


class DataService:
    """Service de gestion des données CSV"""

    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.fixtures_csv = settings.FIXTURES_CSV
        self.base_url = settings.FOOTBALL_DATA_CSV_URL

    def download_fixtures(self) -> Optional[str]:
        """
        Télécharge le fichier fixtures.csv

        Returns:
            Chemin du fichier ou None si erreur
        """
        try:
            url = "https://www.football-data.co.uk/fixtures.csv"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            os.makedirs(self.data_dir, exist_ok=True)

            with open(self.fixtures_csv, 'wb') as f:
                f.write(response.content)

            print(f"[OK] Fixtures téléchargé: {len(response.content)} bytes")
            return self.fixtures_csv

        except Exception as e:
            print(f"[ERREUR] Téléchargement fixtures: {e}")
            return None

    def download_league_results(self, league_code: str, season: str) -> Optional[str]:
        """
        Télécharge les résultats d'une ligue

        Args:
            league_code: Code de la ligue (E0, SP1, etc.)
            season: Saison (ex: "2526")

        Returns:
            Chemin du fichier ou None
        """
        try:
            url = f"https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            os.makedirs(self.data_dir, exist_ok=True)
            filepath = os.path.join(self.data_dir, f"{league_code}_{season}.csv")

            with open(filepath, 'wb') as f:
                f.write(response.content)

            league_name = settings.LEAGUES.get(league_code, {}).get('name', league_code)
            print(f"[OK] {league_name}: {len(response.content)} bytes")
            return filepath

        except Exception as e:
            print(f"[ERREUR] Téléchargement {league_code}: {e}")
            return None

    def download_all_leagues(self, season: Optional[str] = None) -> List[str]:
        """
        Télécharge tous les fichiers CSV des ligues

        Args:
            season: Saison (ex: "2526"), auto-détecté si None

        Returns:
            Liste des chemins des fichiers téléchargés
        """
        if season is None:
            season = self.get_current_season()

        downloaded = []
        for league_code in settings.LEAGUES.keys():
            filepath = self.download_league_results(league_code, season)
            if filepath:
                downloaded.append(filepath)

        return downloaded

    def load_fixtures(self) -> Optional[pd.DataFrame]:
        """
        Charge le fichier fixtures.csv

        Returns:
            DataFrame ou None
        """
        if not os.path.exists(self.fixtures_csv):
            print(f"[ATTENTION] {self.fixtures_csv} introuvable")
            return None

        try:
            df = pd.read_csv(self.fixtures_csv)
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            return df
        except Exception as e:
            print(f"[ERREUR] Lecture fixtures.csv: {e}")
            return None

    def load_league_results(self, league_code: str, season: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Charge les résultats d'une ligue

        Args:
            league_code: Code de la ligue
            season: Saison (auto-détecté si None)

        Returns:
            DataFrame ou None
        """
        if season is None:
            season = self.get_current_season()

        filepath = os.path.join(self.data_dir, f"{league_code}_{season}.csv")

        if not os.path.exists(filepath):
            print(f"[ATTENTION] {filepath} introuvable")
            return None

        try:
            df = pd.read_csv(filepath, encoding='latin1')
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            return df
        except Exception as e:
            print(f"[ERREUR] Lecture {filepath}: {e}")
            return None

    def get_upcoming_matches(self, hours_ahead: int = 2) -> List[Dict]:
        """
        Récupère les matchs à venir dans X heures

        Args:
            hours_ahead: Nombre d'heures à l'avance

        Returns:
            Liste des matchs
        """
        df = self.load_fixtures()
        if df is None:
            return []

        from datetime import timedelta
        all_matches = []
        now = datetime.now()
        cutoff_time = now + timedelta(hours=hours_ahead)

        for _, row in df.iterrows():
            try:
                if pd.isna(row['Date']):
                    continue

                match_date = row['Date']
                if pd.notna(row.get('Time')):
                    time_str = str(row['Time'])
                    hour, minute = time_str.split(':')
                    match_date = match_date.replace(hour=int(hour), minute=int(minute))

                if now <= match_date <= cutoff_time:
                    league_code = row['Div']
                    home_team = row['HomeTeam']
                    away_team = row['AwayTeam']

                    match_id = f"{league_code}_{match_date.strftime('%Y%m%d')}_{home_team.replace(' ', '')}{away_team.replace(' ', '')}"

                    all_matches.append({
                        'match_id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'league_code': league_code,
                        'match_date': match_date
                    })
            except Exception as e:
                continue

        return all_matches

    @staticmethod
    def get_current_season() -> str:
        """
        Retourne la saison actuelle (ex: "2526" pour 2025/26)

        Returns:
            Saison au format AABB
        """
        now = datetime.now()
        year_start = now.year if now.month >= 8 else now.year - 1
        year_end = year_start + 1
        return f"{str(year_start)[2:]}{str(year_end)[2:]}"


# Instance globale
_data_instance = None

def get_data_service() -> DataService:
    """Retourne l'instance singleton du service de données"""
    global _data_instance
    if _data_instance is None:
        _data_instance = DataService()
    return _data_instance
