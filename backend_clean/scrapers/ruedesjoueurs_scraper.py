#!/usr/bin/env python3
"""
Scraper pour ruedesjoueurs.com - Analyses pré-match
"""

import tls_client
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, Any

session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.google.com/",
}


def clean_text(text: str) -> str:
    """Nettoie le texte en enlevant les pubs et espaces superflus"""
    # Enlever les pubs de bookmakers
    ads_patterns = [
        r'10€ GRATUITEMENT.*?RueDesJoueurs',
        r'Misez par exemple.*?débloquez',
        r'PAS DE PRESSION.*?compte bancaire.*?!!!',
        r'Inscrivez-vous chez.*?BONUS.*?!',
        r'⇒Cliquez ICI',
    ]

    for pattern in ads_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    # Nettoyer les espaces multiples
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    return text.strip()


def scrape_match_preview(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape une analyse de match depuis ruedesjoueurs.com

    Args:
        url: URL complète du pronostic (ex: https://www.ruedesjoueurs.com/pronostic/...)

    Returns:
        Dictionnaire avec toutes les données extraites ou None
    """
    try:
        print(f"[SCRAPING] {url}")

        response = session.get(url, headers=HEADERS, timeout_seconds=15)

        if response.status_code != 200:
            print(f"[ERROR] Status {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraire le titre
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Match inconnu"

        # Extraire les noms d'équipes depuis le titre "Pronostic Team1 - Team2"
        match = re.search(r'Pronostic\s+(.+?)\s*-\s*(.+)', title)
        home_team = match.group(1).strip() if match else None
        away_team = match.group(2).strip() if match else None

        # Trouver l'article principal
        article = soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in str(x).lower())

        if not article:
            print("[ERROR] Article content not found")
            return None

        # Extraire toutes les sections
        sections = {}
        current_section = "intro"
        current_text = []

        for elem in article.find_all(['h2', 'h3', 'p']):
            text = elem.get_text(strip=True)

            if elem.name in ['h2', 'h3']:
                # Nouvelle section
                if current_text:
                    sections[current_section] = "\n".join(current_text)
                current_section = text.lower()
                current_text = []
            else:
                # Contenu de la section
                if len(text) > 20:  # Filtrer les petits fragments
                    current_text.append(text)

        # Sauvegarder la dernière section
        if current_text:
            sections[current_section] = "\n".join(current_text)

        # Nettoyer toutes les sections
        for key in sections:
            sections[key] = clean_text(sections[key])

        # Structurer les données
        result = {
            "url": url,
            "title": title,
            "home_team": home_team,
            "away_team": away_team,
            "sections": sections,
            "full_text": clean_text("\n\n".join(sections.values())),
        }

        # Essayer d'extraire les compositions
        compositions_text = sections.get("les effectifs pour " + (home_team or "").lower() + " " + (away_team or "").lower(), "")
        if not compositions_text:
            # Chercher dans toutes les sections
            for key, value in sections.items():
                if "composition" in key or "effectif" in key or "titulaire" in key:
                    compositions_text = value
                    break

        result["lineups_text"] = compositions_text

        # Extraire les blessures/suspensions
        injuries = []
        for key, value in sections.items():
            if any(word in value.lower() for word in ["blessé", "suspendu", "absent", "forfait", "indisponible"]):
                injuries.append(value)

        result["injuries_text"] = "\n".join(injuries)

        return result

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test
    test_url = "https://www.ruedesjoueurs.com/pronostic/sunderland-fulham-4813642.html"

    data = scrape_match_preview(test_url)

    if data:
        print("\n" + "="*60)
        print(f"MATCH: {data['home_team']} vs {data['away_team']}")
        print("="*60)

        print(f"\n[SECTIONS FOUND]")
        for section_name in data['sections'].keys():
            print(f"  - {section_name}")

        print(f"\n[FULL TEXT] ({len(data['full_text'])} chars)")
        print(data['full_text'][:500] + "...\n")

        print(f"\n[INJURIES]")
        print(data['injuries_text'][:300] if data['injuries_text'] else "Aucune info")
