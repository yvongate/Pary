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
        Récupère les compositions via SerpAPI + FlashScore scraping

        Stratégie:
        1. SerpAPI cherche: "team1 vs team2 lineups flashscore"
        2. Extrait l'URL FlashScore des résultats
        3. Scrape FlashScore directement (formations toujours affichées)
        4. Retourne le contenu HTML/texte pour extraction formations

        Args:
            home_team: Équipe domicile
            away_team: Équipe extérieur
            date: Date du match (optionnel)

        Returns:
            {
                'raw_text': str,  # Contenu FlashScore ou fallback SerpAPI
                'flashscore_url': str,  # URL FlashScore si trouvée
                'home_team': str,
                'away_team': str,
                'source': 'flashscore' ou 'serpapi'
            }
        """
        if not self.api_key:
            print("[ERREUR] SERPAPI_KEY non configurée")
            return None

        # Construire la requête avec "flashscore"
        query = f"{home_team} vs {away_team} lineups flashscore"
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

            # ÉTAPE 1: Chercher l'URL FlashScore dans les résultats
            flashscore_url = self._extract_flashscore_url(data)

            if flashscore_url:
                print(f"[OK] URL FlashScore trouvée: {flashscore_url}")

                # ÉTAPE 2: Scraper FlashScore directement
                flashscore_content = self._scrape_flashscore(flashscore_url)

                if flashscore_content:
                    print(f"[OK] FlashScore scrapé ({len(flashscore_content)} caractères)")
                    return {
                        'raw_text': flashscore_content,
                        'flashscore_url': flashscore_url,
                        'home_team': home_team,
                        'away_team': away_team,
                        'source': 'flashscore'
                    }
                else:
                    print(f"[WARNING] Échec scraping FlashScore, fallback SerpAPI")

            # FALLBACK: Utiliser les snippets SerpAPI classiques
            print(f"[INFO] FlashScore non disponible, fallback sur snippets SerpAPI")
            raw_text = self._extract_raw_text(data)

            if raw_text:
                print(f"[OK] Texte lineup récupéré via SerpAPI ({len(raw_text)} caractères)")
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

    def _extract_flashscore_url(self, data: Dict) -> Optional[str]:
        """
        Extrait l'URL FlashScore des résultats SerpAPI

        Args:
            data: Réponse SerpAPI

        Returns:
            URL FlashScore ou None
        """
        organic_results = data.get('organic_results', [])

        for result in organic_results:
            link = result.get('link', '')
            # Chercher flashscore.com dans l'URL
            if 'flashscore.com' in link.lower():
                # Vérifier que c'est bien une page de match (contient /match/)
                if '/match/' in link:
                    return link

        return None

    def _scrape_flashscore(self, url: str) -> Optional[str]:
        """
        Scrape une page FlashScore avec Selenium pour récupérer les formations

        Args:
            url: URL FlashScore du match

        Returns:
            Contenu texte formaté ou None
        """
        try:
            # Essayer d'abord avec Selenium (méthode fiable)
            try:
                from scrapers.flashscore_selenium import get_flashscore_scraper

                scraper = get_flashscore_scraper()
                result = scraper.scrape_lineups(url)

                if result and result.get('raw_text'):
                    return result['raw_text']
                else:
                    print(f"[WARNING] Selenium n'a pas réussi, fallback sur scraping simple")

            except ImportError:
                print(f"[WARNING] Selenium non installé, fallback sur scraping simple")
            except Exception as e:
                print(f"[WARNING] Erreur Selenium: {e}, fallback sur scraping simple")

            # FALLBACK: Scraping simple (sans JavaScript)
            print(f"[INFO] Utilisation du scraping simple (sans formations)")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            return f"FlashScore URL: {url}\n\nContenu HTML (sans JavaScript):\n{response.text[:3000]}"

        except Exception as e:
            print(f"[ERREUR] Scraping FlashScore: {e}")
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
