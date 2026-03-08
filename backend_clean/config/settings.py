"""
Configuration centralisée de l'application
Gère toutes les variables d'environnement
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuration de l'application"""
    
    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPINFRA_API_KEY: str = os.getenv("DEEPINFRA_API_KEY", "")  # Gardé en backup
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    FOOTBALL_DATA_API_TOKEN: str = os.getenv("FOOTBALL_DATA_API_TOKEN", "")
    
    # Base URLs
    FOOTBALL_DATA_BASE_URL: str = os.getenv("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4")
    
    # Database (Supabase)
    DATABASE_URL: str = (
        "postgresql://postgres:voicilemotdepassedepary"
        "@db.qibilvupnrqyxsoxpbze.supabase.co:5432/postgres"
    )
    
    # Paths
    DATA_DIR: str = "data"
    FIXTURES_CSV: str = "data/fixtures.csv"
    
    # URLs externes
    FOOTBALL_DATA_CSV_URL: str = "https://www.football-data.co.uk/fixtures.csv"
    
    # AI Configuration (Anthropic Claude)
    # Claude Sonnet 4 - Utilisé pour TOUTES les IA (textes + raisonnement profond)
    AI_MODEL: str = "claude-sonnet-4-6"
    AI_MAX_TOKENS: int = 1024  # Augmenté pour le raisonnement profond
    AI_TEMPERATURE: float = 0.7
    
    # Cron Configuration
    DATA_SYNC_INTERVAL_HOURS: int = 6
    PREDICTION_INTERVAL_HOURS: int = 1
    PREDICTION_LOOKAHEAD_HOURS: int = 2
    
    # League Mappings
    LEAGUES = {
        "E0": {"name": "Premier League", "country": "England", "soccerstats": "england"},
        "E1": {"name": "Championship", "country": "England", "soccerstats": "england"},
        "E2": {"name": "League One", "country": "England", "soccerstats": "england"},
        "E3": {"name": "League Two", "country": "England", "soccerstats": "england"},
        "D1": {"name": "Bundesliga", "country": "Germany", "soccerstats": "germany"},
        "SP1": {"name": "La Liga", "country": "Spain", "soccerstats": "spain"},
        "I1": {"name": "Serie A", "country": "Italy", "soccerstats": "italy"},
        "F1": {"name": "Ligue 1", "country": "France", "soccerstats": "france"},
        "F2": {"name": "Ligue 2", "country": "France", "soccerstats": "france"},
        "P1": {"name": "Primeira Liga", "country": "Portugal", "soccerstats": "portugal"},
    }
    
    # SoccerStats codes
    SOCCERSTATS_CODES = {
        "E0": "england",
        "E1": "england",
        "E2": "england",
        "E3": "england",
        "SP1": "spain",
        "I1": "italy",
        "F1": "france",
        "F2": "france",
        "D1": "germany",
        "P1": "portugal",
    }


# Instance globale
settings = Settings()
