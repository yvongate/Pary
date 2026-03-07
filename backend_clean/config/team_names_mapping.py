"""
Mapping des noms d'équipes pour Google scraping
Convertit les noms des fixtures CSV en noms reconnus par Google Knowledge Graph
"""

# Mapping complet des équipes par ligue
TEAM_NAME_MAPPING = {
    # Bundesliga (D1) - Allemagne
    "Bayern Munich": "Bayern Munich",
    "RB Leipzig": "RB Leipzig",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "Werder Bremen": "Werder Bremen",
    "Freiburg": "SC Freiburg",
    "Augsburg": "FC Augsburg",
    "Heidenheim": "FC Heidenheim",
    "Wolfsburg": "VfL Wolfsburg",
    "Leverkusen": "Bayer Leverkusen",
    "Hoffenheim": "TSG Hoffenheim",
    "Union Berlin": "Union Berlin",
    "Stuttgart": "VfB Stuttgart",
    "St Pauli": "FC St. Pauli",
    "Dortmund": "Borussia Dortmund",
    "Mainz": "Mainz 05",
    "FC Koln": "FC Cologne",  # Crucial: Google utilise "FC Cologne" ou "Köln"
    "M'gladbach": "Borussia Monchengladbach",
    "Hamburg": "Hamburger SV",

    # Ligue 1 (F1) - France
    "Rennes": "Stade Rennais",
    "Marseille": "Olympique de Marseille",
    "Lens": "RC Lens",
    "Lyon": "Olympique Lyonnais",
    "Monaco": "AS Monaco",
    "Le Havre": "Le Havre AC",
    "Nice": "OGC Nice",
    "Toulouse": "Toulouse FC",
    "Brest": "Stade Brestois",
    "Lille": "Lille OSC",
    "Angers": "Angers SCO",
    "Paris FC": "Paris FC",
    "Auxerre": "AJ Auxerre",
    "Lorient": "FC Lorient",
    "Metz": "FC Metz",
    "Strasbourg": "RC Strasbourg",
    "Nantes": "FC Nantes",
    "Paris SG": "Paris Saint-Germain",

    # Premier League (E0) - Angleterre
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds": "Leeds United",
    "Liverpool": "Liverpool",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Southampton": "Southampton",
    "Tottenham": "Tottenham",
    "West Ham": "West Ham",
    "Wolves": "Wolverhampton",
    "Sunderland": "Sunderland",

    # La Liga (SP1) - Espagne
    "Alaves": "Alaves",
    "Athletic Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atletico Madrid",
    "Barcelona": "Barcelona",
    "Celta Vigo": "Celta Vigo",
    "Espanyol": "Espanyol",
    "Getafe": "Getafe",
    "Girona": "Girona",
    "Las Palmas": "Las Palmas",
    "Leganes": "Leganes",
    "Mallorca": "Mallorca",
    "Osasuna": "Osasuna",
    "Rayo Vallecano": "Rayo Vallecano",
    "Real Betis": "Real Betis",
    "Real Madrid": "Real Madrid",
    "Real Sociedad": "Real Sociedad",
    "Sevilla": "Sevilla",
    "Valencia": "Valencia",
    "Valladolid": "Real Valladolid",
    "Vallecano": "Rayo Vallecano",
    "Oviedo": "Real Oviedo",

    # Serie A (I1) - Italie
    "Atalanta": "Atalanta",
    "Bologna": "Bologna",
    "Cagliari": "Cagliari",
    "Como": "Como",
    "Empoli": "Empoli",
    "Fiorentina": "Fiorentina",
    "Genoa": "Genoa",
    "Inter": "Inter Milan",
    "Juventus": "Juventus",
    "Lazio": "Lazio",
    "Lecce": "Lecce",
    "AC Milan": "AC Milan",
    "Monza": "Monza",
    "Napoli": "Napoli",
    "Parma": "Parma",
    "Roma": "AS Roma",
    "Torino": "Torino",
    "Udinese": "Udinese",
    "Venezia": "Venezia",
    "Verona": "Hellas Verona",
}


def get_google_team_name(team_name: str) -> str:
    """
    Convertit un nom d'équipe du CSV vers le nom reconnu par Google

    Args:
        team_name: Nom de l'équipe dans le CSV

    Returns:
        Nom de l'équipe pour Google (ou nom original si pas de mapping)
    """
    return TEAM_NAME_MAPPING.get(team_name, team_name)


def get_google_team_names(home_team: str, away_team: str) -> tuple[str, str]:
    """
    Convertit les deux équipes pour Google

    Args:
        home_team: Équipe domicile
        away_team: Équipe extérieur

    Returns:
        Tuple (home_team_google, away_team_google)
    """
    return (get_google_team_name(home_team), get_google_team_name(away_team))
