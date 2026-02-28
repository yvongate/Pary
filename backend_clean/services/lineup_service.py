"""
Service de récupération des compositions (lineups)
Utilise SerpAPI pour chercher les compositions sur Google
"""
import requests
from typing import Optional, Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings
import re


class LineupService:
    """Service de récupération des compositions via SerpAPI"""

    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"

    def get_lineups(self, home_team: str, away_team: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Récupère les compositions via SerpAPI

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur
            date: Date du match (optionnel)

        Returns:
            {
                'home_team': str,
                'away_team': str,
                'home_formation': str,
                'away_formation': str,
                'home_lineup': {
                    'formation': str,
                    'players': [
                        {'name': str, 'position': str, 'shirt_number': int, 'substitute': bool}
                    ]
                },
                'away_lineup': {...}
            }
        """
        if not self.api_key:
            print("[ERREUR] SERPAPI_KEY non configurée")
            return None

        # Construire la requête
        query = f"{home_team} vs {away_team} lineup"
        if date:
            query += f" {date}"

        print(f"[SERPAPI] Recherche: {query}")

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "num": 5,  # Nombre de résultats
                "gl": "fr",  # Localisation France
                "hl": "fr"   # Langue française
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Parser les résultats
            lineup_data = self._parse_search_results(data, home_team, away_team)

            if lineup_data:
                print(f"[OK] Compositions trouvées")
                return lineup_data
            else:
                print(f"[ATTENTION] Compositions non trouvées dans les résultats")
                return None

        except Exception as e:
            print(f"[ERREUR] SerpAPI lineup: {e}")
            return None

    def _parse_search_results(self, data: Dict, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Parse les résultats de recherche pour extraire les compositions

        Args:
            data: Réponse SerpAPI
            home_team: Équipe domicile
            away_team: Équipe extérieur

        Returns:
            Données des compositions ou None
        """
        # Chercher dans les sports_results (Google affiche souvent les compositions là)
        sports_results = data.get('sports_results')
        if sports_results:
            game_spotlight = sports_results.get('game_spotlight')
            if game_spotlight:
                return self._parse_game_spotlight(game_spotlight, home_team, away_team)

        # Chercher dans les organic_results
        organic_results = data.get('organic_results', [])
        for result in organic_results[:3]:  # Checker les 3 premiers résultats
            snippet = result.get('snippet', '')
            title = result.get('title', '')

            # Chercher des formations dans le snippet
            formations = self._extract_formations(snippet + " " + title)
            if formations:
                return {
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_formation': formations.get('home'),
                    'away_formation': formations.get('away'),
                    'source': result.get('link', 'serpapi')
                }

        return None

    def _parse_game_spotlight(self, game_spotlight: Dict, home_team: str, away_team: str) -> Optional[Dict]:
        """Parse le bloc game_spotlight de Google"""
        try:
            # Extraire les formations si disponibles
            home_formation = None
            away_formation = None

            # Google peut afficher les formations dans différents champs
            teams = game_spotlight.get('teams', [])
            if len(teams) >= 2:
                # Chercher les formations dans les données des équipes
                for team in teams:
                    formation = team.get('formation')
                    if formation:
                        if not home_formation:
                            home_formation = formation
                        elif not away_formation:
                            away_formation = formation

            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_formation': home_formation,
                'away_formation': away_formation,
                'source': 'google_sports'
            }

        except Exception as e:
            print(f"[ERREUR] Parse game_spotlight: {e}")
            return None

    def _extract_formations(self, text: str) -> Optional[Dict]:
        """
        Extrait les formations d'un texte (ex: "4-3-3", "5-4-1")

        Args:
            text: Texte à analyser

        Returns:
            {'home': '4-3-3', 'away': '5-4-1'} ou None
        """
        # Pattern pour détecter les formations (ex: 4-3-3, 4-4-2, etc.)
        formation_pattern = r'\b(\d-\d-\d|\d-\d-\d-\d)\b'
        formations = re.findall(formation_pattern, text)

        if len(formations) >= 2:
            return {
                'home': formations[0],
                'away': formations[1]
            }
        elif len(formations) == 1:
            return {
                'home': formations[0],
                'away': None
            }

        return None

    def get_lineups_simple(self, home_team: str, away_team: str) -> Dict:
        """
        Version simplifiée qui retourne au moins les formations même si les compositions complètes ne sont pas dispo

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur

        Returns:
            Dictionnaire avec au minimum home_team et away_team
        """
        lineups = self.get_lineups(home_team, away_team)

        if lineups:
            return lineups

        # Fallback: retourner structure minimale
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_formation': None,
            'away_formation': None,
            'source': 'unavailable'
        }


# Instance globale
_lineup_instance = None

def get_lineup_service() -> LineupService:
    """Retourne l'instance singleton du service de compositions"""
    global _lineup_instance
    if _lineup_instance is None:
        _lineup_instance = LineupService()
    return _lineup_instance
