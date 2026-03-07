"""
Service de récupération des compositions (lineups)
Utilise Bright Data Browser API pour scraper les formations depuis Google
"""
from typing import Optional, Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings

# Import du scraper Bright Data
try:
    from google_formation_scraper import get_formations
except ImportError:
    # Fallback si import échoue
    get_formations = None


class LineupService:
    """Service de récupération des compositions via Bright Data Browser API"""

    def __init__(self):
        # Plus besoin de SerpAPI
        pass

    def get_lineups(self, home_team: str, away_team: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Récupère les formations via Bright Data Browser API

        Stratégie:
        1. Convertit les noms d'équipes pour Google (mapping)
        2. Scrape Google Knowledge Graph avec Bright Data
        3. Extrait les formations (4-3-3, 5-3-2, etc.)

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur
            date: Date du match (optionnel, non utilisé)

        Returns:
            {
                'home_formation': str,  # ex: "4-3-3"
                'away_formation': str,  # ex: "4-4-2"
                'home_team': str,
                'away_team': str,
                'source': 'google_brightdata',
                'success': bool
            }
        """
        if not get_formations:
            print("[ERREUR] google_formation_scraper non disponible")
            return {
                'home_formation': None,
                'away_formation': None,
                'home_team': home_team,
                'away_team': away_team,
                'source': 'unavailable',
                'success': False
            }

        print(f"[Lineup Service] Récupération formations: {home_team} vs {away_team}")

        try:
            # Appeler le scraper Bright Data
            result = get_formations(home_team, away_team)

            if result and result.get('success'):
                print(f"[Lineup Service] OK - {home_team}: {result.get('home_formation')} | {away_team}: {result.get('away_formation')}")
                return {
                    'home_formation': result.get('home_formation'),
                    'away_formation': result.get('away_formation'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'source': 'google_brightdata',
                    'success': True
                }
            else:
                print(f"[Lineup Service] ERREUR - Formations non trouvées")
                return {
                    'home_formation': None,
                    'away_formation': None,
                    'home_team': home_team,
                    'away_team': away_team,
                    'source': 'google_brightdata',
                    'success': False
                }

        except Exception as e:
            print(f"[Lineup Service] ERREUR: {e}")
            return {
                'home_formation': None,
                'away_formation': None,
                'home_team': home_team,
                'away_team': away_team,
                'source': 'google_brightdata',
                'success': False,
                'error': str(e)
            }


    def get_lineups_simple(self, home_team: str, away_team: str) -> Dict:
        """
        Version simplifiée avec fallback

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur

        Returns:
            Dictionnaire avec formations ou structure minimale
        """
        lineups = self.get_lineups(home_team, away_team)

        if lineups and lineups.get('success'):
            return lineups

        # Fallback: retourner structure minimale
        return {
            'home_formation': None,
            'away_formation': None,
            'home_team': home_team,
            'away_team': away_team,
            'source': 'unavailable',
            'success': False
        }


# Instance globale
_lineup_instance = None

def get_lineup_service() -> LineupService:
    """Retourne l'instance singleton du service de compositions"""
    global _lineup_instance
    if _lineup_instance is None:
        _lineup_instance = LineupService()
    return _lineup_instance
