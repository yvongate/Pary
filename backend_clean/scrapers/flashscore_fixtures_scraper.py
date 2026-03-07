"""
FlashScore Fixtures Scraper avec Selenium
Récupère les matchs à venir depuis FlashScore pour chaque championnat
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from typing import List, Dict, Optional
import time
from datetime import datetime


# Mapping codes vers URLs FlashScore
FLASHSCORE_FIXTURES_URLS = {
    'E0': 'https://www.flashscore.com/football/england/premier-league/fixtures/',
    'SP1': 'https://www.flashscore.com/football/spain/laliga/fixtures/',
    'I1': 'https://www.flashscore.com/football/italy/serie-a/fixtures/',
    'F1': 'https://www.flashscore.com/football/france/ligue-1/fixtures/',
    'D1': 'https://www.flashscore.com/football/germany/bundesliga/fixtures/',
}

# Noms des championnats
LEAGUE_NAMES = {
    'E0': 'Premier League',
    'SP1': 'La Liga',
    'I1': 'Serie A',
    'F1': 'Ligue 1',
    'D1': 'Bundesliga',
}


class FlashScoreFixturesScraper:
    """Scraper pour récupérer les fixtures depuis FlashScore avec Selenium"""

    def __init__(self):
        self.driver = None

    def _init_driver(self):
        """Initialise le driver Chrome headless"""
        if self.driver is not None:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Sur Railway/Linux, spécifier le binary chromium
        import os
        if os.path.exists('/usr/bin/chromium-browser'):
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            print(f"[INFO] Utilisation de chromium-browser système (/usr/bin/chromium-browser)")

        try:
            # Essayer d'utiliser chromedriver système (Railway/nixpacks.toml)
            if os.path.exists('/usr/bin/chromedriver'):
                service = Service('/usr/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print(f"[INFO] Chromedriver système initialisé (/usr/bin/chromedriver)")
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                print(f"[INFO] Chromedriver initialisé avec succès")
        except Exception as e1:
            # Fallback: webdriver-manager (local)
            print(f"[INFO] Fallback webdriver-manager: {e1}")
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def scrape_fixtures(self, league_code: str, days_ahead: int = 14) -> List[Dict]:
        """
        Scrape les fixtures d'un championnat depuis FlashScore

        Args:
            league_code: Code championnat (E0, SP1, I1, F1, D1)
            days_ahead: Nombre de jours à venir à récupérer

        Returns:
            Liste de matchs avec date, heure, équipes
        """
        if league_code not in FLASHSCORE_FIXTURES_URLS:
            print(f"[ERROR] Code championnat non supporté: {league_code}")
            return []

        url = FLASHSCORE_FIXTURES_URLS[league_code]

        try:
            self._init_driver()

            print(f"[FLASHSCORE] Chargement fixtures {league_code}: {url}")
            self.driver.get(url)

            # Attendre que React charge le contenu
            time.sleep(5)

            fixtures = []

            # Extraire tout le texte de la page
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text

            # Rechercher les patterns de matchs dans le texte
            lines = page_text.split('\n')

            i = 0
            while i < len(lines) - 2:
                line = lines[i].strip()
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                next_next_line = lines[i + 2].strip() if i + 2 < len(lines) else ""

                # Vérifier si c'est un pattern de match (date + heure au format "DD.MM. HH:MM")
                # Exemple: "14.03. 15:00"
                if '.' in next_next_line and ':' in next_next_line:
                    try:
                        # Séparer date et heure
                        parts = next_next_line.split()
                        if len(parts) >= 2:
                            date_part = parts[0]  # "14.03."
                            time_part = parts[1]  # "15:00"

                            # Vérifier que c'est bien une date valide (DD.MM.)
                            if date_part.count('.') >= 2:
                                # Vérifier que c'est bien une heure valide (HH:MM)
                                if ':' in time_part and len(time_part) == 5:
                                    home_team = line
                                    away_team = next_line

                                    # Filtrer les lignes invalides (titres, sections, etc.)
                                    skip_keywords = ['ROUND', 'Advertisement', 'FAVORITES', 'SCORES', 'NEWS',
                                                     'STANDINGS', 'RESULTS', 'FIXTURES', 'ODDS', 'SUMMARY']

                                    if (home_team and away_team and
                                        len(home_team) > 2 and len(away_team) > 2 and
                                        not any(kw in home_team.upper() for kw in skip_keywords) and
                                        not any(kw in away_team.upper() for kw in skip_keywords)):

                                        match_id = f"{league_code}_{home_team.replace(' ', '')}_{away_team.replace(' ', '')}"

                                        fixture = {
                                            'id': match_id,
                                            'league_code': league_code,
                                            'league': LEAGUE_NAMES.get(league_code, league_code),
                                            'home_team': home_team,
                                            'away_team': away_team,
                                            'time': time_part,
                                            'date': date_part.replace('.', '/').rstrip('/'),  # "14.03" -> "14/03"
                                            'status': 'SCHEDULED'
                                        }

                                        fixtures.append(fixture)
                                        print(f"[OK] {home_team} vs {away_team} - {date_part} {time_part}")

                                        i += 3  # Sauter les lignes déjà traitées
                                        continue
                    except (ValueError, IndexError):
                        pass

                i += 1

            print(f"[FLASHSCORE] {len(fixtures)} fixtures extraites pour {league_code}")
            return fixtures

        except Exception as e:
            print(f"[ERROR] FlashScore fixtures scraping {league_code}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_all_leagues(self, days_ahead: int = 14) -> List[Dict]:
        """
        Scrape les fixtures de tous les championnats supportés

        Args:
            days_ahead: Nombre de jours à venir

        Returns:
            Liste de tous les matchs
        """
        all_fixtures = []

        for league_code in FLASHSCORE_FIXTURES_URLS.keys():
            fixtures = self.scrape_fixtures(league_code, days_ahead)
            all_fixtures.extend(fixtures)
            time.sleep(2)  # Pause entre chaque championnat

        return all_fixtures

    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __del__(self):
        """Cleanup automatique"""
        self.close()


# Instance singleton
_scraper_instance = None

def get_flashscore_fixtures_scraper() -> FlashScoreFixturesScraper:
    """Retourne une instance singleton du scraper"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = FlashScoreFixturesScraper()
    return _scraper_instance


if __name__ == '__main__':
    # Test du scraper
    scraper = FlashScoreFixturesScraper()

    # Test sur Premier League
    print("\n" + "="*70)
    print("TEST: Scraping fixtures Premier League")
    print("="*70)

    fixtures = scraper.scrape_fixtures('E0', days_ahead=7)

    print(f"\n[RESULTAT] {len(fixtures)} matchs trouvés")

    if fixtures:
        print("\nPremiers 10 matchs:")
        for i, fixture in enumerate(fixtures[:10], 1):
            print(f"{i}. {fixture['home_team']} vs {fixture['away_team']} - {fixture['time']}")

    scraper.close()
