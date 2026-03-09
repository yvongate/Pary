from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional
import utils.football_data_org as fd_api
import scrapers.ruedesjoueurs_scraper
import scrapers.ruedesjoueurs_finder
import core.ai_preview_generator as ai_preview_generator
import scrapers.soccerstats_working
from gnews import GNews
from core.dynamic_prediction import DynamicPredictor
from services.supabase_client import SupabaseClient
from services.sqlite_database_service import get_sqlite_db

app = FastAPI(title="Football Stats API", version="1.2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 8 championnats
# Championnats supportés pour les prédictions (avec scraping soccerstats.com)
LEAGUES = {
    "E0": {"name": "Premier League", "country": "England"},
    "SP1": {"name": "La Liga", "country": "Spain"},
    "I1": {"name": "Serie A", "country": "Italy"},
    "F1": {"name": "Ligue 1", "country": "France"},
    "D1": {"name": "Bundesliga", "country": "Germany"},
}

# Mapping vers codes soccerstats.com
SOCCERSTATS_CODES = {
    "E0": "england",
    "F1": "france",
    "SP1": "spain",
    "I1": "italy",
    "D1": "germany",
}

# Mapping des variations de noms d'équipes
# Clé = Nom utilisé (fixtures.csv, API, frontend), Valeur = Nom dans CSV historique
TEAM_NAME_MAPPING = {
    # La Liga (Espagne) - fixtures.csv vs SP1_2526.csv
    'Espanyol': 'Espanol',              # fixtures.csv → CSV
    'RCD Espanyol': 'Espanol',
    'Atletico Madrid': 'Ath Madrid',
    'Atlético Madrid': 'Ath Madrid',
    'Atl. Madrid': 'Ath Madrid',        # fixtures.csv → CSV (avec point)
    'Athletic Bilbao': 'Ath Bilbao',
    'Athletic Club': 'Ath Bilbao',
    'Deportivo Alaves': 'Alaves',
    'Real Sociedad': 'Sociedad',
    'Celta Vigo': 'Celta',               # fixtures.csv → CSV (enlève "Vigo")
    'Rayo Vallecano': 'Vallecano',       # fixtures.csv → CSV (enlève "Rayo")

    # Premier League (Angleterre)
    'Manchester United': 'Man United',
    'Manchester City': 'Man City',
    'Newcastle United': 'Newcastle',
    'Tottenham Hotspur': 'Tottenham',
    'Nottingham Forest': "Nott'm Forest",
    'West Ham United': 'West Ham',
    'Wolverhampton': 'Wolves',
    'Brighton & Hove Albion': 'Brighton',
    'Leicester City': 'Leicester',

    # Ligue 1 (France)
    'Paris Saint-Germain': 'Paris SG',
    'Paris Saint Germain': 'Paris SG',
    'PSG': 'Paris SG',
    'Olympique Marseille': 'Marseille',
    'Olympique Lyonnais': 'Lyon',

    # Bundesliga (Allemagne)
    'Bayern Munich': 'Bayern Munich',
    'Bayern München': 'Bayern Munich',
    'Borussia Dortmund': 'Dortmund',
    'Borussia Mönchengladbach': "M'gladbach",
    'VfB Stuttgart': 'Stuttgart',

    # Serie A (Italie)
    'Inter Milan': 'Inter',
    'AC Milan': 'Milan',
    'AS Roma': 'Roma',
}

def normalize_team_name(team_name: str) -> str:
    """
    Normalise un nom d'équipe pour correspondre au format CSV

    Args:
        team_name: Nom de l'équipe (peut varier)

    Returns:
        Nom normalisé correspondant au CSV
    """
    # Enlever espaces superflus
    team_name = team_name.strip()

    # Vérifier mapping direct
    if team_name in TEAM_NAME_MAPPING:
        normalized = TEAM_NAME_MAPPING[team_name]
        print(f"[NORMALIZE] '{team_name}' → '{normalized}'")
        return normalized

    # Sinon retourner tel quel
    return team_name

def get_current_season():
    now = datetime.now()
    year_start = now.year if now.month >= 8 else now.year - 1
    year_end = year_start + 1
    return f"{str(year_start)[2:]}{str(year_end)[2:]}"

def load_fixtures() -> Optional[pd.DataFrame]:
    """Charge le fichier fixtures (matchs  venir)"""
    filepath = "data/fixtures.csv"
    if not os.path.exists(filepath):
        return None
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception as e:
        print(f"Erreur lecture fixtures: {e}")
        return None

def load_results(league_code: str) -> Optional[pd.DataFrame]:
    """Charge les rsultats d'un championnat"""
    season = get_current_season()
    filepath = f"data/{league_code}_{season}.csv"
    if not os.path.exists(filepath):
        return None
    try:
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception as e:
        print(f"Erreur lecture {filepath}: {e}")
        return None

@app.get("/")
def root():
    return {
        "message": "Football Stats API",
        "sources": {
            "fixtures": "football-data.co.uk (CSV auto-update)",
            "results": "football-data.co.uk (CSV)",
            "standings": "soccerstats.com (scraping)",
            "team_stats": "football-data.co.uk (CSV)"
        },
        "season": get_current_season()
    }

@app.get("/fixtures/csv")
def get_fixtures_csv(
    league: Optional[str] = Query(None, description="Code championnat (E0, E1, D1, SP1, I1, F1, F2, P1)"),
    days: int = Query(14, description="Jours  venir  afficher"),
):
    """Matchs  venir depuis les fichiers CSV (fallback)"""
    df = load_fixtures()
    if df is None:
        return {"error": "Fixtures not found. Run download_data.py first."}

    # Normaliser les dates pour comparaison (enlever l'heure)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    date_limit = today + timedelta(days=days)

    # Filtrer par date (incluant aujourd'hui)
    mask = (df['Date'] >= today) & (df['Date'] <= date_limit)
    future = df[mask].copy()

    # Filtrer par ligue si spcifi
    if league:
        future = future[future['Div'] == league]

    matches = []
    for _, row in future.iterrows():
        matches.append({
            "id": f"{row.get('Div')}_{row['Date'].strftime('%Y%m%d')}_{str(row.get('HomeTeam')).replace(' ', '')}",
            "league_code": row.get('Div'),
            "league": LEAGUES.get(row.get('Div'), {}).get('name', row.get('Div')),
            "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
            "time": row.get('Time'),
            "home_team": row.get('HomeTeam'),
            "away_team": row.get('AwayTeam'),
            "status": "SCHEDULED",
        })

    return {"matches": matches, "count": len(matches), "source": "football-data.co.uk (CSV)"}

@app.get("/leagues")
def get_leagues():
    """Liste des 8 championnats"""
    return [{"code": k, **v} for k, v in LEAGUES.items()]

@app.get("/fixtures")
def get_fixtures(
    league: Optional[str] = Query(None, description="Code championnat (E0, D1, SP1, I1, F1)"),
    days: int = Query(14, description="Jours à venir à afficher"),
):
    """Matchs à venir (fixtures) - Source: football-data.co.uk CSV"""

    # Récupérer fixtures CSV
    csv_matches = []
    df = load_fixtures()
    if df is not None:
        SUPPORTED_LEAGUES = ['E0', 'SP1', 'I1', 'F1', 'D1']
        df = df[df['Div'].isin(SUPPORTED_LEAGUES)]

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_limit = today + timedelta(days=days)

        mask = (df['Date'] >= today) & (df['Date'] <= date_limit)
        future = df[mask].copy()

        if league:
            future = future[future['Div'] == league]

        for _, row in future.iterrows():
            csv_matches.append({
                "id": f"{row.get('Div')}_{row['Date'].strftime('%Y%m%d')}_{str(row.get('HomeTeam')).replace(' ', '')}",
                "league_code": row.get('Div'),
                "league": LEAGUES.get(row.get('Div'), {}).get('name', row.get('Div')),
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "time": row.get('Time'),
                "home_team": row.get('HomeTeam'),
                "away_team": row.get('AwayTeam'),
                "referee": row.get('Referee') if pd.notna(row.get('Referee')) else None,
                "odds_home": float(row.get('B365H')) if pd.notna(row.get('B365H')) else None,
                "odds_draw": float(row.get('B365D')) if pd.notna(row.get('B365D')) else None,
                "odds_away": float(row.get('B365A')) if pd.notna(row.get('B365A')) else None,
                "status": "SCHEDULED",
                "source": "CSV"
            })

        print(f"[FIXTURES] CSV: {len(csv_matches)} matchs récupérés")

    today = datetime.now()
    date_limit = today + timedelta(days=days)

    print(f"[FIXTURES] TOTAL: {len(csv_matches)} matchs")

    return {
        "matches": csv_matches,
        "count": len(csv_matches),
        "period": f"{today.strftime('%Y-%m-%d')} to {date_limit.strftime('%Y-%m-%d')}",
        "source": "football-data.co.uk (CSV)"
    }

@app.get("/results")
def get_results(
    league: Optional[str] = Query(None, description="Code championnat"),
    days: int = Query(7, description="Jours passs  afficher"),
):
    """Rsultats des matchs passs"""
    today = datetime.now()
    date_start = today - timedelta(days=days)

    all_matches = []

    leagues_to_check = [league] if league else list(LEAGUES.keys())

    for league_code in leagues_to_check:
        df = load_results(league_code)
        if df is None:
            continue

        # Filtrer par date et matchs termins (avec score)
        mask = (df['Date'] >= date_start) & (df['Date'] <= today) & (df['FTHG'].notna())
        recent = df[mask].copy()

        for _, row in recent.iterrows():
            all_matches.append({
                "id": f"{league_code}_{row['Date'].strftime('%Y%m%d')}_{str(row.get('HomeTeam')).replace(' ', '')}",
                "league_code": league_code,
                "league": LEAGUES.get(league_code, {}).get('name', league_code),
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "home_team": row.get('HomeTeam'),
                "away_team": row.get('AwayTeam'),
                "home_score": int(row['FTHG']) if pd.notna(row.get('FTHG')) else None,
                "away_score": int(row['FTAG']) if pd.notna(row.get('FTAG')) else None,
                "ht_home_score": int(row['HTHG']) if pd.notna(row.get('HTHG')) else None,
                "ht_away_score": int(row['HTAG']) if pd.notna(row.get('HTAG')) else None,
                "result": row.get('FTR'),  # H/D/A
                "status": "FINISHED",
            })

    all_matches.sort(key=lambda x: x['date'] or '', reverse=True)

    return {"matches": all_matches, "count": len(all_matches)}

@app.get("/calendar")
def get_calendar(
    league: Optional[str] = Query(None, description="Code championnat (E0, E1, D1, SP1, I1, F1, F2, P1)"),
    days_past: int = Query(7, description="Jours passs  afficher"),
    days_future: int = Query(7, description="Jours futurs  afficher"),
):
    """Calendrier complet: jours passs + aujourd'hui + jours futurs"""
    today = datetime.now()

    # Rcuprer les rsultats passs (des CSV)
    date_start = today - timedelta(days=days_past)
    past_matches = []

    leagues_to_check = [league] if league else list(LEAGUES.keys())

    for league_code in leagues_to_check:
        df = load_results(league_code)
        if df is None:
            continue

        mask = (df['Date'] >= date_start) & (df['Date'] <= today) & (df['FTHG'].notna())
        recent = df[mask].copy()

        for _, row in recent.iterrows():
            past_matches.append({
                "id": f"{league_code}_{row['Date'].strftime('%Y%m%d')}_{str(row.get('HomeTeam')).replace(' ', '')}",
                "league_code": league_code,
                "league": LEAGUES.get(league_code, {}).get('name', league_code),
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "time": row.get('Time'),
                "home_team": row.get('HomeTeam'),
                "away_team": row.get('AwayTeam'),
                "home_score": int(row['FTHG']) if pd.notna(row.get('FTHG')) else None,
                "away_score": int(row['FTAG']) if pd.notna(row.get('FTAG')) else None,
                "status": "FINISHED",
            })

    # Rcuprer les fixtures futurs (de l'API)
    future_matches = fd_api.get_all_fixtures(days_future=days_future, league_code=league)

    # Combiner
    all_matches = past_matches + future_matches

    # Trier par date
    all_matches.sort(key=lambda x: x['date'] or '')

    return {
        "today": today.strftime('%Y-%m-%d'),
        "period": {
            "start": date_start.strftime('%Y-%m-%d'),
            "end": (today + timedelta(days=days_future)).strftime('%Y-%m-%d')
        },
        "matches": all_matches,
        "count": len(all_matches),
        "count_past": len(past_matches),
        "count_future": len(future_matches),
    }

@app.get("/calendar/days")
def get_calendar_days(
    league: Optional[str] = Query(None, description="Code championnat"),
    days_past: int = Query(7, description="Jours passs  afficher"),
    days_future: int = Query(7, description="Jours futurs  afficher"),
):
    """Calendrier group par jour - pour l'affichage du frontend"""
    today = datetime.now()

    # Rcuprer les rsultats passs
    date_start = today - timedelta(days=days_past)
    past_matches = []

    leagues_to_check = [league] if league else list(LEAGUES.keys())

    for league_code in leagues_to_check:
        df = load_results(league_code)
        if df is None:
            continue

        mask = (df['Date'] >= date_start) & (df['Date'] <= today) & (df['FTHG'].notna())
        recent = df[mask].copy()

        for _, row in recent.iterrows():
            past_matches.append({
                "id": f"{league_code}_{row['Date'].strftime('%Y%m%d')}_{str(row.get('HomeTeam')).replace(' ', '')}",
                "league_code": league_code,
                "league": LEAGUES.get(league_code, {}).get('name', league_code),
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "time": row.get('Time'),
                "home_team": row.get('HomeTeam'),
                "away_team": row.get('AwayTeam'),
                "home_score": int(row['FTHG']) if pd.notna(row.get('FTHG')) else None,
                "away_score": int(row['FTAG']) if pd.notna(row.get('FTAG')) else None,
                "status": "FINISHED",
            })

    # Rcuprer les fixtures futurs
    future_matches = fd_api.get_all_fixtures(days_future=days_future, league_code=league)

    # Combiner
    all_matches = past_matches + future_matches

    # Grouper par date
    from collections import defaultdict
    days_dict = defaultdict(list)

    for match in all_matches:
        if match['date']:
            days_dict[match['date']].append(match)

    # Crer la liste des jours (passs -> futurs)
    days_list = []
    current = date_start
    end_date = today + timedelta(days=days_future)

    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        is_today = date_str == today.strftime('%Y-%m-%d')
        is_past = date_str < today.strftime('%Y-%m-%d')

        days_list.append({
            "date": date_str,
            "is_today": is_today,
            "is_past": is_past,
            "is_future": not is_today and not is_past,
            "matches": days_dict.get(date_str, [])
        })
        current += timedelta(days=1)

    return {
        "today": today.strftime('%Y-%m-%d'),
        "days": days_list,
        "total_matches": len(all_matches),
    }

@app.get("/team/{team_name}/stats")
def get_team_stats(team_name: str, league: Optional[str] = None):
    """Stats d'une quipe sur la saison"""
    leagues_to_check = [league] if league else list(LEAGUES.keys())

    all_matches = []
    for league_code in leagues_to_check:
        df = load_results(league_code)
        if df is None:
            continue

        # Matchs  domicile
        home = df[(df['HomeTeam'].str.lower() == team_name.lower()) & (df['FTHG'].notna())]
        for _, row in home.iterrows():
            all_matches.append({
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "opponent": row.get('AwayTeam'),
                "venue": "home",
                "goals_for": int(row['FTHG']) if pd.notna(row['FTHG']) else 0,
                "goals_against": int(row['FTAG']) if pd.notna(row['FTAG']) else 0,
                "result": row.get('FTR'),
                "league": LEAGUES.get(league_code, {}).get('name', league_code),
            })

        # Matchs  l'extrieur
        away = df[(df['AwayTeam'].str.lower() == team_name.lower()) & (df['FTHG'].notna())]
        for _, row in away.iterrows():
            all_matches.append({
                "date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                "opponent": row.get('HomeTeam'),
                "venue": "away",
                "goals_for": int(row['FTAG']) if pd.notna(row['FTAG']) else 0,
                "goals_against": int(row['FTHG']) if pd.notna(row['FTHG']) else 0,
                "result": row.get('FTR'),
                "league": LEAGUES.get(league_code, {}).get('name', league_code),
            })

    if not all_matches:
        return {"error": f"Team '{team_name}' not found"}

    played = len(all_matches)
    wins = sum(1 for m in all_matches if (m['venue'] == 'home' and m['result'] == 'H') or (m['venue'] == 'away' and m['result'] == 'A'))
    draws = sum(1 for m in all_matches if m['result'] == 'D')
    losses = played - wins - draws

    gf = sum(m['goals_for'] for m in all_matches)
    ga = sum(m['goals_against'] for m in all_matches)

    return {
        "team": team_name,
        "matches": all_matches,
        "summary": {
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": gf,
            "goals_against": ga,
            "goal_difference": gf - ga,
            "win_rate": round(wins / played * 100, 1) if played > 0 else 0,
        }
    }

@app.get("/standings")
def get_standings(league: str = Query(..., description="Code championnat")):
    """Classement d'une ligue"""
    if league not in LEAGUES:
        return {"error": f"League '{league}' not found"}

    df = load_results(league)
    if df is None:
        return {"error": f"No data for league {league}"}

    teams = {}

    for _, row in df.iterrows():
        if pd.isna(row.get('FTHG')) or pd.isna(row.get('FTAG')):
            continue

        home = row.get('HomeTeam')
        away = row.get('AwayTeam')
        ftr = row.get('FTR')

        for team in [home, away]:
            if team not in teams:
                teams[team] = {"played": 0, "wins": 0, "draws": 0, "losses": 0, "gf": 0, "ga": 0, "points": 0}

        # Home
        teams[home]["played"] += 1
        teams[home]["gf"] += int(row['FTHG'])
        teams[home]["ga"] += int(row['FTAG'])
        if ftr == 'H':
            teams[home]["wins"] += 1
            teams[home]["points"] += 3
        elif ftr == 'D':
            teams[home]["draws"] += 1
            teams[home]["points"] += 1
        else:
            teams[home]["losses"] += 1

        # Away
        teams[away]["played"] += 1
        teams[away]["gf"] += int(row['FTAG'])
        teams[away]["ga"] += int(row['FTHG'])
        if ftr == 'A':
            teams[away]["wins"] += 1
            teams[away]["points"] += 3
        elif ftr == 'D':
            teams[away]["draws"] += 1
            teams[away]["points"] += 1
        else:
            teams[away]["losses"] += 1

    standings = [{"team": t, **s, "gd": s["gf"] - s["ga"]} for t, s in teams.items()]
    standings.sort(key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)

    for i, t in enumerate(standings):
        t["position"] = i + 1

    return {"league": LEAGUES[league]["name"], "season": get_current_season(), "standings": standings}

@app.get("/standings/live")
def get_live_standings(league: str = Query(..., description="Code championnat (E0, F1, SP1, I1, D1)")):
    """
    Classement EN TEMPS REL depuis soccerstats.com

    Disponible pour: Premier League (E0), Ligue 1 (F1), La Liga (SP1), Serie A (I1), Bundesliga (D1)
    """
    if league not in SOCCERSTATS_CODES:
        return {
            "error": f"Live standings not available for '{league}'",
            "available": list(SOCCERSTATS_CODES.keys())
        }

    soccerstats_code = SOCCERSTATS_CODES[league]
    standings = soccerstats_working.get_standings(soccerstats_code)

    if not standings:
        return {"error": f"Failed to fetch live standings for {league}"}

    return {
        "league": LEAGUES[league]["name"],
        "country": LEAGUES[league]["country"],
        "source": "soccerstats.com",
        "last_updated": datetime.now().isoformat(),
        "standings": standings
    }

@app.get("/standings/live/team")
def get_live_team_standing(
    team: str = Query(..., description="Nom de l'quipe"),
    league: str = Query(..., description="Code championnat (E0, F1, SP1, I1, D1)")
):
    """
    Classement d'une quipe spcifique avec contexte comptitif

    Retourne: position, points, forme, carts (leader/Top4/relgation)
    """
    if league not in SOCCERSTATS_CODES:
        return {
            "error": f"Live standings not available for '{league}'",
            "available": list(SOCCERSTATS_CODES.keys())
        }

    soccerstats_code = SOCCERSTATS_CODES[league]
    team_data = soccerstats_working.get_team_context(team, soccerstats_code)

    if not team_data:
        return {"error": f"Team '{team}' not found in {LEAGUES[league]['name']}"}

    return {
        "league": LEAGUES[league]["name"],
        "country": LEAGUES[league]["country"],
        "source": "soccerstats.com",
        "last_updated": datetime.now().isoformat(),
        "team_data": team_data
    }

@app.get("/match/analysis")
def get_match_analysis(
    url: str = Query(..., description="URL complte de l'analyse sur ruedesjoueurs.com"),
):
    """
    Rcupre l'analyse complte d'un match depuis ruedesjoueurs.com

    Retourne :
    - Contexte du match (enjeux, motivation)
    - Forme rcente des quipes
    - Effectifs (blessures, suspensions, compositions)
    - Confrontations directes
    - Statistiques cls
    - Pronostics

    Exemple:
    /match/analysis?url=https://www.ruedesjoueurs.com/pronostic/sunderland-fulham-4813642.html
    """
    data = ruedesjoueurs_scraper.scrape_match_preview(url)

    if not data:
        return {
            "error": "Analysis not found",
            "message": f"Impossible de rcuprer l'analyse depuis {url}"
        }

    return {
        "home_team": data.get("home_team"),
        "away_team": data.get("away_team"),
        "title": data.get("title"),
        "url": url,
        "analysis": {
            "full_text": data.get("full_text"),
            "sections": data.get("sections"),
            "lineups": data.get("lineups_text"),
            "injuries": data.get("injuries_text"),
        },
        "source": "ruedesjoueurs.com"
    }


@app.get("/match/rdj-auto")
def get_rdj_analysis_auto(
    home_team: str = Query(..., description="Nom de l'quipe  domicile"),
    away_team: str = Query(..., description="Nom de l'quipe  l'extrieur"),
):
    """
     Rcupre automatiquement l'analyse ruedesjoueurs.com via SerpAPI

    Processus :
    1. Recherche Google via SerpAPI : "home_team vs away_team rue des joueurs"
    2. Rcupre le premier lien ruedesjoueurs.com
    3. Scrape l'analyse complte

    Exemple:
    /match/rdj-auto?home_team=Nice&away_team=Lorient

    Retourne :
    - Analyse complte du match
    - Enjeux, forme, compositions, pronostics
    - Blessures et suspensions
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()

        serpapi_key = os.getenv("SERPAPI_KEY")

        if not serpapi_key:
            return {
                "error": "SerpAPI key not configured",
                "message": "Ajoutez SERPAPI_KEY dans le fichier .env"
            }

        # Recherche automatique + scraping
        data = ruedesjoueurs_finder.get_match_analysis_auto(
            home_team=home_team,
            away_team=away_team,
            serpapi_key=serpapi_key
        )

        if not data:
            return {
                "error": "Analysis not found",
                "message": f"Aucune analyse trouve pour {home_team} vs {away_team}",
                "suggestion": "Vrifiez l'orthographe des noms d'quipes"
            }

        return {
            "home_team": data.get("home_team"),
            "away_team": data.get("away_team"),
            "title": data.get("title"),
            "url": data.get("url"),
            "found_via": data.get("found_via"),
            "analysis": {
                "full_text": data.get("full_text"),
                "sections": data.get("sections"),
                "lineups": data.get("lineups_text"),
                "injuries": data.get("injuries_text"),
            },
            "source": "ruedesjoueurs.com (auto via SerpAPI)"
        }

    except Exception as e:
        return {
            "error": "Search failed",
            "message": str(e),
            "home_team": home_team,
            "away_team": away_team
        }


@app.get("/match/weather")
def get_match_weather(
    home_team: str = Query(..., description="Nom de l'quipe  domicile"),
    away_team: str = Query(..., description="Nom de l'quipe  l'extrieur"),
    match_date: str = Query(..., description="Date du match (YYYY-MM-DD)"),
):
    """
    Rcupre les prvisions mto pour un match

    Utilise :
    - Stadium mapping (gratuit) pour trouver le stade et la ville
    - OpenWeather API (gratuit) pour les prvisions mto

    Exemple:
    /match/weather?home_team=Liverpool&away_team=Arsenal&match_date=2026-02-22

    Retourne :
    - Stade et ville
    - Temprature et ressenti
    - Conditions mto (pluie, nuages, etc.)
    - Vent (vitesse et direction)
    - Humidit et prcipitations
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Utiliser wttr.in (gratuit, pas de cl API requise)
        import weather_wttr

        weather = weather_wttr.get_match_weather_wttr(
            home_team=home_team,
            away_team=away_team,
            match_date=match_date
        )

        if not weather:
            return {
                "error": "Weather not found",
                "message": f"Impossible de rcuprer la mto pour {home_team} vs {away_team}",
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_date
            }

        return {
            "match": {
                "home_team": weather["home_team"],
                "away_team": weather["away_team"],
                "date": weather["date"],
                "stadium": weather["stadium"],
                "city": weather["city"]
            },
            "forecast": {
                "forecast_time": weather["forecast_time"],
                "temperature": weather["temperature"],
                "feels_like": weather["feels_like"],
                "temp_range": {
                    "min": weather["temp_min"],
                    "max": weather["temp_max"]
                },
                "weather": weather["weather"],
                "description": weather["weather_description"],
                "humidity": weather["humidity"],
                "wind": {
                    "speed": weather["wind_speed"],
                    "direction": weather["wind_direction"],
                    "degrees": weather["wind_deg"]
                },
                "precipitation": weather["precipitation"],
                "clouds": weather["clouds"],
                "icon": weather["icon"]
            },
            "impact_analysis": analyze_weather_impact(weather),
            "source": "wttr.in (gratuit)"
        }

    except Exception as e:
        return {
            "error": "Weather fetch failed",
            "message": str(e),
            "home_team": home_team,
            "away_team": away_team,
            "match_date": match_date
        }


def analyze_weather_impact(weather: dict) -> dict:
    """
    Analyse l'impact de la mto sur le match

    Returns:
        {
            "playing_conditions": "Difficiles" | "Bonnes" | "Idales",
            "factors": ["Pluie lgre", "Vent fort", etc.],
            "recommendations": ["Match physique attendu", etc.]
        }
    """
    factors = []
    recommendations = []

    temp = weather["temperature"]
    wind_speed = weather["wind_speed"]
    precipitation = weather["precipitation"]
    humidity = weather["humidity"]

    # Temprature
    if temp < 5:
        factors.append("Tempratures froides")
        recommendations.append("Ballon plus dur, risque de blessures musculaires")
    elif temp > 25:
        factors.append("Tempratures chaudes")
        recommendations.append("Risque de fatigue accrue, hydratation importante")

    # Vent
    if wind_speed > 10:
        factors.append("Vent trs fort")
        recommendations.append("Jeu arien perturb, passes longues difficiles")
    elif wind_speed > 6:
        factors.append("Vent modr")
        recommendations.append("Jeu au sol privilgi")

    # Prcipitations
    if precipitation > 5:
        factors.append("Pluie forte")
        recommendations.append("Terrain glissant, jeu technique difficile")
    elif precipitation > 0.5:
        factors.append("Pluie lgre")
        recommendations.append("Terrain lgrement humide, ballon rapide")

    # Humidit
    if humidity > 85:
        factors.append("Forte humidit")
        recommendations.append("Sensation de froid accrue")

    # Dterminer les conditions globales
    if len(factors) == 0:
        conditions = "Idales"
        recommendations.append("Conditions optimales pour le football")
    elif len(factors) <= 2:
        conditions = "Bonnes"
    else:
        conditions = "Difficiles"

    return {
        "playing_conditions": conditions,
        "factors": factors if factors else ["Pas de facteurs dfavorables"],
        "recommendations": recommendations
    }


@app.get("/match/ai-preview")
def get_ai_match_preview(
    home_team: str = Query(..., description="Nom de l'quipe  domicile"),
    away_team: str = Query(..., description="Nom de l'quipe  l'extrieur"),
    league_code: str = Query(..., description="Code du championnat (E0, SP1, etc.)"),
    match_date: str = Query(..., description="Date du match (YYYY-MM-DD)"),
):
    """
    Gnre une analyse pr-match complte avec IA

    Combine :
    - Forme rcente (depuis CSV)
    - Head-to-Head (depuis CSV)
    - Actualits (Google News)
    - Analyse gnre par IA (OpenAI GPT)

    Exemple:
    /match/ai-preview?home_team=Liverpool&away_team=Arsenal&league_code=E0&match_date=2026-02-22
    """
    try:
        # Rcuprer la cl API (DeepInfra en priorit, sinon OpenAI)
        from dotenv import load_dotenv
        load_dotenv()
        openai_key = os.getenv("DEEPINFRA_API_KEY") or os.getenv("OPENAI_API_KEY")

        result = ai_preview_generator.generate_prematch_analysis(
            home_team=home_team,
            away_team=away_team,
            league_code=league_code,
            match_date=match_date,
            openai_api_key=openai_key
        )

        return {
            "home_team": result["home_team"],
            "away_team": result["away_team"],
            "match_date": result["match_date"],
            "analysis": result["ai_analysis"],
            "data": result["data"],
            "source": "AI Generated (CSV + GNews + OpenAI)"
        }

    except Exception as e:
        return {
            "error": "Generation failed",
            "message": str(e),
            "home_team": home_team,
            "away_team": away_team
        }


@app.get("/team/{team_name}/news")
def get_team_news(
    team_name: str,
    max_results: int = Query(10, description="Nombre max d'articles  rcuprer"),
    period: str = Query("7d", description="Priode: 7d, 14d, 1m, etc.")
):
    """Rcupre les dernires news d'une quipe depuis Google News"""
    try:
        # Initialiser GNews
        google_news = GNews(language='fr', country='FR', max_results=max_results, period=period)

        # Rechercher les news de l'quipe
        query = f"{team_name} football"
        news = google_news.get_news(query)

        # Formater les rsultats
        articles = []
        for article in news:
            articles.append({
                "title": article.get('title'),
                "description": article.get('description'),
                "published_date": article.get('published date'),
                "url": article.get('url'),
                "publisher": article.get('publisher', {}).get('title', 'Unknown'),
                "publisher_url": article.get('publisher', {}).get('href')
            })

        return {
            "team": team_name,
            "articles": articles,
            "count": len(articles),
            "period": period,
            "source": "Google News"
        }
    except Exception as e:
        return {
            "error": str(e),
            "team": team_name,
            "articles": [],
            "count": 0
        }

@app.get("/match/news")
def get_match_news(
    home_team: str = Query(..., description="Nom de l'quipe  domicile"),
    away_team: str = Query(..., description="Nom de l'quipe  l'extrieur"),
    max_results: int = Query(5, description="Nombre max d'articles par quipe"),
    period: str = Query("7d", description="Priode: 7d, 14d, 1m, etc.")
):
    """Rcupre les news des deux quipes d'un match"""
    try:
        google_news = GNews(language='fr', country='FR', max_results=max_results, period=period)

        # News quipe domicile
        home_news = google_news.get_news(f"{home_team} football")
        home_articles = [{
            "title": a.get('title'),
            "description": a.get('description'),
            "published_date": a.get('published date'),
            "url": a.get('url'),
            "publisher": a.get('publisher', {}).get('title', 'Unknown'),
            "publisher_url": a.get('publisher', {}).get('href'),
            "team": home_team
        } for a in home_news]

        # News quipe extrieur
        away_news = google_news.get_news(f"{away_team} football")
        away_articles = [{
            "title": a.get('title'),
            "description": a.get('description'),
            "published_date": a.get('published date'),
            "url": a.get('url'),
            "publisher": a.get('publisher', {}).get('title', 'Unknown'),
            "publisher_url": a.get('publisher', {}).get('href'),
            "team": away_team
        } for a in away_news]

        # Combiner et trier par date
        all_articles = home_articles + away_articles

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_articles": home_articles,
            "away_articles": away_articles,
            "all_articles": all_articles,
            "total_count": len(all_articles),
            "period": period,
            "source": "Google News"
        }
    except Exception as e:
        return {
            "error": str(e),
            "home_team": home_team,
            "away_team": away_team,
            "articles": [],
            "total_count": 0
        }


# === PREDICTION ENDPOINTS (DYNAMIQUE - TEMPS REL) ===

# Initialize dynamic predictor (global instance)
# use_formations=True  Analyse les performances par formation (plus lent mais plus prcis)
predictor = DynamicPredictor(use_formations=True)

# Initialize Supabase client (pour rcuprer les prdictions pr-calcules)
supabase_client = SupabaseClient()


@app.get("/predict/match")
def predict_match(
    home_team: str = Query(..., description="Nom de l'quipe  domicile"),
    away_team: str = Query(..., description="Nom de l'quipe  l'extrieur"),
    league: str = Query("E0", description="Code championnat (E0, SP1, I1, F1, D1)"),
):
    """
     Prdiction DYNAMIQUE - Calcul en temps rel pour ce match

    PAS de ML pr-entran! Pour chaque match:
    1. Rcupre les donnes EN TEMPS REL (classements actuels, mto du jour)
    2. Analyse TOUS les matchs historiques de l'quipe (CSV)
    3. Fait la corrlation  LA VOLE avec les rangs dfensifs
    4. Prdit avec la situation ACTUELLE

    Sources:
    - Matchs historiques: CSV (football-data.co.uk)
    - Classements ACTUELS: soccerstats.com (live)
    - Mto DU JOUR: wttr.in

    Exemple:
    /predict/match?home_team=Tottenham&away_team=Arsenal&league=E0
    """
    # Map league code to soccerstats code
    soccerstats_code = SOCCERSTATS_CODES.get(league, "england")

    try:
        result = predictor.predict_match(
            home_team=home_team,
            away_team=away_team,
            league_code=soccerstats_code,
            match_date=datetime.now()
        )

        if 'error' in result:
            return {
                "error": result['error'],
                "message": result.get('message', ''),
                "home_team": home_team,
                "away_team": away_team,
                "league": LEAGUES.get(league, {}).get('name', league)
            }

        # Add league name
        result['match']['league_name'] = LEAGUES.get(league, {}).get('name', league)
        result['match']['league_code'] = league
        result['method'] = "Dynamic Real-Time Correlation (no pre-training)"
        result['data_freshness'] = "Live rankings + Current weather + Historical analysis"

        return result

    except Exception as e:
        return {
            "error": "Prediction failed",
            "message": str(e),
            "home_team": home_team,
            "away_team": away_team,
            "league": LEAGUES.get(league, {}).get('name', league)
        }


@app.get("/predict/batch")
def predict_batch_matches(
    league: str = Query("E0", description="Code championnat"),
    days: int = Query(7, description="Jours futurs  prdire"),
    limit: int = Query(5, description="Nombre max de matchs (viter timeout)"),
):
    """
     Prdire plusieurs matchs  venir (calcul dynamique pour chacun)

    ATTENTION: Chaque match ncessite:
    - Chargement de l'historique complet (200+ matchs)
    - Rcupration des classements live
    - Calcul de corrlation  la vole

    Limit  5 matchs par dfaut pour viter le timeout.

    Exemple:
    /predict/batch?league=E0&days=7&limit=5
    """
    soccerstats_code = SOCCERSTATS_CODES.get(league, "england")

    try:
        # Get upcoming fixtures
        fixtures = fd_api.get_all_fixtures(days_future=days, league_code=league)

        if not fixtures:
            return {
                "error": "No upcoming fixtures found",
                "league": LEAGUES.get(league, {}).get('name', league),
                "days": days
            }

        # Limit matches
        fixtures = fixtures[:min(limit, len(fixtures))]

        # Make predictions dynamically
        results = []
        for i, fixture in enumerate(fixtures):
            print(f"\n[{i+1}/{len(fixtures)}] Prdiction: {fixture['home_team']} vs {fixture['away_team']}")

            result = predictor.predict_match(
                home_team=fixture['home_team'],
                away_team=fixture['away_team'],
                league_code=soccerstats_code,
                match_date=datetime.fromisoformat(fixture['date']) if fixture.get('date') else None
            )

            if 'error' not in result:
                results.append(result)

        return {
            "league": LEAGUES.get(league, {}).get('name', league),
            "league_code": league,
            "period_days": days,
            "predictions": results,
            "count": len(results),
            "method": "Dynamic Real-Time Correlation (per match)",
            "warning": "Each prediction uses live data - results may vary over time"
        }

    except Exception as e:
        return {
            "error": "Batch prediction failed",
            "message": str(e),
            "league": LEAGUES.get(league, {}).get('name', league)
        }


@app.get("/predict/info")
def get_prediction_info():
    """
     Information sur le systme de prdiction DYNAMIQUE
    """
    return {
        "method": "Dynamic Real-Time Prediction",
        "description": "PAS de machine learning pr-entran! Calcul  la vole pour chaque match.",
        "how_it_works": {
            "step_1": {
                "title": "Rcupration donnes EN TEMPS REL",
                "sources": [
                    "Classements ACTUELS (soccerstats.com - live)",
                    "Mto DU JOUR (wttr.in)",
                    "Rangs dfensifs ACTUELS des adversaires"
                ]
            },
            "step_2": {
                "title": "Chargement historique complet",
                "description": "Charge TOUS les matchs historiques de l'quipe depuis les CSV",
                "source": "football-data.co.uk (2-3 dernires saisons)",
                "typical_count": "100-200 matchs par quipe"
            },
            "step_3": {
                "title": "Analyse de corrlation  LA VOLE",
                "description": "Trouve la relation mathmatique entre performances passes et rangs dfensifs",
                "formula": "Tirs = a  rang_dfense_adversaire + b",
                "method": "Rgression linaire simple (numpy.polyfit)"
            },
            "step_4": {
                "title": "Application aux donnes ACTUELLES",
                "description": "Utilise les rangs dfensifs ACTUELS de l'adversaire pour prdire",
                "adjustments": [
                    "Facteur mto (vent augmente corners)",
                    "Facteur temprature (optimale ~15C)",
                    "Domicile vs Extrieur"
                ]
            }
        },
        "why_dynamic": {
            "reason_1": "Les donnes changent constamment (classements, blessures, forme)",
            "reason_2": "Un joueur bless peut tout changer pour une quipe",
            "reason_3": "Les rangs dfensifs voluent chaque semaine",
            "reason_4": "La mto du jour d'un match impacte le jeu",
            "conclusion": "Impossible d'utiliser un modle pr-entran - il faut calculer EN TEMPS REL"
        },
        "data_sources": {
            "historical_matches": {
                "source": "football-data.co.uk CSV",
                "data": "Rsultats historiques (tirs, corners, buts)",
                "freshness": "Historique (2-3 saisons)"
            },
            "current_rankings": {
                "source": "soccerstats.com (scraping)",
                "data": "12 classements diffrents (attaque, dfense, forme, domicile/extrieur)",
                "freshness": "TEMPS REL (scraped  chaque requte)"
            },
            "weather": {
                "source": "wttr.in",
                "data": "Vent, temprature, prcipitations",
                "freshness": "TEMPS REL (prvisions du jour)"
            }
        },
        "predictions": {
            "home_shots": "Tirs de l'quipe  domicile",
            "home_corners": "Corners de l'quipe  domicile",
            "away_shots": "Tirs de l'quipe  l'extrieur",
            "away_corners": "Corners de l'quipe  l'extrieur",
            "total_shots": "Total des tirs",
            "total_corners": "Total des corners"
        },
        "confidence_metric": {
            "name": "R (coefficient de dtermination)",
            "range": "0  1",
            "interpretation": {
                "R2 > 0.9": "Excellente corrlation",
                "R2 > 0.7": "Bonne corrlation",
                "R2 > 0.5": "Corrlation acceptable",
                "R2 < 0.5": "Faible corrlation (prdiction peu fiable)"
            }
        },
        "performance": {
            "typical_response_time": "5-10 secondes par match",
            "breakdown": {
                "load_historical_matches": "2-3s",
                "scrape_live_rankings": "1-2s",
                "correlation_analysis": "1s",
                "weather_fetch": "0.5s"
            },
            "note": "Temps rel = plus lent mais donnes fraches"
        },
        "example_workflow": {
            "request": "Tottenham vs Arsenal",
            "step_1": "Charge 150 matchs de Tottenham (CSV)",
            "step_2": "Rcupre rang dfense d'Arsenal AUJOURD'HUI (2e)",
            "step_3": "Trouve corrlation: Tirs_Tottenham = 0.65  rang_dfense + 8.2",
            "step_4": "Calcule: 0.65  2 + 8.2 = 9.5 tirs prdits",
            "step_5": "Ajuste selon mto du jour (vent 20km/h  +10% corners)",
            "result": "Prdiction base sur donnes ACTUELLES"
        }
    }


# === PREDICTIONS PR-CALCULES (DEPUIS SUPABASE) ===

@app.get("/predictions/upcoming")
def get_upcoming_predictions(
    league: Optional[str] = Query(None, description="Code championnat (E0, SP1, I1, F1, D1)"),
    limit: int = Query(20, description="Nombre max de prdictions")
):
    """
     Rcupre les prdictions pr-calcules pour les matchs  venir

    Les prdictions sont calcules automatiquement par le cron
    chaque jour à 10:00 pour les matchs des prochaines 48h

    Exemple:
    /predictions/upcoming?league=E0&limit=10
    """
    try:
        # Utiliser SQLite au lieu de Supabase
        sqlite_db = get_sqlite_db()
        predictions = sqlite_db.get_upcoming_predictions(
            league_code=league,
            limit=limit
        )

        # Formatter les rsultats
        formatted_predictions = []
        for pred in predictions:
            # Helper pour formater les dates (SQLite renvoie des strings)
            match_date = pred.get('match_date')
            if match_date and hasattr(match_date, 'isoformat'):
                match_date = match_date.isoformat()

            created_at = pred.get('created_at')
            if created_at and hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()

            formatted_predictions.append({
                'match_id': pred['match_id'],
                'home_team': pred['home_team'],
                'away_team': pred['away_team'],
                'league_code': pred['league_code'],
                'league_name': LEAGUES.get(pred['league_code'], {}).get('name', pred['league_code']),
                'match_date': match_date,

                # Prdictions TIRS
                'shots': {
                    'min': pred['shots_min'],
                    'max': pred['shots_max'],
                    'confidence': float(pred['shots_confidence']),
                    'message_min': f"Il y aura PLUS de {pred['shots_min']} tirs",
                    'message_max': f"Il y aura MOINS de {pred['shots_max']} tirs",
                    # Messages par équipe (Méthode 1 - Poisson + IA Tactique)
                    'home_team_message': f"{pred['home_team']}: {pred.get('home_shots', 'N/A')} tirs" if pred.get('home_shots') else None,
                    'away_team_message': f"{pred['away_team']}: {pred.get('away_shots', 'N/A')} tirs" if pred.get('away_shots') else None,
                },

                # Prdictions CORNERS
                'corners': {
                    'min': pred['corners_min'],
                    'max': pred['corners_max'],
                    'confidence': float(pred['corners_confidence']),
                    'message_min': f"Il y aura PLUS de {pred['corners_min']} corners",
                    'message_max': f"Il y aura MOINS de {pred['corners_max']} corners",
                    # Messages par équipe (Méthode 1 - Poisson + IA Tactique)
                    'home_team_message': f"{pred['home_team']}: {pred.get('home_corners', 'N/A')} corners" if pred.get('home_corners') else None,
                    'away_team_message': f"{pred['away_team']}: {pred.get('away_corners', 'N/A')} corners" if pred.get('away_corners') else None,
                },

                # Analyses IA (prendre seulement ai_reasoning_shots pour éviter duplication)
                'ai_reasoning': pred.get('ai_reasoning_shots') or pred.get('ai_reasoning_corners'),

                # Formations
                'formations': {
                    'home': pred.get('home_formation'),
                    'away': pred.get('away_formation')
                },

                # Mto (informatif)
                'weather': pred.get('weather'),

                'created_at': created_at
            })

        return {
            'league': league,
            'league_name': LEAGUES.get(league, {}).get('name', 'Tous') if league else 'Tous',
            'predictions': formatted_predictions,
            'count': len(formatted_predictions),
            'source': 'SQLite (pr-calcules par cron)'
        }

    except Exception as e:
        return {
            'error': 'Erreur rcupration prdictions',
            'message': str(e),
            'predictions': [],
            'count': 0
        }


@app.get("/predictions/match/{match_id}")
def get_prediction_detail(match_id: str):
    """
     Rcupre le dtail complet d'une prdiction

    Inclut:
    - Prdictions tirs et corners
    - Analyses dtailles (tapes pour chaque quipe)
    - Textes IA
    - Formations, mto, classements utiliss

    Exemple:
    /predictions/match/E0_20260225_TottenhamArsenal
    """
    try:
        # Utiliser SQLite au lieu de Supabase
        sqlite_db = get_sqlite_db()
        prediction = sqlite_db.get_prediction_by_match_id(match_id)

        if not prediction:
            return {
                'error': 'Prdiction non trouve',
                'match_id': match_id
            }

        # Helper pour formater les dates (SQLite renvoie des strings)
        match_date = prediction.get('match_date')
        if match_date and hasattr(match_date, 'isoformat'):
            match_date = match_date.isoformat()

        created_at = prediction.get('created_at')
        if created_at and hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()

        updated_at = prediction.get('updated_at')
        if updated_at and hasattr(updated_at, 'isoformat'):
            updated_at = updated_at.isoformat()

        return {
            'match_id': prediction['match_id'],
            'home_team': prediction['home_team'],
            'away_team': prediction['away_team'],
            'league_code': prediction['league_code'],
            'league_name': LEAGUES.get(prediction['league_code'], {}).get('name', prediction['league_code']),
            'match_date': match_date,

            # Tirs/Corners par équipe (NOUVEAU - pour le modal)
            'home_shots': prediction.get('home_shots'),
            'away_shots': prediction.get('away_shots'),
            'home_corners': prediction.get('home_corners'),
            'away_corners': prediction.get('away_corners'),

            # Fourchettes par équipe (NOUVEAU - pour IA Deep Reasoning)
            'home_shots_min': prediction.get('home_shots_min'),
            'home_shots_max': prediction.get('home_shots_max'),
            'away_shots_min': prediction.get('away_shots_min'),
            'away_shots_max': prediction.get('away_shots_max'),
            'home_corners_min': prediction.get('home_corners_min'),
            'home_corners_max': prediction.get('home_corners_max'),
            'away_corners_min': prediction.get('away_corners_min'),
            'away_corners_max': prediction.get('away_corners_max'),

            # Prdictions TIRS (totaux)
            'shots': {
                'min': prediction['shots_min'],
                'max': prediction['shots_max'],
                'confidence': float(prediction['shots_confidence']),
                'message_min': f"Il y aura PLUS de {prediction['shots_min']} tirs",
                'message_max': f"Il y aura MOINS de {prediction['shots_max']} tirs",
                'analysis': prediction.get('analysis_shots'),  # Dtails complets
                'ai_reasoning': prediction.get('ai_reasoning_shots')
            },

            # Prdictions CORNERS (totaux)
            'corners': {
                'min': prediction['corners_min'],
                'max': prediction['corners_max'],
                'confidence': float(prediction['corners_confidence']),
                'message_min': f"Il y aura PLUS de {prediction['corners_min']} corners",
                'message_max': f"Il y aura MOINS de {prediction['corners_max']} corners",
                'analysis': prediction.get('analysis_corners'),  # Dtails complets
                'ai_reasoning': prediction.get('ai_reasoning_corners')
            },

            # Analyse IA globale (pour génération manuelle)
            'ai_reasoning': prediction.get('ai_reasoning_shots') or prediction.get('ai_reasoning_corners'),

            # Contexte
            'formations': {
                'home': prediction.get('home_formation'),
                'away': prediction.get('away_formation')
            },
            'weather': prediction.get('weather'),
            'rankings_used': prediction.get('rankings_used'),

            'created_at': created_at,
            'updated_at': updated_at
        }

    except Exception as e:
        return {
            'error': 'Erreur rcupration prdiction',
            'message': str(e),
            'match_id': match_id
        }


# =====================================================
# GÉNÉRATION MANUELLE DE PRÉDICTIONS
# =====================================================

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str
    home_formation: str
    away_formation: str
    home_players: Optional[str] = None
    away_players: Optional[str] = None
    bookmaker_props_text: Optional[str] = None

@app.post("/api/generate-prediction")
async def generate_prediction_manual(
    request: PredictionRequest,
    background_tasks: BackgroundTasks
):
    """
    🎯 GÉNÉRATION MANUELLE - Créer une prédiction avec compositions manuelles

    Permet à l'utilisateur de générer une prédiction en renseignant manuellement:
    - Noms des équipes
    - Formations (format: X-X-X ou X-X-X-X)
    - Joueurs titulaires (optionnel, séparés par virgules)

    Le traitement se fait en arrière-plan (30-60 secondes):
    1. Récupération données historiques
    2. Calcul Poisson
    3. IA Tactique (ajustements)
    4. IA Deep Reasoning (analyse complète)

    Returns:
        prediction_id: ID pour suivre la génération
        status: "en_cours"
    """
    try:
        import re
        from datetime import datetime

        # Validation des formations
        formation_pattern = r'^\d(-\d){1,3}$'
        if not re.match(formation_pattern, request.home_formation):
            return {
                'error': 'Formation domicile invalide',
                'detail': f'Format attendu: 4-3-3 ou 4-2-3-1. Reçu: {request.home_formation}'
            }

        if not re.match(formation_pattern, request.away_formation):
            return {
                'error': 'Formation extérieur invalide',
                'detail': f'Format attendu: 4-3-3 ou 4-2-3-1. Reçu: {request.away_formation}'
            }

        # Créer un match_id unique
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        match_id = f"MANUAL_{timestamp}_{request.home_team.replace(' ', '')}_{request.away_team.replace(' ', '')}"

        # Créer entrée en base avec status="en_cours"
        sqlite_db = get_sqlite_db()
        cursor = sqlite_db.conn.cursor()

        cursor.execute("""
            INSERT INTO match_predictions (
                match_id, home_team, away_team, league_code, match_date,
                home_formation, away_formation,
                shots_min, shots_max, shots_confidence,
                corners_min, corners_max, corners_confidence,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            request.home_team,
            request.away_team,
            "MANUAL",  # Code ligue spécial
            datetime.now().isoformat(),
            request.home_formation,
            request.away_formation,
            0, 0, 0.0,  # Valeurs temporaires
            0, 0, 0.0,
            "en_cours",  # STATUS
            datetime.now().isoformat()
        ))

        sqlite_db.conn.commit()
        prediction_id = cursor.lastrowid

        # Lancer le traitement en arrière-plan
        background_tasks.add_task(
            process_full_prediction,
            prediction_id=prediction_id,
            match_id=match_id,
            home_team=request.home_team,
            away_team=request.away_team,
            home_formation=request.home_formation,
            away_formation=request.away_formation,
            home_players=request.home_players,
            away_players=request.away_players,
            bookmaker_props_text=request.bookmaker_props_text
        )

        return {
            'success': True,
            'prediction_id': prediction_id,
            'match_id': match_id,
            'status': 'en_cours',
            'message': 'Prédiction en cours de génération (30-60 secondes)',
            'estimated_time_seconds': 45
        }

    except Exception as e:
        import traceback
        return {
            'error': 'Erreur lors de la création de la prédiction',
            'detail': str(e),
            'traceback': traceback.format_exc()
        }


async def process_full_prediction(
    prediction_id: int,
    match_id: str,
    home_team: str,
    away_team: str,
    home_formation: str,
    away_formation: str,
    home_players: Optional[str],
    away_players: Optional[str],
    bookmaker_props_text: Optional[str] = None
):
    """
    Traite une prédiction complète en arrière-plan

    Étapes:
    1. Récupérer données historiques (si disponibles)
    2. Calculer Poisson
    3. Appliquer IA Tactique
    4. Générer analyse Deep Reasoning
    5. Sauvegarder tout en DB
    """
    try:
        print(f"[PREDICTION {prediction_id}] Début du traitement...")

        # NORMALISATION DES NOMS D'ÉQUIPES (gérer les variations)
        home_team_original = home_team
        away_team_original = away_team
        home_team = normalize_team_name(home_team)
        away_team = normalize_team_name(away_team)

        if home_team != home_team_original or away_team != away_team_original:
            print(f"[PREDICTION {prediction_id}] Noms normalisés: '{home_team_original}' → '{home_team}', '{away_team_original}' → '{away_team}'")

        sqlite_db = get_sqlite_db()

        # ÉTAPE 0: Mise à jour des données (comme le CRON job)
        print(f"[PREDICTION {prediction_id}] Mise à jour des données CSV...")
        try:
            from automation.update_csv import run_full_update
            update_report = run_full_update('./data')
            print(f"[PREDICTION {prediction_id}] CSV mis à jour : {update_report['historical']['success']}/{update_report['historical']['total']} ligues")
        except Exception as e:
            print(f"[PREDICTION {prediction_id}] Erreur mise à jour CSV (utilisation des données existantes): {e}")

        # ÉTAPE 1: Déterminer la ligue (essayer de deviner depuis les noms)
        print(f"[PREDICTION {prediction_id}] Détection de la ligue...")
        league_code = "MANUAL"  # Par défaut
        soccerstats_code = "england"  # Par défaut

        # Essayer de détecter la ligue en cherchant les équipes dans les CSV
        for lcode, linfo in LEAGUES.items():
            try:
                csv_path = f"./data/{lcode}.csv"
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    if home_team in df['HomeTeam'].values or away_team in df['AwayTeam'].values:
                        league_code = lcode
                        soccerstats_code = SOCCERSTATS_CODES.get(lcode, "england")
                        print(f"[PREDICTION {prediction_id}] Ligue détectée: {linfo['name']} ({lcode})")
                        break
            except:
                pass

        # ÉTAPE 2: Utiliser le predictor existant (Poisson + IA Tactique)
        print(f"[PREDICTION {prediction_id}] Calcul Poisson + IA Tactique...")

        try:
            # Utiliser le predictor qui fait déjà tout le travail
            # Note: predict_match ne prend pas les formations en paramètres
            # Les formations sont utilisées uniquement par l'IA Deep Reasoning
            prediction_result = predictor.predict_match(
                home_team=home_team,
                away_team=away_team,
                league_code=soccerstats_code,
                match_date=datetime.now()
            )

            # Variable pour savoir si on a une analyse IA complète du predictor
            has_full_ai_analysis = False

            if 'error' in prediction_result:
                print(f"[PREDICTION {prediction_id}] Predictor error: {prediction_result['error']}")
                # Fallback sur valeurs par défaut
                home_shots = 15.0
                away_shots = 10.0
                home_corners = 6.0
                away_corners = 4.0
            else:
                # Extraire les résultats du predictor
                home_shots = prediction_result.get('predictions', {}).get('home', {}).get('shots', 15.0)
                away_shots = prediction_result.get('predictions', {}).get('away', {}).get('shots', 10.0)
                home_corners = prediction_result.get('predictions', {}).get('home', {}).get('corners', 6.0)
                away_corners = prediction_result.get('predictions', {}).get('away', {}).get('corners', 4.0)

                # Vérifier si le predictor a généré une analyse IA complète
                ai_reasoning = prediction_result.get('predictions', {}).get('ai_reasoning_shots', '')
                if ai_reasoning and len(ai_reasoning) > 500:  # Analyse complète = au moins 500 caractères
                    has_full_ai_analysis = True
                    print(f"[PREDICTION {prediction_id}] ✅ Analyse IA complète disponible ({len(ai_reasoning)} caractères)")

                print(f"[PREDICTION {prediction_id}] Résultats Poisson+IA: {home_team} {home_shots} tirs, {away_team} {away_shots} tirs")

        except Exception as e:
            print(f"[PREDICTION {prediction_id}] Erreur predictor: {e}")
            # Fallback sur valeurs par défaut
            home_shots = 15.0
            away_shots = 10.0
            home_corners = 6.0
            away_corners = 4.0
            has_full_ai_analysis = False

        # ÉTAPE 3: IA Deep Reasoning (analyse complète)
        print(f"[PREDICTION {prediction_id}] IA Deep Reasoning...")

        # Si le predictor a généré une analyse complète, l'utiliser
        if has_full_ai_analysis:
            print(f"[PREDICTION {prediction_id}] Utilisation de l'analyse complète du DynamicPredictor (7+ étapes)")
            reasoning_text = prediction_result['predictions']['ai_reasoning_shots']

            # Extraire les fourchettes depuis le predictor
            shots_range = {
                'min': prediction_result['predictions'].get('shots_min', int(home_shots + away_shots - 5)),
                'max': prediction_result['predictions'].get('shots_max', int(home_shots + away_shots + 5))
            }
            corners_range = {
                'min': prediction_result['predictions'].get('corners_min', int(home_corners + away_corners - 3)),
                'max': prediction_result['predictions'].get('corners_max', int(home_corners + away_corners + 3))
            }

            # Si l'utilisateur a fourni des propositions bookmaker, enrichir l'analyse
            if bookmaker_props_text and bookmaker_props_text.strip():
                print(f"[PREDICTION {prediction_id}] Enrichissement avec propositions bookmaker...")
                from core.ai_deep_reasoning import DeepReasoningAnalyzer
                analyzer = DeepReasoningAnalyzer()

                # Analyse supplémentaire focalisée sur le value betting
                context = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_formation': home_formation,
                    'away_formation': away_formation,
                    'home_players': [p.strip() for p in home_players.split(',')] if home_players else [],
                    'away_players': [p.strip() for p in away_players.split(',')] if away_players else [],
                    'home_stats': {'avg_shots': home_shots, 'avg_corners': home_corners},
                    'away_stats': {'avg_shots': away_shots, 'avg_corners': away_corners},
                    'league': LEAGUES.get(league_code, {}).get('name', 'Unknown'),
                    'match_date': datetime.now().isoformat(),
                    'bookmaker_propositions': bookmaker_props_text
                }
                value_betting_analysis = analyzer.analyze_match(context)

                # Combiner les analyses
                reasoning_text = reasoning_text + "\n\n" + "="*80 + "\n\n" + "🎯 ANALYSE VALUE BETTING (propositions bookmaker)\n\n" + value_betting_analysis.get('reasoning', '')

        else:
            # Sinon utiliser DeepReasoningAnalyzer (version simplifiée)
            print(f"[PREDICTION {prediction_id}] Utilisation de DeepReasoningAnalyzer (version simplifiée)")
            from core.ai_deep_reasoning import DeepReasoningAnalyzer
            analyzer = DeepReasoningAnalyzer()

            # Créer contexte enrichi pour l'IA
            context = {
                'home_team': home_team,
                'away_team': away_team,
                'home_formation': home_formation,
                'away_formation': away_formation,
                'home_players': [p.strip() for p in home_players.split(',')] if home_players else [],
                'away_players': [p.strip() for p in away_players.split(',')] if away_players else [],
                'home_stats': {'avg_shots': home_shots, 'avg_corners': home_corners},
                'away_stats': {'avg_shots': away_shots, 'avg_corners': away_corners},
                'league': LEAGUES.get(league_code, {}).get('name', 'Unknown'),
                'match_date': datetime.now().isoformat(),
                'bookmaker_propositions': bookmaker_props_text  # Texte brut des propositions
            }

            ai_analysis = analyzer.analyze_match(context)

            # Extraire résultats
            shots_range = ai_analysis.get('shots_range', {'min': int(home_shots + away_shots - 5), 'max': int(home_shots + away_shots + 5)})
            corners_range = ai_analysis.get('corners_range', {'min': int(home_corners + away_corners - 3), 'max': int(home_corners + away_corners + 3)})
            reasoning_text = ai_analysis.get('reasoning', f'Analyse de {home_team} vs {away_team}...')

        print(f"[PREDICTION {prediction_id}] IA Deep: Total tirs {shots_range}, corners {corners_range}")

        # ÉTAPE 4: Sauvegarder en base
        print(f"[PREDICTION {prediction_id}] Sauvegarde en DB...")

        # Utiliser la connexion existante
        cursor = sqlite_db.conn.cursor()

        cursor.execute("""
            UPDATE match_predictions
            SET
                shots_min = ?,
                shots_max = ?,
                shots_confidence = ?,
                corners_min = ?,
                corners_max = ?,
                corners_confidence = ?,
                home_shots = ?,
                away_shots = ?,
                home_corners = ?,
                away_corners = ?,
                home_shots_min = ?,
                home_shots_max = ?,
                away_shots_min = ?,
                away_shots_max = ?,
                home_corners_min = ?,
                home_corners_max = ?,
                away_corners_min = ?,
                away_corners_max = ?,
                ai_reasoning_shots = ?,
                ai_reasoning_corners = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            shots_range['min'],
            shots_range['max'],
            0.75,  # Confiance
            corners_range['min'],
            corners_range['max'],
            0.75,
            home_shots,
            away_shots,
            home_corners,
            away_corners,
            int(home_shots * 0.8),  # Fourchette -20%
            int(home_shots * 1.2),  # Fourchette +20%
            int(away_shots * 0.8),
            int(away_shots * 1.2),
            int(home_corners * 0.8),
            int(home_corners * 1.2),
            int(away_corners * 0.8),
            int(away_corners * 1.2),
            reasoning_text,
            reasoning_text,  # Même texte pour tirs et corners
            'completed',  # STATUS COMPLÉTÉ
            datetime.now().isoformat(),
            prediction_id
        ))

        sqlite_db.conn.commit()

        print(f"[PREDICTION {prediction_id}] ✅ Terminé avec succès!")

    except Exception as e:
        import traceback
        print(f"[PREDICTION {prediction_id}] ❌ ERREUR:")
        print(traceback.format_exc())

        # Marquer comme erreur en DB
        try:
            cursor = sqlite_db.conn.cursor()
            cursor.execute("""
                UPDATE match_predictions
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, ('error', datetime.now().isoformat(), prediction_id))
            sqlite_db.conn.commit()
        except:
            pass


# =====================================================
# ENDPOINTS AUTOMATISATION
# =====================================================

@app.post("/automation/update-data")
def automation_update_data():
    """
    🤖 AUTOMATISATION - Mise à jour des données (CSV historiques + fixtures)

    Appelé par Cron-job.org quotidiennement

    Actions:
    - Télécharge les CSV historiques depuis football-data.co.uk
    - Met à jour fixtures.csv

    Returns:
        Rapport de mise à jour
    """
    try:
        from automation.update_csv import run_full_update

        # Exécuter la mise à jour
        report = run_full_update('./data')

        return {
            'success': True,
            'timestamp': report['end_time'],
            'duration_seconds': report['duration_seconds'],
            'historical': {
                'total': report['historical']['total'],
                'success': report['historical']['success'],
                'failed': report['historical']['failed']
            },
            'fixtures': {
                'success': report['fixtures']['success']
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@app.post("/automation/generate-predictions")
def automation_generate_predictions(hours_ahead: int = Query(48, description="Nombre d'heures dans le futur")):
    """
    🤖 AUTOMATISATION - Génération des prédictions

    Appelé par Cron-job.org quotidiennement

    Actions:
    - Récupère les matchs des prochaines X heures
    - Génère les prédictions automatiquement
    - Sauvegarde dans SQLite + Supabase

    Args:
        hours_ahead: Nombre d'heures dans le futur (défaut: 48h)

    Returns:
        Rapport de génération
    """
    try:
        from automation.generate_predictions import run_auto_predictions

        # Exécuter la génération
        report = run_auto_predictions(hours_ahead)

        return {
            'success': True,
            'timestamp': report['timestamp'],
            'duration_seconds': report['duration_seconds'],
            'total_matches': report['total_matches'],
            'predictions_generated': report['predictions_generated'],
            'predictions_failed': report['predictions_failed']
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@app.post("/automation/fetch-lineups")
def automation_fetch_lineups(
    time_window_minutes: int = Query(30, description="Temps avant le match (défaut: 30 min)"),
    buffer_minutes: int = Query(5, description="Marge de tolérance (défaut: 5 min = fenêtre 25-35 min)")
):
    """
    🤖 AUTOMATISATION - Récupération des lineups via SerpAPI + FlashScore

    Appelé par cron job toutes les 15 minutes

    Actions:
    - Récupère tous les matchs à venir sans lineup
    - Filtre ceux qui commencent dans 30 min (± 5 min = fenêtre 25-35 min)
    - Appelle SerpAPI pour récupérer les lineups
    - Sauvegarde en DB pour ne JAMAIS re-fetcher

    Args:
        time_window_minutes: Temps avant le match (défaut: 30 min)
        buffer_minutes: Marge de tolérance (défaut: 5 min)

    Returns:
        Rapport de récupération
    """
    try:
        from automation.fetch_lineups import fetch_lineups_for_upcoming_matches

        # Exécuter la récupération
        report = fetch_lineups_for_upcoming_matches(time_window_minutes, buffer_minutes)

        return {
            'success': True,
            'timestamp': report['timestamp'],
            'duration_seconds': report['duration_seconds'],
            'total_matches_without_lineup': report['total_matches_without_lineup'],
            'matches_in_time_window': report['matches_in_time_window'],
            'lineups_fetched': report['lineups_fetched'],
            'lineups_failed': report['lineups_failed'],
            'results': report['results']
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@app.get("/automation/status")
def automation_status():
    """
    🤖 AUTOMATISATION - Statut du système

    Vérifie que tout fonctionne correctement

    Returns:
        Statut des différents composants
    """
    import os

    status = {
        'timestamp': datetime.now().isoformat(),
        'api': 'OK',
        'data_files': {},
        'database': {}
    }

    # Vérifier les fichiers CSV
    data_dir = './data'
    expected_files = [
        'E0_2526.csv', 'SP1_2526.csv', 'I1_2526.csv',
        'F1_2526.csv', 'D1_2526.csv', 'fixtures.csv'
    ]

    for file in expected_files:
        path = os.path.join(data_dir, file)
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            status['data_files'][file] = {
                'exists': True,
                'size': size,
                'last_modified': mtime.isoformat()
            }
        else:
            status['data_files'][file] = {
                'exists': False
            }

    # Vérifier la base de données
    try:
        from services.sqlite_database_service import SQLiteDatabaseService
        db = SQLiteDatabaseService()

        # Compter les prédictions
        count_query = "SELECT COUNT(*) as total FROM predictions"
        cursor = db.conn.cursor()
        cursor.execute(count_query)
        total = cursor.fetchone()[0]

        status['database']['sqlite'] = {
            'connected': True,
            'total_predictions': total
        }
    except Exception as e:
        status['database']['sqlite'] = {
            'connected': False,
            'error': str(e)
        }

    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
