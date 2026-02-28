import tls_client
from typing import Optional, Dict, Any
import time
from urllib.parse import quote

BASE_URL = "https://www.sofascore.com/api/v1"

# Créer une session tls_client qui simule Chrome
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def search_team(team_name: str) -> Optional[Dict[str, Any]]:
    """Recherche une équipe par nom sur SofaScore"""
    try:
        url = f"{BASE_URL}/search/all?q={quote(team_name)}"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code != 200:
            print(f"[ERREUR] Recherche équipe '{team_name}': Status {response.status_code}")
            return None

        data = response.json()

        # Récupérer la première équipe trouvée
        teams = data.get("results", [])
        for result in teams:
            if result.get("type") == "team":
                entity = result.get("entity", {})
                return {
                    "id": entity.get("id"),
                    "name": entity.get("name"),
                    "slug": entity.get("slug"),
                }

        return None
    except Exception as e:
        print(f"[ERREUR] Recherche équipe '{team_name}': {e}")
        return None

def search_match(home_team: str, away_team: str, date: str) -> Optional[int]:
    """
    Recherche un match sur SofaScore à partir des noms d'équipes et de la date

    Args:
        home_team: Nom de l'équipe à domicile
        away_team: Nom de l'équipe à l'extérieur
        date: Date du match (format YYYY-MM-DD)

    Returns:
        ID du match SofaScore ou None
    """
    try:
        # Chercher l'équipe à domicile
        home_info = search_team(home_team)
        if not home_info:
            print(f"[ERREUR] Équipe '{home_team}' non trouvée")
            return None

        team_id = home_info["id"]

        # Récupérer les événements de l'équipe
        url = f"{BASE_URL}/team/{team_id}/events/last/0"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code != 200:
            print(f"[ERREUR] Récupération événements team {team_id}: Status {response.status_code}")
            return None

        data = response.json()

        events = data.get("events", [])

        # Rechercher le match correspondant
        for event in events:
            home_team_event = event.get("homeTeam", {}).get("name", "")
            away_team_event = event.get("awayTeam", {}).get("name", "")

            # Vérifier si c'est le bon match (recherche plus flexible)
            home_match = (
                home_team.lower() in home_team_event.lower() or
                home_team_event.lower() in home_team.lower()
            )
            away_match = (
                away_team.lower() in away_team_event.lower() or
                away_team_event.lower() in away_team.lower()
            )

            if home_match and away_match:
                # Vérifier la date (avec marge de ±1 jour)
                start_timestamp = event.get("startTimestamp")
                if start_timestamp:
                    from datetime import datetime, timedelta
                    event_date = datetime.fromtimestamp(start_timestamp)
                    target_date = datetime.strptime(date, "%Y-%m-%d")

                    # Accepter le match si la date est proche (±1 jour)
                    if abs((event_date.date() - target_date.date()).days) <= 1:
                        return event.get("id")

        print(f"[ERREUR] Match {home_team} vs {away_team} ({date}) non trouvé")
        return None

    except Exception as e:
        print(f"[ERREUR] Recherche match: {e}")
        return None

def get_match_lineups(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère les compositions d'équipes d'un match

    Args:
        match_id: ID du match SofaScore

    Returns:
        Dictionnaire avec les lineups ou None en cas d'erreur
    """
    try:
        url = f"{BASE_URL}/event/{match_id}/lineups"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code == 404:
            print(f"[ERREUR] Match {match_id} non trouvé ou lineups non disponibles")
            return None
        elif response.status_code != 200:
            print(f"[ERREUR] Récupération lineups {match_id}: Status {response.status_code}")
            return None

        data = response.json()

        if not data:
            print(f"[ERREUR] Pas de lineups disponibles pour le match {match_id}")
            return None

        # Extraire les informations importantes
        home_lineup = data.get("home", {})
        away_lineup = data.get("away", {})

        result = {
            "home": {
                "team": home_lineup.get("team", {}).get("name", "Unknown"),
                "formation": home_lineup.get("formation", "Unknown"),
                "players": []
            },
            "away": {
                "team": away_lineup.get("team", {}).get("name", "Unknown"),
                "formation": away_lineup.get("formation", "Unknown"),
                "players": []
            }
        }

        # Extraire les joueurs de l'équipe à domicile
        for player_data in home_lineup.get("players", []):
            player = player_data.get("player", {})
            result["home"]["players"].append({
                "name": player.get("name", "Unknown"),
                "position": player.get("position", "Unknown"),
                "shirt_number": player.get("jerseyNumber"),
                "substitute": player_data.get("substitute", False),
            })

        # Extraire les joueurs de l'équipe à l'extérieur
        for player_data in away_lineup.get("players", []):
            player = player_data.get("player", {})
            result["away"]["players"].append({
                "name": player.get("name", "Unknown"),
                "position": player.get("position", "Unknown"),
                "shirt_number": player.get("jerseyNumber"),
                "substitute": player_data.get("substitute", False),
            })

        return result

    except Exception as e:
        print(f"[ERREUR] Récupération lineups {match_id}: {e}")
        return None

def get_match_preview(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère l'avant-match (preview) d'un match depuis SofaScore

    Args:
        match_id: ID du match SofaScore

    Returns:
        Dictionnaire avec les infos d'avant-match ou None
    """
    try:
        url = f"{BASE_URL}/event/{match_id}/preview"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code == 404:
            print(f"[ERREUR] Preview non disponible pour le match {match_id}")
            return None
        elif response.status_code != 200:
            print(f"[ERREUR] Récupération preview {match_id}: Status {response.status_code}")
            return None

        data = response.json()
        return data

    except Exception as e:
        print(f"[ERREUR] Récupération preview {match_id}: {e}")
        return None


def get_missing_players(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère les joueurs absents (blessures, suspensions) pour un match

    Args:
        match_id: ID du match SofaScore

    Returns:
        Dictionnaire avec les joueurs absents ou None
    """
    try:
        url = f"{BASE_URL}/event/{match_id}/missing-players"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code == 404:
            print(f"[INFO] Pas de joueurs absents déclarés pour le match {match_id}")
            return {"home": [], "away": []}
        elif response.status_code != 200:
            print(f"[ERREUR] Récupération absences {match_id}: Status {response.status_code}")
            return None

        data = response.json()

        # Formater les données
        result = {
            "home": [],
            "away": []
        }

        # Joueurs domicile absents
        for player_data in data.get("home", {}).get("missingPlayers", []):
            player = player_data.get("player", {})
            result["home"].append({
                "name": player.get("name", "Unknown"),
                "position": player.get("position", "Unknown"),
                "reason": player_data.get("reason", "Unknown"),
                "expected_return": player_data.get("expectedReturn")
            })

        # Joueurs extérieur absents
        for player_data in data.get("away", {}).get("missingPlayers", []):
            player = player_data.get("player", {})
            result["away"].append({
                "name": player.get("name", "Unknown"),
                "position": player.get("position", "Unknown"),
                "reason": player_data.get("reason", "Unknown"),
                "expected_return": player_data.get("expectedReturn")
            })

        return result

    except Exception as e:
        print(f"[ERREUR] Récupération absences {match_id}: {e}")
        return None


def get_head_to_head(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère l'historique des confrontations directes

    Args:
        match_id: ID du match SofaScore

    Returns:
        Dictionnaire avec les matchs H2H ou None
    """
    try:
        url = f"{BASE_URL}/event/{match_id}/h2h/events"
        response = session.get(url, headers=HEADERS, timeout_seconds=10)

        if response.status_code == 404:
            print(f"[INFO] Pas d'historique H2H pour le match {match_id}")
            return {"events": []}
        elif response.status_code != 200:
            print(f"[ERREUR] Récupération H2H {match_id}: Status {response.status_code}")
            return None

        data = response.json()
        return data

    except Exception as e:
        print(f"[ERREUR] Récupération H2H {match_id}: {e}")
        return None


def get_match_context(home_team: str, away_team: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Récupère toutes les informations contextuelles d'un match :
    - Preview / Avant-match
    - Joueurs absents (blessures/suspensions)
    - Historique des confrontations

    Args:
        home_team: Nom de l'équipe à domicile
        away_team: Nom de l'équipe à l'extérieur
        date: Date du match (format YYYY-MM-DD)

    Returns:
        Dictionnaire complet avec tout le contexte
    """
    match_id = search_match(home_team, away_team, date)
    if not match_id:
        return None

    # Récupérer toutes les données
    preview = get_match_preview(match_id)
    missing = get_missing_players(match_id)
    h2h = get_head_to_head(match_id)

    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "date": date,
        "preview": preview,
        "missing_players": missing,
        "head_to_head": h2h
    }


def get_lineups_by_teams(home_team: str, away_team: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les lineups à partir des noms d'équipes et de la date

    Args:
        home_team: Nom de l'équipe à domicile
        away_team: Nom de l'équipe à l'extérieur
        date: Date du match (format YYYY-MM-DD)

    Returns:
        Dictionnaire avec les lineups ou None
    """
    match_id = search_match(home_team, away_team, date)
    if not match_id:
        return None

    return get_match_lineups(match_id)

if __name__ == "__main__":
    # Test
    print("Test de récupération des lineups...")
    lineups = get_lineups_by_teams("Arsenal", "Liverpool", "2024-02-04")
    if lineups:
        print(f"\nDomicile: {lineups['home']['team']} ({lineups['home']['formation']})")
        print(f"Extérieur: {lineups['away']['team']} ({lineups['away']['formation']})")
        print(f"Joueurs domicile: {len(lineups['home']['players'])}")
        print(f"Joueurs extérieur: {len(lineups['away']['players'])}")
    else:
        print("Aucune lineup trouvée")
