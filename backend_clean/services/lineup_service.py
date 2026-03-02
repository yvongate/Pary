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
        Récupère les compositions via SerpAPI et retourne le TEXTE BRUT

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur
            date: Date du match (optionnel)

        Returns:
            {
                'raw_text': str,  # Texte brut des résultats SerpAPI
                'home_team': str,
                'away_team': str,
                'source': 'serpapi'
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

            # Extraire le TEXTE BRUT de tous les résultats pertinents
            raw_text = self._extract_raw_text(data)

            if raw_text:
                print(f"[OK] Texte lineup récupéré ({len(raw_text)} caractères)")
                return {
                    'raw_text': raw_text,
                    'home_team': home_team,
                    'away_team': away_team,
                    'source': 'serpapi'
                }
            else:
                print(f"[ATTENTION] Aucun texte lineup trouvé")
                return None

        except Exception as e:
            print(f"[ERREUR] SerpAPI lineup: {e}")
            return None

    def _extract_raw_text(self, data: Dict) -> Optional[str]:
        """
        Extrait le TEXTE BRUT de tous les résultats SerpAPI pertinents

        Args:
            data: Réponse SerpAPI complète

        Returns:
            Texte brut concaténé ou None
        """
        raw_text_parts = []

        # 1. Answer box (souvent les meilleures infos)
        answer_box = data.get('answer_box')
        if answer_box:
            if answer_box.get('title'):
                raw_text_parts.append(f"TITLE: {answer_box['title']}")
            if answer_box.get('answer'):
                raw_text_parts.append(f"ANSWER: {answer_box['answer']}")
            if answer_box.get('snippet'):
                raw_text_parts.append(f"SNIPPET: {answer_box['snippet']}")

        # 2. Sports results (Google affiche souvent les lineups ici)
        sports_results = data.get('sports_results')
        if sports_results:
            game_spotlight = sports_results.get('game_spotlight')
            if game_spotlight:
                raw_text_parts.append(f"GAME SPOTLIGHT: {str(game_spotlight)[:1000]}")

        # 3. Organic results (premiers résultats Google)
        organic_results = data.get('organic_results', [])
        for i, result in enumerate(organic_results[:3], 1):  # Top 3 résultats
            if result.get('title'):
                raw_text_parts.append(f"RESULT {i} TITLE: {result['title']}")
            if result.get('snippet'):
                raw_text_parts.append(f"RESULT {i} SNIPPET: {result['snippet']}")

        # 4. Knowledge graph (si présent)
        knowledge_graph = data.get('knowledge_graph')
        if knowledge_graph and knowledge_graph.get('description'):
            raw_text_parts.append(f"KNOWLEDGE: {knowledge_graph['description']}")

        if raw_text_parts:
            return "\n\n".join(raw_text_parts)

        return None

    def get_lineups_simple(self, home_team: str, away_team: str) -> Dict:
        """
        Version simplifiée avec fallback

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur

        Returns:
            Dictionnaire avec texte brut ou structure minimale
        """
        lineups = self.get_lineups(home_team, away_team)

        if lineups:
            return lineups

        # Fallback: retourner structure minimale
        return {
            'raw_text': None,
            'home_team': home_team,
            'away_team': away_team,
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
