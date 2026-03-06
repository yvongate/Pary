"""
Scraper FlashScore avec Selenium pour récupérer les formations
Les formations sont dans le DOM mais chargées via React/JavaScript
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict
import re
import time


class FlashScoreScraper:
    """Scraper FlashScore avec Selenium pour récupérer les vraies formations"""

    def __init__(self):
        self.driver = None

    def _init_driver(self):
        """Initialise le driver Selenium en mode headless"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Mode sans interface graphique
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Désactiver les logs verbeux
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        try:
            # Utiliser webdriver-manager pour télécharger ChromeDriver automatiquement
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return True
        except Exception as e:
            print(f"[ERREUR] Impossible d'initialiser Chrome: {e}")
            print("[INFO] Vérifiez que Chrome/Chromium est installé sur le système")
            return False

    def scrape_lineups(self, url: str) -> Optional[Dict]:
        """
        Scrape une page FlashScore pour récupérer les formations

        Args:
            url: URL FlashScore du match

        Returns:
            {
                'home_formation': str,  # Ex: "4-3-3"
                'away_formation': str,  # Ex: "4-2-3-1"
                'home_players': list,   # Noms joueurs domicile
                'away_players': list,   # Noms joueurs extérieur
                'raw_text': str        # Texte formaté pour l'IA
            }
        """
        if not self._init_driver():
            return None

        try:
            print(f"[SELENIUM] Chargement de {url}")
            self.driver.get(url)

            # Attendre que la page charge (max 15 secondes)
            wait = WebDriverWait(self.driver, 15)

            # Attendre que les formations soient visibles
            print("[SELENIUM] Attente du chargement React...")
            time.sleep(3)  # Laisser React initialiser

            # ÉTAPE 1: Récupérer les formations
            home_formation = None
            away_formation = None

            try:
                # Sélecteur pour les formations
                formation_elements = self.driver.find_elements(By.CSS_SELECTOR, '.wcl-headerSection_SGpOR span')

                if len(formation_elements) >= 3:
                    # formations[0] → "3 - 4 - 3" (domicile)
                    # formations[2] → "4 - 3 - 3" (extérieur)
                    home_formation_raw = formation_elements[0].text.strip()
                    away_formation_raw = formation_elements[2].text.strip()

                    # Nettoyer (enlever espaces: "3 - 4 - 3" → "3-4-3")
                    home_formation = home_formation_raw.replace(' ', '')
                    away_formation = away_formation_raw.replace(' ', '')

                    print(f"[OK] Formations trouvées: {home_formation} vs {away_formation}")
                else:
                    print(f"[WARNING] Formations non trouvées (éléments: {len(formation_elements)})")

            except Exception as e:
                print(f"[WARNING] Erreur extraction formations: {e}")

            # ÉTAPE 2: Récupérer les noms des joueurs
            home_players = []
            away_players = []

            try:
                # Joueurs domicile
                home_section = self.driver.find_element(By.CSS_SELECTOR, '.lf__formation:not(.lf__formationAway)')
                home_player_elements = home_section.find_elements(By.CSS_SELECTOR, '.lf__player')
                home_players = [p.text.strip() for p in home_player_elements if p.text.strip()]

                print(f"[OK] Joueurs domicile: {len(home_players)} trouvés")

            except Exception as e:
                print(f"[WARNING] Erreur extraction joueurs domicile: {e}")

            try:
                # Joueurs extérieur
                away_section = self.driver.find_element(By.CSS_SELECTOR, '.lf__formationAway')
                away_player_elements = away_section.find_elements(By.CSS_SELECTOR, '.lf__player')
                away_players = [p.text.strip() for p in away_player_elements if p.text.strip()]

                print(f"[OK] Joueurs extérieur: {len(away_players)} trouvés")

            except Exception as e:
                print(f"[WARNING] Erreur extraction joueurs extérieur: {e}")

            # ÉTAPE 3: Construire le texte formaté
            raw_text_parts = [
                f"FlashScore URL: {url}",
                ""
            ]

            if home_formation and away_formation:
                raw_text_parts.append(f"FORMATIONS:")
                raw_text_parts.append(f"  Home: {home_formation}")
                raw_text_parts.append(f"  Away: {away_formation}")
                raw_text_parts.append("")

            if home_players:
                raw_text_parts.append(f"HOME TEAM LINEUP ({len(home_players)} players):")
                raw_text_parts.extend([f"  - {player}" for player in home_players])
                raw_text_parts.append("")

            if away_players:
                raw_text_parts.append(f"AWAY TEAM LINEUP ({len(away_players)} players):")
                raw_text_parts.extend([f"  - {player}" for player in away_players])

            raw_text = "\n".join(raw_text_parts)

            result = {
                'home_formation': home_formation,
                'away_formation': away_formation,
                'home_players': home_players,
                'away_players': away_players,
                'raw_text': raw_text,
                'source': 'flashscore_selenium'
            }

            return result

        except Exception as e:
            print(f"[ERREUR] Scraping Selenium: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()


# Instance globale
_flashscore_scraper = None

def get_flashscore_scraper() -> FlashScoreScraper:
    """Retourne l'instance du scraper FlashScore"""
    global _flashscore_scraper
    if _flashscore_scraper is None:
        _flashscore_scraper = FlashScoreScraper()
    return _flashscore_scraper
