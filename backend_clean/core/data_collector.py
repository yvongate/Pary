"""
Data Collector - Gathers all data from various sources for predictions
Integrates: soccerstats, weather, lineups, odds, context, H2H, stadium
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json

# Import our scrapers
try:
    import scrapers.soccerstats_overview
    import scrapers.soccerstats_working
except ImportError:
    print("Warning: soccerstats modules not found")


class DataCollector:
    """
    Collects and aggregates data from all available sources
    """

    # Mapping codes CSV → codes soccerstats.com pour scraping
    SOCCERSTATS_CODES = {
        "E0": "england",
        "F1": "france",
        "SP1": "spain",
        "I1": "italy",
        "P1": "portugal",
        "B1": "belgium",
        "T1": "turkey",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: API-FOOTBALL key for odds/lineups (optional)
        """
        self.api_key = api_key
        self.cache = {}  # Simple cache to avoid repeated API calls

    # === RANKINGS (from soccerstats.com) ===

    def get_rankings(self, league_code: str = "england", use_cache: bool = True) -> Optional[Dict]:
        """
        Get all 12 classements from soccerstats.com

        Returns:
            {
                'standings': [...],
                'form_last_8': [...],
                'home': [...],
                'away': [...],
                'offence': [...],
                'defence': [...],
                'offence_last_8': [...],
                'defence_last_8': [...],
                'offence_home': [...],
                'defence_home': [...],
                'offence_away': [...],
                'defence_away': [...]
            }
        """
        cache_key = f"rankings_{league_code}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Convertir code ligue CSV (F1) → code soccerstats (france)
            soccerstats_league = self.SOCCERSTATS_CODES.get(league_code, league_code)

            rankings = soccerstats_overview.get_tables_overview(soccerstats_league)
            if rankings:
                self.cache[cache_key] = rankings
            return rankings
        except Exception as e:
            print(f"Error getting rankings: {e}")
            return None

    def get_team_rank(self, team_name: str, ranking_type: str, league_code: str = "england") -> int:
        """
        Get specific ranking for a team

        Args:
            team_name: Team name
            ranking_type: 'standings', 'form_last_8', 'offence', 'defence', etc.
            league_code: League code

        Returns:
            Position (1-20) or 10 (middle) if not found
        """
        rankings = self.get_rankings(league_code)
        if not rankings or ranking_type not in rankings:
            return 10

        for team in rankings[ranking_type]:
            if team['team'].lower() == team_name.lower():
                return team['position']

        return 10  # Default middle position

    # === WEATHER (from wttr.in) ===

    def get_weather(self, city: str, match_date: Optional[datetime] = None) -> Dict:
        """
        Get weather forecast for match location

        Args:
            city: City name (e.g., "London", "Manchester")
            match_date: Date of match (if None, uses today)

        Returns:
            {
                'wind_speed': float (km/h),
                'precipitation': float (mm),
                'temperature': float (C),
                'condition': str
            }
        """
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # Get current weather or forecast
                if match_date and match_date.date() > datetime.now().date():
                    # Use forecast (if available)
                    weather_data = data['weather'][0] if 'weather' in data else data['current_condition'][0]
                else:
                    # Use current conditions
                    weather_data = data['current_condition'][0]

                return {
                    'wind_speed': float(weather_data.get('windspeedKmph', 10)),
                    'precipitation': float(weather_data.get('precipMM', 0)),
                    'temperature': float(weather_data.get('temp_C', 15)),
                    'condition': weather_data.get('weatherDesc', [{}])[0].get('value', 'Clear')
                }
        except Exception as e:
            print(f"Error getting weather: {e}")

        # Return default values
        return {
            'wind_speed': 10,
            'precipitation': 0,
            'temperature': 15,
            'condition': 'Unknown'
        }

    # === LINEUPS (from API-FOOTBALL or SofaScore) ===

    def get_lineup_features(self, home_team: str, away_team: str, match_id: Optional[int] = None) -> Dict:
        """
        Get lineup features for home team

        Args:
            home_team: Home team name
            away_team: Away team name
            match_id: Optional match ID from API

        Returns:
            {
                'offensive_formation': bool,  # 4-3-3, 4-2-3-1, etc.
                'num_wingers': int,  # 0-2
                'key_striker_present': bool,
                'lineup_strength': float  # 0-1
            }
        """
        # TODO: Integrate with actual lineup API when available
        # For now, return estimated values based on team rankings

        # Placeholder logic - replace with actual API call
        return {
            'offensive_formation': True,  # Assume offensive at home
            'num_wingers': 2,
            'key_striker_present': True,
            'lineup_strength': 0.75
        }

    # === ODDS (from API-FOOTBALL) ===

    def get_odds_features(self, home_team: str, away_team: str, match_id: Optional[int] = None) -> Dict:
        """
        Get betting odds features

        Args:
            home_team: Home team name
            away_team: Away team name
            match_id: Optional match ID

        Returns:
            {
                'win_probability': float,  # 0-1
                'over_2_5_probability': float  # 0-1
            }
        """
        if not self.api_key:
            # Return neutral probabilities
            return {
                'win_probability': 0.5,
                'over_2_5_probability': 0.5
            }

        # TODO: Implement actual API-FOOTBALL odds fetching
        # For now, return placeholder values
        return {
            'win_probability': 0.55,
            'over_2_5_probability': 0.52
        }

    # === CONTEXT ===

    def get_context_features(self, home_team: str, away_team: str,
                            league_code: str = "england",
                            match_importance: Optional[int] = None) -> Dict:
        """
        Get contextual features for the match

        Args:
            home_team: Home team name
            away_team: Away team name
            league_code: League code
            match_importance: Optional importance (1-10)

        Returns:
            {
                'match_importance': int,  # 1-10
                'days_rest': int,  # Days since last match
                'key_injuries': int,  # Number of key injuries
                'morale': int,  # 1-10 based on recent form
                'home_atmosphere': int  # 1-10 based on stadium/fans
            }
        """
        # Get team context from soccerstats
        try:
            # Convertir code ligue CSV (F1) → code soccerstats (france)
            soccerstats_league = self.SOCCERSTATS_CODES.get(league_code, league_code)

            team_context = soccerstats_working.get_team_context(home_team, soccerstats_league)
            if team_context:
                # Calculate morale from position and gaps
                position = team_context.get('position', 10)
                morale = 10 - (position - 1) * 0.3  # Higher position = better morale
                morale = max(1, min(10, morale))
            else:
                morale = 5
        except Exception:
            morale = 5

        return {
            'match_importance': match_importance or 5,
            'days_rest': 7,  # Default weekly schedule
            'key_injuries': 0,  # TODO: Get from lineup API
            'morale': int(morale),
            'home_atmosphere': 7  # TODO: Get from stadium data
        }

    # === H2H (Head to Head) ===

    def get_h2h_features(self, home_team: str, away_team: str,
                        league_code: str = "england") -> Dict:
        """
        Get historical H2H statistics

        Args:
            home_team: Home team name
            away_team: Away team name
            league_code: League code

        Returns:
            {
                'avg_shots_h2h': float,
                'avg_corners_h2h': float,
                'avg_goals_h2h': float
            }
        """
        # TODO: Load from historical database
        # For now, return neutral averages
        return {
            'avg_shots_h2h': 12,
            'avg_corners_h2h': 6,
            'avg_goals_h2h': 1.5
        }

    # === STADIUM ===

    def get_stadium_features(self, home_team: str) -> Dict:
        """
        Get stadium characteristics

        Args:
            home_team: Home team name

        Returns:
            {
                'pitch_quality': int,  # 1-10
                'is_covered': bool  # Covered/retractable roof
            }
        """
        # Stadium mapping (extend as needed)
        stadium_data = {
            'tottenham': {'pitch_quality': 10, 'is_covered': True},
            'arsenal': {'pitch_quality': 9, 'is_covered': False},
            'manchester city': {'pitch_quality': 10, 'is_covered': False},
            'liverpool': {'pitch_quality': 9, 'is_covered': False},
            'chelsea': {'pitch_quality': 9, 'is_covered': False},
            'manchester united': {'pitch_quality': 9, 'is_covered': False},
        }

        team_key = home_team.lower()
        return stadium_data.get(team_key, {
            'pitch_quality': 8,
            'is_covered': False
        })

    # === CITY MAPPING ===

    def get_team_city(self, team_name: str) -> str:
        """
        Map team name to city for weather lookup

        Args:
            team_name: Team name

        Returns:
            City name
        """
        city_mapping = {
            # Premier League (Angleterre)
            'arsenal': 'London',
            'chelsea': 'London',
            'tottenham': 'London',
            'west ham': 'London',
            'crystal palace': 'London',
            'fulham': 'London',
            'brentford': 'London',
            'manchester city': 'Manchester',
            'man city': 'Manchester',
            'manchester united': 'Manchester',
            'man united': 'Manchester',
            'liverpool': 'Liverpool',
            'everton': 'Liverpool',
            'newcastle': 'Newcastle',
            'aston villa': 'Birmingham',
            'wolverhampton': 'Wolverhampton',
            'wolves': 'Wolverhampton',
            'brighton': 'Brighton',
            'southampton': 'Southampton',
            'bournemouth': 'Bournemouth',
            'nottingham forest': 'Nottingham',
            "nott'm forest": 'Nottingham',
            'leicester': 'Leicester',
            'leeds': 'Leeds',

            # Ligue 1 (France)
            'paris sg': 'Paris',
            'psg': 'Paris',
            'marseille': 'Marseille',
            'lyon': 'Lyon',
            'lille': 'Lille',
            'monaco': 'Monaco',
            'nice': 'Nice',
            'rennes': 'Rennes',
            'lens': 'Lens',
            'nantes': 'Nantes',
            'strasbourg': 'Strasbourg',
            'brest': 'Brest',
            'montpellier': 'Montpellier',
            'toulouse': 'Toulouse',
            'reims': 'Reims',
            'lorient': 'Lorient',
            'auxerre': 'Auxerre',
            'angers': 'Angers',
            'le havre': 'Le Havre',
            'metz': 'Metz',
            'paris fc': 'Paris',

            # La Liga (Espagne)
            'barcelona': 'Barcelona',
            'real madrid': 'Madrid',
            'atletico madrid': 'Madrid',
            'ath madrid': 'Madrid',
            'sevilla': 'Sevilla',
            'valencia': 'Valencia',
            'villarreal': 'Villarreal',
            'athletic bilbao': 'Bilbao',
            'ath bilbao': 'Bilbao',
            'real sociedad': 'San Sebastian',
            'sociedad': 'San Sebastian',
            'real betis': 'Sevilla',
            'betis': 'Sevilla',
            'espanyol': 'Barcelona',
            'espanol': 'Barcelona',
            'celta vigo': 'Vigo',
            'celta': 'Vigo',
            'getafe': 'Madrid',
            'osasuna': 'Pamplona',
            'alaves': 'Vitoria',
            'mallorca': 'Palma',
            'cadiz': 'Cadiz',
            'elche': 'Elche',
            'granada': 'Granada',
            'rayo vallecano': 'Madrid',
            'vallecano': 'Madrid',
            'girona': 'Girona',
            'almeria': 'Almeria',

            # Serie A (Italie)
            'inter': 'Milan',
            'milan': 'Milan',
            'juventus': 'Turin',
            'roma': 'Rome',
            'lazio': 'Rome',
            'napoli': 'Naples',
            'atalanta': 'Bergamo',
            'fiorentina': 'Florence',
            'torino': 'Turin',
            'bologna': 'Bologna',
            'sassuolo': 'Sassuolo',
            'udinese': 'Udine',
            'sampdoria': 'Genoa',
            'verona': 'Verona',
            'cagliari': 'Cagliari',
            'empoli': 'Empoli',
            'spezia': 'La Spezia',
            'salernitana': 'Salerno',
            'lecce': 'Lecce',
            'monza': 'Monza',
            'cremonese': 'Cremona',

            # Bundesliga (Allemagne)
            'bayern munich': 'Munich',
            'bayern': 'Munich',
            'dortmund': 'Dortmund',
            'rb leipzig': 'Leipzig',
            'leipzig': 'Leipzig',
            'leverkusen': 'Leverkusen',
            'frankfurt': 'Frankfurt',
            'wolfsburg': 'Wolfsburg',
            'freiburg': 'Freiburg',
            'union berlin': 'Berlin',
            'stuttgart': 'Stuttgart',
            'monchengladbach': 'Monchengladbach',
            "m'gladbach": 'Monchengladbach',
            'hoffenheim': 'Hoffenheim',
            'mainz': 'Mainz',
            'augsburg': 'Augsburg',
            'werder bremen': 'Bremen',
            'hertha': 'Berlin',
            'schalke': 'Gelsenkirchen',
            'bochum': 'Bochum',

            # Primeira Liga (Portugal)
            'benfica': 'Lisbon',
            'porto': 'Porto',
            'sporting': 'Lisbon',
            'sp lisbon': 'Lisbon',
            'braga': 'Braga',
            'guimaraes': 'Guimaraes',
            'boavista': 'Porto',
            'maritimo': 'Funchal',
            'pacos ferreira': 'Pacos de Ferreira',
            'gil vicente': 'Barcelos',
            'famalicao': 'Famalicao',
            'arouca': 'Arouca',
            'vizela': 'Vizela',
            'casa pia': 'Lisbon',
            'estoril': 'Estoril',
            'chaves': 'Chaves',
            'portimonense': 'Portimao',
            'rio ave': 'Vila do Conde',
            'nacional': 'Funchal',
            'avs': 'Vila das Aves',

            # Jupiler Pro League (Belgique)
            'club brugge': 'Bruges',
            'anderlecht': 'Brussels',
            'antwerp': 'Antwerp',
            'genk': 'Genk',
            'gent': 'Ghent',
            'union sg': 'Brussels',
            'st. gilloise': 'Brussels',
            'charleroi': 'Charleroi',
            'standard liege': 'Liege',
            'kortrijk': 'Kortrijk',
            'mechelen': 'Mechelen',
            'oostende': 'Ostend',
            'leuven': 'Leuven',
            'eupen': 'Eupen',
            'seraing': 'Seraing',
            'cercle brugge': 'Bruges',
            'waregem': 'Waregem',
            'dender': 'Denderleeuw',

            # Super Lig (Turquie)
            'galatasaray': 'Istanbul',
            'fenerbahce': 'Istanbul',
            'besiktas': 'Istanbul',
            'trabzonspor': 'Trabzon',
            'basaksehir': 'Istanbul',
            'antalyaspor': 'Antalya',
            'konyaspor': 'Konya',
            'sivasspor': 'Sivas',
            'alanyaspor': 'Alanya',
            'kasimpasa': 'Istanbul',
            'gaziantep': 'Gaziantep',
            'hatayspor': 'Hatay',
            'adana demirspor': 'Adana',
            'kayserispor': 'Kayseri',
            'goztepe': 'Izmir',
            'goztep': 'Izmir',
            'rizespor': 'Rize',
            'giresunspor': 'Giresun',
            'fatih karagumruk': 'Istanbul',
            'istanbulspor': 'Istanbul',
            'pendikspor': 'Istanbul',
            'samsunspor': 'Samsun',
            'genclerbirligi': 'Ankara',
            'eyupspor': 'Istanbul',
        }

        team_key = team_name.lower()
        # Essayer d'abord match exact, sinon chercher si le nom d'équipe contient la clé
        if team_key in city_mapping:
            return city_mapping[team_key]

        # Fallback: chercher si la clé contient le nom de l'équipe
        for key, city in city_mapping.items():
            if key in team_key or team_key in key:
                return city

        return 'London'  # Default to London si vraiment rien trouvé

    # === COMPLETE DATA COLLECTION ===

    def collect_all_data(self, home_team: str, away_team: str,
                        league_code: str = "england",
                        match_date: Optional[datetime] = None,
                        match_importance: Optional[int] = None) -> Dict:
        """
        Collect ALL data for a match from all sources

        Args:
            home_team: Home team name
            away_team: Away team name
            league_code: League code (england, spain, etc.)
            match_date: Date of match
            match_importance: Match importance (1-10)

        Returns:
            Complete feature dict ready for prediction_engine
        """
        print(f"\n Collecting data for {home_team} vs {away_team}...")

        # Get rankings
        print("   Fetching rankings...")
        rankings = self.get_rankings(league_code)

        if not rankings:
            print("    Warning: Could not fetch rankings")
            return {}

        # Extract home team attack rankings
        home_ranks = {}
        away_ranks = {}

        for table_name, teams in rankings.items():
            for team in teams:
                if team['team'].lower() == home_team.lower():
                    home_ranks[table_name] = team['position']
                if team['team'].lower() == away_team.lower():
                    away_ranks[table_name] = team['position']

        # Get weather
        print("    Fetching weather...")
        city = self.get_team_city(home_team)
        weather = self.get_weather(city, match_date)

        # Get lineups
        print("   Fetching lineup features...")
        lineups = self.get_lineup_features(home_team, away_team)

        # Get odds
        print("   Fetching odds...")
        odds = self.get_odds_features(home_team, away_team)

        # Get context
        print("   Fetching context...")
        context = self.get_context_features(home_team, away_team, league_code, match_importance)

        # Get H2H
        print("   Fetching H2H history...")
        h2h = self.get_h2h_features(home_team, away_team, league_code)

        # Get stadium
        print("    Fetching stadium data...")
        stadium = self.get_stadium_features(home_team)

        # Build complete feature dict
        features = {
            # Home team attack rankings
            'rank_attack': home_ranks.get('offence', 10),
            'rank_attack_home': home_ranks.get('offence_home', 10),
            'rank_attack_away': home_ranks.get('offence_away', 10),
            'rank_attack_last8': home_ranks.get('offence_last_8', 10),
            'rank_form': home_ranks.get('form_last_8', 10),
            'rank_home': home_ranks.get('home', 10),
            'rank_offence': home_ranks.get('offence', 10),
            'rank_offence_home': home_ranks.get('offence_home', 10),
            'rank_offence_last8': home_ranks.get('offence_last_8', 10),

            # Home team stats (estimated)
            'goals_for_per_game': 2.0 - (home_ranks.get('offence', 10) - 1) * 0.1,
            'form_percentage': 1.0 - (home_ranks.get('form_last_8', 10) - 1) * 0.05,
            'points_per_game_home': 2.5 - (home_ranks.get('home', 10) - 1) * 0.1,

            # Away team defence rankings
            'opponent_rank_defence': away_ranks.get('defence', 10),
            'opponent_rank_defence_away': away_ranks.get('defence_away', 10),
            'opponent_rank_defence_last8': away_ranks.get('defence_last_8', 10),
            'opponent_goals_against_per_game': 1.0 + (away_ranks.get('defence', 10) - 1) * 0.1,

            # Weather
            **weather,

            # Lineups
            **lineups,

            # Odds
            **odds,

            # Context
            **context,

            # H2H
            **h2h,

            # Stadium
            **stadium
        }

        print("   Data collection complete!\n")
        return features


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    # Example: Collect data for a match
    collector = DataCollector()

    data = collector.collect_all_data(
        home_team="Tottenham",
        away_team="Arsenal",
        league_code="england",
        match_importance=9  # Derby match
    )

    print("Collected features:")
    for key, value in data.items():
        print(f"  {key}: {value}")
