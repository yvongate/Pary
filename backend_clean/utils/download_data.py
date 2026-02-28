import requests
import os
from datetime import datetime

# Configuration des 8 championnats
LEAGUES = {
    "E0": {"name": "Premier League", "country": "England"},
    "E1": {"name": "Championship", "country": "England"},
    "D1": {"name": "Bundesliga", "country": "Germany"},
    "SP1": {"name": "La Liga", "country": "Spain"},
    "I1": {"name": "Serie A", "country": "Italy"},
    "F1": {"name": "Ligue 1", "country": "France"},
    "F2": {"name": "Ligue 2", "country": "France"},
    "P1": {"name": "Primeira Liga", "country": "Portugal"},
}

def get_current_season():
    """Saison actuelle (2025/26 = 2526)"""
    now = datetime.now()
    year_start = now.year if now.month >= 8 else now.year - 1
    year_end = year_start + 1
    return f"{str(year_start)[2:]}{str(year_end)[2:]}"

def download_file(url, filepath, desc):
    """Télécharge un fichier depuis une URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"[OK] {desc}: {len(response.content)} bytes")
        return filepath
    except Exception as e:
        print(f"[ERREUR] {desc}: {e}")
        return None

def download_fixtures(data_dir="data"):
    """Télécharge le fichier fixtures (matchs à venir)"""
    url = "https://www.football-data.co.uk/fixtures.csv"
    filepath = os.path.join(data_dir, "fixtures.csv")
    return download_file(url, filepath, "Fixtures")

def download_league(league_code, league_info, season, data_dir="data"):
    """Télécharge un fichier CSV de résultats pour une ligue"""
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"
    filepath = os.path.join(data_dir, f"{league_code}_{season}.csv")
    return download_file(url, filepath, league_info["name"])

def download_all():
    """Télécharge tous les fichiers nécessaires"""
    season = get_current_season()
    print(f"Telechargement des donnees saison {season}...\n")

    # 1. Fixtures (matchs à venir)
    fixtures_path = download_fixtures()

    # 2. Résultats par championnat
    downloaded = []
    for code, info in LEAGUES.items():
        path = download_league(code, info, season)
        if path:
            downloaded.append(path)

    print(f"\n{len(downloaded)}/8 championnats + fixtures telecharges")
    return fixtures_path, downloaded

if __name__ == "__main__":
    download_all()
