"""
Google Composition Scraper - VERSION FINALE
Scrape les compositions de matchs depuis Google Knowledge Graph
Utilise Bright Data Browser API pour contourner CAPTCHA
"""
import asyncio
from playwright.async_api import async_playwright
import re
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration Bright Data
CUSTOMER_ID = os.getenv("BRIGHTDATA_CUSTOMER_ID", "hl_d76a8bf0")
BROWSER_API_ZONE = os.getenv("BRIGHTDATA_BROWSER_API_ZONE", "google_scraper")
BROWSER_API_PASSWORD = os.getenv("BRIGHTDATA_BROWSER_API_PASSWORD", "cw407utbgsjj")

AUTH = f"brd-customer-{CUSTOMER_ID}-zone-{BROWSER_API_ZONE}:{BROWSER_API_PASSWORD}"
ENDPOINT = f"wss://{AUTH}@brd.superproxy.io:9222"


async def scrape_google_composition(home_team: str, away_team: str, league_code: str = None) -> Optional[Dict]:
    """
    Scrape la composition d'un match depuis Google

    Args:
        home_team: Équipe domicile (ex: "PSG", "Marseille")
        away_team: Équipe extérieur (ex: "Monaco", "Rennes")
        league_code: Code ligue optionnel (E0, F1, SP1, I1, D1)

    Returns:
        {
            'home_team': str,
            'away_team': str,
            'home_formation': str,  # ex: "4-3-3"
            'away_formation': str,
            'home_players': List[str],  # Liste des joueurs domicile
            'away_players': List[str],  # Liste des joueurs extérieur
            'source': 'google',
            'success': bool
        }
    """

    async with async_playwright() as p:
        browser = None
        try:
            print(f"[Google Scraper] Recherche: {home_team} vs {away_team}")

            # Connexion Browser API
            browser = await p.chromium.connect_over_cdp(ENDPOINT)
            page = await browser.new_page()

            # Navigation Google - FORCER LANGUE FRANÇAISE
            query = f"{home_team} vs {away_team}"
            if league_code:
                query += f" {league_code}"

            # hl=fr : langue interface, gl=FR : géolocalisation France
            await page.goto(f"https://www.google.com/search?q={query}&hl=fr&gl=FR", timeout=120000)
            await asyncio.sleep(2)

            # Accepter cookies (multi-langues)
            try:
                consent_selectors = [
                    "text=Tout accepter",
                    "text=Accept all",
                    "text=Aceptar todo",
                    "button#W0wltc",  # Sélecteur ID générique
                    "button[aria-label*='Accept']",
                    "button[aria-label*='Accepter']"
                ]
                for selector in consent_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        break
                    except:
                        continue
            except:
                pass

            # Cliquer sur widget pour l'étendre - MÉTHODE ROBUSTE
            print("[Google Scraper] Extension du widget...")
            widget_expanded = False

            # Méthode 1: Chercher les onglets directement (si déjà étendu)
            try:
                # Google utilise la classe GSkImd pour les onglets
                tabs = await page.query_selector_all('.GSkImd, div[role="tab"], button[role="tab"]')
                if len(tabs) >= 2:
                    print(f"[Google Scraper] Widget déjà étendu ({len(tabs)} onglets visibles)")
                    widget_expanded = True
            except:
                pass

            # Méthode 2: Cliquer sur le bouton d'extension
            if not widget_expanded:
                expand_selectors = [
                    'div[data-entityid]',
                    'div[data-entityname]',
                    'button:has-text("Plus d\'informations")',
                    'button:has-text("More about")',
                    'button:has-text("Más información")',
                    'div[jsname] > div > div > button',  # Bouton chevron générique
                ]

                for selector in expand_selectors:
                    try:
                        await page.click(selector, timeout=3000)
                        await asyncio.sleep(2)

                        # Vérifier si onglets maintenant visibles
                        tabs = await page.query_selector_all('.GSkImd, div[role="tab"], button[role="tab"]')
                        if len(tabs) >= 2:
                            print(f"[Google Scraper] Widget étendu avec {selector}")
                            widget_expanded = True
                            break
                    except:
                        continue

            # Méthode 3: Force-cliquer tous les boutons (dernier recours)
            if not widget_expanded:
                print("[Google Scraper] Force-clic sur tous les boutons...")
                all_buttons = await page.query_selector_all('button, div[role="button"]')
                for btn in all_buttons[:20]:  # Limiter à 20 premiers boutons
                    try:
                        await btn.click(force=True, timeout=1000)
                        await asyncio.sleep(1)

                        tabs = await page.query_selector_all('.GSkImd, div[role="tab"], button[role="tab"]')
                        if len(tabs) >= 2:
                            print(f"[Google Scraper] Widget étendu (force-clic)")
                            widget_expanded = True
                            break
                    except:
                        continue

            # Vérifier si widget étendu
            if not widget_expanded:
                print("[Google Scraper] ERREUR - Impossible d'étendre le widget")
                await browser.close()
                return None

            # Cliquer sur onglet COMPOSITION (multi-langues)
            print("[Google Scraper] Clic sur onglet Composition/Lineups...")
            composition_clicked = False

            # Chercher l'onglet avec différentes méthodes
            # NOTE: Le texte dans le HTML est "Composition" (pas "COMPOSITION")
            # Le CSS le transforme visuellement en majuscules
            tab_selectors = [
                # Par texte exact (multi-langues)
                "text=Composition",  # Français
                "text=Lineups",      # Anglais
                "text=Alineación",   # Espagnol
                "text=Formações",    # Portugais
                # Avec variations de casse
                ".GSkImd:has-text('Composition')",
                ".GSkImd:has-text('composition')",
                ".GSkImd:has-text('Lineups')",
                ".GSkImd:has-text('lineups')",
                # Par rôle
                "div[role='tab']:has-text('Composition')",
                "button[role='tab']:has-text('Lineups')",
            ]

            for selector in tab_selectors:
                try:
                    await page.wait_for_selector(selector, state="visible", timeout=2000)
                    await page.click(selector, timeout=2000)
                    composition_clicked = True
                    print(f"[Google Scraper] OK - Onglet cliqué: {selector}")
                    break
                except:
                    continue

            # Si pas trouvé par texte, chercher par position (3ème onglet généralement)
            if not composition_clicked:
                try:
                    tabs = await page.query_selector_all('div[role="tab"], button[role="tab"]')
                    if len(tabs) >= 3:
                        # Essayer le 3ème onglet (index 2)
                        await tabs[2].click()
                        composition_clicked = True
                        print(f"[Google Scraper] OK - 3ème onglet cliqué (position)")
                except:
                    pass

            if not composition_clicked:
                print("[Google Scraper] ERREUR - Onglet COMPOSITION non trouvé")
                await browser.close()
                return None

            await asyncio.sleep(3)

            # Extraction des données
            print("[Google Scraper] Extraction des données...")

            # Sauvegarder screenshot pour debug
            await page.screenshot(path=f"google_composition_debug.png", full_page=True)

            # Récupérer le texte VISIBLE (pas le HTML/CSS)
            page_text = await page.locator("body").inner_text()

            # DEBUG: Afficher un extrait
            print(f"[DEBUG] Extrait texte visible: {page_text[:1000]}")

            # Méthode 1: Chercher formations avec regex améliorée
            # Pattern: 4-3-3, 4-4-2, 5-3-2, 3-5-2, 4-2-3-1, etc.
            formation_patterns = [
                r'\b\d-\d-\d\b',        # 4-3-3
                r'\b\d-\d-\d-\d\b',     # 4-2-3-1
                r'\b\d\s*-\s*\d\s*-\s*\d\b',  # 4 - 3 - 3 (avec espaces)
            ]

            formations = []
            for pattern in formation_patterns:
                found = re.findall(pattern, page_text)
                formations.extend(found)

            # Nettoyer les formations (enlever espaces)
            formations = [f.replace(' ', '') for f in formations]
            formations = list(dict.fromkeys(formations))  # Dédupliquer

            print(f"[Google Scraper] Formations détectées: {formations}")

            # Méthode 2: Extraction directe depuis les locators
            # Chercher les conteneurs de formation
            formation_elements = await page.locator("[class*='formation'], [data-formation]").all()

            if not formations and formation_elements:
                for elem in formation_elements:
                    text = await elem.text_content()
                    if re.match(r'\d-\d-\d', text):
                        formations.append(text.strip())

            # Extraction des joueurs (seulement TITULAIRES)
            # Diviser le texte par "REMPLAÇANTS" pour séparer titulaires et remplaçants
            if "REMPLAÇANTS" in page_text or "REMPLACANTS" in page_text:
                text_before_subs = page_text.split("REMPLAÇANTS")[0] if "REMPLAÇANTS" in page_text else page_text.split("REMPLACANTS")[0]
            else:
                text_before_subs = page_text[:10000]  # Premiers 10k chars si pas de section remplaçants

            # Chercher tous les noms (Prénom Nom ou Initial. Nom)
            player_patterns = [
                r'\b[A-Z]\.\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # A. Lopes ou A. Van Den Boomen
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Fabien Centonze
            ]

            all_players = []
            for pattern in player_patterns:
                found = re.findall(pattern, text_before_subs)
                all_players.extend(found)

            # Nettoyer les noms (enlever \n\t)
            all_players = [p.replace('\n', ' ').replace('\t', ' ').strip() for p in all_players]

            # Filtrer les faux positifs
            excluded_words = ['Google Sans', 'Sans Text', 'Ligue', 'Match', 'Plus', 'Voir', 'Tous', 'Outils', 'Mode', 'Aide']
            all_players = [p for p in all_players if not any(ex in p for ex in excluded_words) and len(p) > 3]

            # Dédupliquer
            all_players = list(dict.fromkeys(all_players))

            print(f"[Google Scraper] Joueurs titulaires détectés: {len(all_players)}")

            # Diviser entre domicile et extérieur
            # On cherche où commence l'équipe 2 (après la formation de l'équipe 1)
            # On sait qu'il y a généralement 11 titulaires par équipe
            mid = min(11, len(all_players) // 2)
            home_players = all_players[:mid] if all_players else []
            away_players = all_players[mid:mid+11] if len(all_players) > mid else []

            # Assigner formations
            home_formation = formations[0] if len(formations) >= 1 else None
            away_formation = formations[1] if len(formations) >= 2 else None

            # Si qu'une seule formation trouvée, l'autre équipe a peut-être la même
            if home_formation and not away_formation and len(formations) == 1:
                away_formation = None  # On garde None si pas détectée

            result = {
                'home_team': home_team,
                'away_team': away_team,
                'home_formation': home_formation,
                'away_formation': away_formation,
                'home_players': home_players,
                'away_players': away_players,
                'all_players': all_players,  # Pour debug
                'source': 'google_brightdata',
                'success': bool(formations or all_players)
            }

            print(f"[Google Scraper] Résultat:")
            print(f"  Formation domicile: {home_formation}")
            print(f"  Formation extérieur: {away_formation}")
            print(f"  Joueurs domicile: {len(home_players)}")
            print(f"  Joueurs extérieur: {len(away_players)}")

            await browser.close()
            return result

        except Exception as e:
            print(f"[Google Scraper] ERREUR: {e}")
            import traceback
            traceback.print_exc()

            if browser:
                try:
                    await browser.close()
                except:
                    pass

            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_formation': None,
                'away_formation': None,
                'home_players': [],
                'away_players': [],
                'source': 'google_brightdata',
                'success': False,
                'error': str(e)
            }


# Wrapper synchrone pour compatibilité
def get_google_composition(home_team: str, away_team: str, league_code: str = None) -> Optional[Dict]:
    """Wrapper synchrone pour appeler le scraper async"""
    return asyncio.run(scrape_google_composition(home_team, away_team, league_code))


# Test
if __name__ == "__main__":
    print("="*80)
    print("TEST GOOGLE COMPOSITION SCRAPER")
    print("="*80)

    result = get_google_composition("Nantes", "Angers", "ligue 1")

    if result and result['success']:
        print("\n[SUCCÈS] Composition récupérée !")
        print(f"\nMatch: {result['home_team']} vs {result['away_team']}")
        print(f"Formation {result['home_team']}: {result['home_formation']}")
        print(f"Formation {result['away_team']}: {result['away_formation']}")
        print(f"\nJoueurs {result['home_team']}: {result['home_players'][:5]}...")
        print(f"Joueurs {result['away_team']}: {result['away_players'][:5]}...")
    else:
        print("\n[ÉCHEC] Composition non récupérée")
        if result:
            print(f"Erreur: {result.get('error')}")
