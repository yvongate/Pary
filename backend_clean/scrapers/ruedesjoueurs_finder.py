#!/usr/bin/env python3
"""
Module pour trouver automatiquement les URLs de ruedesjoueurs.com
VERSION 2.0 : Scraping direct GRATUIT (sans SerpAPI)
Economie : ~0.005$ par recherche = 100% gratuit !
"""

from typing import Optional
import os
from scrapers import ruedesjoueurs_direct


def find_match_url(home_team: str, away_team: str, serpapi_key: Optional[str] = None,
                  league_code: str = None) -> Optional[str]:
    """
    Trouve l'URL d'un match sur ruedesjoueurs.com
    NOUVEAU: Scraping direct GRATUIT (sans SerpAPI)

    Args:
        home_team: Nom équipe domicile (ex: "Nice", "Liverpool")
        away_team: Nom équipe extérieur (ex: "Lorient", "Arsenal")
        serpapi_key: OBSOLETE - gardé pour compatibilité
        league_code: Code ligue (E0, SP1, I1, F1, D1) - REQUIS pour scraping direct

    Returns:
        URL complète du pronostic ou None si non trouvé

    Exemple:
        >>> find_match_url("Nice", "Lorient", league_code="F1")
        "https://www.ruedesjoueurs.com/pronostic/nice-lorient-4830661.html"
    """

    if not league_code:
        print("[WARNING] league_code non fourni - requis pour scraping direct")
        print("          Utilisez: E0=Premier League, SP1=Liga, I1=Serie A, F1=Ligue 1, D1=Bundesliga")
        return None

    # NOUVELLE METHODE : Scraping direct GRATUIT
    print(f"[RDJ] Scraping direct (gratuit) - recherche {home_team} vs {away_team}...")

    url = ruedesjoueurs_direct.find_match_url(home_team, away_team, league_code)

    return url


def get_match_analysis_auto(home_team: str, away_team: str, serpapi_key: Optional[str] = None,
                            league_code: str = None) -> Optional[dict]:
    """
    Trouve automatiquement l'URL puis scrape l'analyse
    NOUVEAU: Scraping direct GRATUIT (sans SerpAPI)

    Args:
        home_team: Nom équipe domicile
        away_team: Nom équipe extérieur
        serpapi_key: OBSOLETE - gardé pour compatibilité
        league_code: Code ligue (REQUIS)

    Returns:
        Dictionnaire avec analyse complète ou None
    """

    if not league_code:
        print("[WARNING] league_code non fourni")
        return None

    # NOUVELLE METHODE : Scraping direct complet
    print(f"[RDJ] Analyse complete (gratuit)...")

    analysis = ruedesjoueurs_direct.get_match_analysis_auto(home_team, away_team, league_code)

    if analysis:
        analysis["search_query"] = f"{home_team} vs {away_team}"
        analysis["found_via"] = "RDJ Direct Scraping (GRATUIT)"

    return analysis


if __name__ == "__main__":
    # Test
    print("="*70)
    print("TEST: Scraping Direct RDJ (GRATUIT)")
    print("="*70)

    # Test avec Strasbourg vs Lens
    result = get_match_analysis_auto(
        home_team="Strasbourg",
        away_team="Lens",
        league_code="F1"
    )

    if result:
        print("\n" + "="*70)
        print("ANALYSE RECUPEREE")
        print("="*70)
        print(f"\nURL: {result['url']}")
        print(f"Trouve via: {result['found_via']}")
        print(f"\nTexte complet: {len(result['full_text'])} caracteres")
        print(f"Joueurs absents: {result['injuries_text'][:200]}...")

        print(f"\n[SUCCESS] Scraping direct = 0€ (au lieu de SerpAPI payant)")
    else:
        print("\n[ERREUR] Aucune analyse trouvee")
