"""
Google Formation Scraper - VERSION SIMPLE
Scrape UNIQUEMENT les formations (4-3-3, 5-3-2, etc.) depuis Google
Utilise Bright Data Browser API
"""
import asyncio
from playwright.async_api import async_playwright
import re
from typing import Optional, Dict
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(__file__))
from config.team_names_mapping import get_google_team_names

load_dotenv()

# Configuration Bright Data
CUSTOMER_ID = os.getenv("BRIGHTDATA_CUSTOMER_ID", "hl_d76a8bf0")
BROWSER_API_ZONE = os.getenv("BRIGHTDATA_BROWSER_API_ZONE", "google_scraper")
BROWSER_API_PASSWORD = os.getenv("BRIGHTDATA_BROWSER_API_PASSWORD", "cw407utbgsjj")

AUTH = f"brd-customer-{CUSTOMER_ID}-zone-{BROWSER_API_ZONE}:{BROWSER_API_PASSWORD}"
ENDPOINT = f"wss://{AUTH}@brd.superproxy.io:9222"


async def scrape_formations_async(home_team: str, away_team: str) -> Optional[Dict]:
    """
    Scrape les formations depuis Google

    Args:
        home_team: Équipe domicile (ex: "PSG")
        away_team: Équipe extérieur (ex: "Monaco")

    Returns:
        {
            'home_formation': str,  # ex: "4-3-3"
            'away_formation': str,  # ex: "4-4-2"
            'success': bool
        }
    """

    async with async_playwright() as p:
        browser = None
        try:
            print(f"[Formation Scraper] {home_team} vs {away_team}")

            # Convertir les noms d'équipes pour Google
            home_google, away_google = get_google_team_names(home_team, away_team)
            if home_google != home_team or away_google != away_team:
                print(f"[Formation Scraper] Mapping: {home_team} -> {home_google}, {away_team} -> {away_google}")

            # Connexion Browser API
            browser = await p.chromium.connect_over_cdp(ENDPOINT)
            page = await browser.new_page()

            # Navigation Google avec les noms mappés
            query = f"{home_google} vs {away_google}"
            await page.goto(f"https://www.google.com/search?q={query}&hl=fr", timeout=120000)
            await asyncio.sleep(2)

            # Accepter cookies
            try:
                await page.click("text=Tout accepter", timeout=3000)
            except:
                pass

            # Cliquer sur widget avec retry
            widget_clicked = False
            for attempt in range(3):  # 3 tentatives
                for selector in ["div[data-entityid]", "text=Plus d'informations"]:
                    try:
                        await page.click(selector, timeout=5000)
                        widget_clicked = True
                        print(f"[Formation Scraper] Widget cliqué (tentative {attempt + 1})")
                        break
                    except:
                        continue
                if widget_clicked:
                    break
                await asyncio.sleep(2)

            await asyncio.sleep(3)  # Attendre chargement widget

            # Attendre les onglets avec patience (jusqu'à 30s)
            onglets_visibles = False
            for attempt in range(6):  # 6 × 5s = 30s max
                try:
                    await page.wait_for_selector("text=TEMPS FORTS", timeout=5000)
                    onglets_visibles = True
                    print(f"[Formation Scraper] Onglets détectés (tentative {attempt + 1})")
                    break
                except:
                    print(f"[Formation Scraper] Attente onglets... ({attempt + 1}/6)")
                    await asyncio.sleep(2)

            if not onglets_visibles:
                print("[Formation Scraper] WARNING - Onglets toujours pas visibles après 30s")

            # Cliquer sur COMPOSITION avec retry (jusqu'à 2 min)
            composition_clicked = False
            max_attempts = 24  # 24 × 5s = 2 minutes

            for attempt in range(max_attempts):
                for selector in ["text=COMPOSITION", "[role='tab']:has-text('COMPOSITION')", "button:has-text('COMPOSITION')"]:
                    try:
                        await page.wait_for_selector(selector, state="visible", timeout=3000)
                        await page.click(selector, timeout=2000)
                        composition_clicked = True
                        print(f"[Formation Scraper] Onglet COMPOSITION cliqué (tentative {attempt + 1})")
                        break
                    except:
                        continue

                if composition_clicked:
                    break

                # Afficher progression toutes les 5 tentatives
                if (attempt + 1) % 5 == 0:
                    print(f"[Formation Scraper] Toujours en attente... ({attempt + 1}/{max_attempts})")

                await asyncio.sleep(5)

            if not composition_clicked:
                print("[Formation Scraper] ERREUR - Onglet COMPOSITION non trouvé après 2 minutes")
                await browser.close()
                return {'home_formation': None, 'away_formation': None, 'success': False}

            await asyncio.sleep(5)  # Attendre chargement compositions

            # Extraction des formations
            page_text = await page.locator("body").inner_text()

            # Chercher formations (4-3-3, 5-3-2, 4-2-3-1, etc.)
            formation_patterns = [
                r'\b\d-\d-\d\b',        # 4-3-3, 5-3-2
                r'\b\d-\d-\d-\d\b',     # 4-2-3-1
            ]

            formations = []
            for pattern in formation_patterns:
                found = re.findall(pattern, page_text)
                formations.extend(found)

            # Dédupliquer
            formations = list(dict.fromkeys(formations))

            # Assigner
            home_formation = formations[0] if len(formations) >= 1 else None
            away_formation = formations[1] if len(formations) >= 2 else None

            result = {
                'home_formation': home_formation,
                'away_formation': away_formation,
                'success': bool(home_formation or away_formation)
            }

            print(f"[Formation Scraper] OK {home_team}: {home_formation} | {away_team}: {away_formation}")

            await browser.close()
            return result

        except Exception as e:
            print(f"[Formation Scraper] ERREUR: {e}")

            if browser:
                try:
                    await browser.close()
                except:
                    pass

            return {'home_formation': None, 'away_formation': None, 'success': False, 'error': str(e)}


# Wrapper synchrone
def get_formations(home_team: str, away_team: str) -> Dict:
    """Version synchrone pour faciliter l'utilisation"""
    return asyncio.run(scrape_formations_async(home_team, away_team))


# Test
if __name__ == "__main__":
    print("="*80)
    print("TEST GOOGLE FORMATION SCRAPER")
    print("="*80)

    result = get_formations("Nantes", "Angers")

    if result['success']:
        print(f"\n[OK] Formations extraites:")
        print(f"  Domicile: {result['home_formation']}")
        print(f"  Exterieur: {result['away_formation']}")
    else:
        print(f"\n[ERREUR] Echec")
