import requests
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN")
BASE_URL = os.getenv("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4")

HEADERS = {
    "X-Auth-Token": API_TOKEN
}

# Mapping des codes championnats football-data.co.uk vers football-data.org
LEAGUE_MAPPING = {
    "E0": "PL",      # Premier League
    "E1": "ELC",     # Championship
    "D1": "BL1",     # Bundesliga
    "SP1": "PD",     # La Liga (Primera Division)
    "I1": "SA",      # Serie A
    "F1": "FL1",     # Ligue 1
    "F2": "FL2",     # Ligue 2
    "P1": "PPL",     # Primeira Liga
}

# Mapping inverse
REVERSE_LEAGUE_MAPPING = {v: k for k, v in LEAGUE_MAPPING.items()}

# Noms des championnats
LEAGUE_NAMES = {
    "PL": "Premier League",
    "ELC": "Championship",
    "BL1": "Bundesliga",
    "PD": "La Liga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "FL2": "Ligue 2",
    "PPL": "Primeira Liga",
}

def get_competition_matches(competition_code: str, date_from: Optional[str] = None, date_to: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère les matchs d'une compétition depuis football-data.org

    Args:
        competition_code: Code de la compétition (PL, ELC, BL1, etc.)
        date_from: Date de début (format YYYY-MM-DD)
        date_to: Date de fin (format YYYY-MM-DD)
        status: Filtrer par statut (SCHEDULED, LIVE, FINISHED, etc.)
    """
    if not API_TOKEN:
        print("[ERREUR] FOOTBALL_DATA_API_TOKEN non défini")
        return []

    url = f"{BASE_URL}/competitions/{competition_code}/matches"

    params = {}
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to
    if status:
        params["status"] = status

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("matches", [])
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            print(f"[ERREUR] Accès refusé pour {competition_code} - Le tier gratuit ne couvre peut-être pas cette compétition")
        elif response.status_code == 429:
            print(f"[ERREUR] Rate limit atteint (10 requêtes/minute)")
        else:
            print(f"[ERREUR] football-data.org {competition_code}: {e}")
        return []
    except Exception as e:
        print(f"[ERREUR] football-data.org {competition_code}: {e}")
        return []

def get_all_fixtures(days_future: int = 14, league_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère les matchs à venir pour tous les championnats ou un seul

    Args:
        days_future: Nombre de jours à venir à récupérer
        league_code: Code du championnat (E0, E1, etc.) ou None pour tous
    """
    today = datetime.now()
    date_from = today.strftime("%Y-%m-%d")
    date_to = (today + timedelta(days=days_future)).strftime("%Y-%m-%d")

    all_matches = []

    # Déterminer quels championnats récupérer
    if league_code:
        if league_code in LEAGUE_MAPPING:
            comp_codes = [LEAGUE_MAPPING[league_code]]
        else:
            print(f"[AVERTISSEMENT] Code {league_code} non reconnu")
            return []
    else:
        comp_codes = list(LEAGUE_MAPPING.values())

    for comp_code in comp_codes:
        matches = get_competition_matches(
            competition_code=comp_code,
            date_from=date_from,
            date_to=date_to,
            status="SCHEDULED"
        )

        # Convertir au format de notre API
        for match in matches:
            formatted = format_match_from_api(match)
            if formatted:
                all_matches.append(formatted)

    return all_matches

def format_match_from_api(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convertit un match de l'API football-data.org vers notre format"""
    try:
        competition_code = match.get("competition", {}).get("code")
        if not competition_code:
            return None

        # Récupérer notre code interne
        internal_code = REVERSE_LEAGUE_MAPPING.get(competition_code, competition_code)

        # Date et heure
        utc_date = match.get("utcDate", "")
        if utc_date:
            dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")
        else:
            date_str = None
            time_str = None

        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})

        return {
            "id": str(match.get("id")),
            "league_code": internal_code,
            "league": LEAGUE_NAMES.get(competition_code, match.get("competition", {}).get("name", "Unknown")),
            "date": date_str,
            "time": time_str,
            "home_team": home_team.get("name", "Unknown"),
            "away_team": away_team.get("name", "Unknown"),
            "status": "SCHEDULED",
            "home_score": None,
            "away_score": None,
        }
    except Exception as e:
        print(f"[ERREUR] Formatage match: {e}")
        return None

def get_standings_from_api(league_code: str) -> Optional[Dict[str, Any]]:
    """Récupère le classement depuis football-data.org"""
    if league_code not in LEAGUE_MAPPING:
        print(f"[ERREUR] Code {league_code} non reconnu")
        return None

    comp_code = LEAGUE_MAPPING[league_code]
    url = f"{BASE_URL}/competitions/{comp_code}/standings"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        standings = []
        for standing in data.get("standings", []):
            if standing.get("type") == "TOTAL":
                for table in standing.get("table", []):
                    team = table.get("team", {})
                    standings.append({
                        "position": table.get("position"),
                        "team": team.get("name"),
                        "played": table.get("playedGames"),
                        "wins": table.get("won"),
                        "draws": table.get("draw"),
                        "losses": table.get("lost"),
                        "gf": table.get("goalsFor"),
                        "ga": table.get("goalsAgainst"),
                        "gd": table.get("goalDifference"),
                        "points": table.get("points"),
                    })

        return {
            "league": data.get("competition", {}).get("name"),
            "season": str(data.get("season", {}).get("startDate", "")[:4]),
            "standings": standings
        }
    except Exception as e:
        print(f"[ERREUR] Standings {league_code}: {e}")
        return None

if __name__ == "__main__":
    # Test
    print("Test de récupération des fixtures...")
    fixtures = get_all_fixtures(days_future=7)
    print(f"{len(fixtures)} matchs trouvés")
    for f in fixtures[:3]:
        print(f"  {f['date']} {f['time']} - {f['home_team']} vs {f['away_team']} ({f['league']})")
