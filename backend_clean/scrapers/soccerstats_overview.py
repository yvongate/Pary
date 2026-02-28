#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper COMPLET pour Tables Overview de soccerstats.com
Parse le MEGA tableau (275 lignes) avec tous les classements
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List

def get_tables_overview(league_code: str = "england") -> Optional[Dict]:
    """
    Récupère TOUS les classements depuis le tableau Tables overview

    Retourne:
    - standings: Classement général
    - form_last_8: Forme sur 8 derniers matchs
    - home: Classement domicile
    - away: Classement extérieur
    - offence: Classement attaque
    - defence: Classement défense
    - offence_last_8: Attaque sur 8 derniers
    - defence_last_8: Défense sur 8 derniers
    - offence_home: Attaque à domicile
    - defence_home: Défense à domicile
    - offence_away: Attaque à l'extérieur
    - defence_away: Défense à l'extérieur
    """

    url = f"https://www.soccerstats.com/latest.asp?league={league_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    print(f"[SCRAPING] {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trouver le mega tableau (TABLE 62 - 275 lignes)
        overview_table = None
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if len(rows) > 250:  # Le mega tableau a 275 lignes
                overview_table = table
                break

        if not overview_table:
            print("[ERREUR] Tables overview non trouvé")
            return None

        rows = overview_table.find_all('tr')
        print(f"[FOUND] Tables overview: {len(rows)} lignes")

        # Parser ligne par ligne pour identifier les sections
        result = {
            "standings": [],
            "form_last_8": [],
            "home": [],
            "away": [],
            "offence": [],
            "defence": [],
            "offence_last_8": [],
            "defence_last_8": [],
            "offence_home": [],
            "defence_home": [],
            "offence_away": [],
            "defence_away": []
        }

        current_section = None

        for i, row in enumerate(rows):
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]

            if len(cells) == 0:
                continue

            # Identifier les headers de section
            first_cell = cells[0].lower()

            if 'points' in first_cell and 'gp' in first_cell:
                current_section = 'standings'
                print(f"  Ligne {i}: Section STANDINGS")
                continue
            elif 'form (last 8)' in first_cell:
                current_section = 'form_last_8'
                print(f"  Ligne {i}: Section FORM (last 8)")
                continue
            elif first_cell == 'home' or ('home' in first_cell and 'gp' in first_cell):
                current_section = 'home'
                print(f"  Ligne {i}: Section HOME")
                continue
            elif first_cell == 'away' or ('away' in first_cell and 'gp' in first_cell):
                current_section = 'away'
                print(f"  Ligne {i}: Section AWAY")
                continue
            elif first_cell == 'offence' or ('offence' in first_cell and 'gp' in first_cell):
                if 'last 8' in first_cell:
                    current_section = 'offence_last_8'
                    print(f"  Ligne {i}: Section OFFENCE (last 8)")
                elif 'home' in first_cell:
                    current_section = 'offence_home'
                    print(f"  Ligne {i}: Section OFFENCE (home)")
                elif 'away' in first_cell:
                    current_section = 'offence_away'
                    print(f"  Ligne {i}: Section OFFENCE (away)")
                else:
                    current_section = 'offence'
                    print(f"  Ligne {i}: Section OFFENCE")
                continue
            elif first_cell == 'defence' or ('defence' in first_cell and 'gp' in first_cell):
                if 'last 8' in first_cell:
                    current_section = 'defence_last_8'
                    print(f"  Ligne {i}: Section DEFENCE (last 8)")
                elif 'home' in first_cell:
                    current_section = 'defence_home'
                    print(f"  Ligne {i}: Section DEFENCE (home)")
                elif 'away' in first_cell:
                    current_section = 'defence_away'
                    print(f"  Ligne {i}: Section DEFENCE (away)")
                else:
                    current_section = 'defence'
                    print(f"  Ligne {i}: Section DEFENCE")
                continue
            elif 'segment' in first_cell:
                current_section = None  # Ignorer segments table
                continue

            # Parser les lignes de données
            if current_section and len(cells) >= 4:
                # Format typique: ['', 'Team', 'GP', 'Value', '']
                # Exemples:
                # - Standings: ['', 'Arsenal', '27', '58', '']
                # - Form: ['', 'Manchester U.', '8', '16', '']
                # - Offence: ['', 'Manchester C.', '27', '56', '']

                try:
                    team = cells[1]  # Cell 1 = Team name
                    gp = int(cells[2])  # Cell 2 = GP
                    value = int(cells[3])  # Cell 3 = Value (points/goals)

                    # Vérifier que c'est une vraie ligne (pas un header)
                    if team and gp > 0 and gp <= 40:  # GP raisonnable
                        team_data = {
                            "team": team,
                            "played": gp,
                        }

                        # Ajouter la valeur selon le type de section
                        if current_section in ['standings', 'home', 'away', 'form_last_8']:
                            team_data["points"] = value
                        elif 'offence' in current_section:
                            team_data["goals_for"] = value
                        elif 'defence' in current_section:
                            team_data["goals_against"] = value

                        result[current_section].append(team_data)

                except (ValueError, IndexError):
                    continue

        # Ajouter les positions
        for section_name, teams in result.items():
            for i, team in enumerate(teams, 1):
                team['position'] = i

        # Stats
        print(f"\n[SUCCESS] Données extraites:")
        for section_name, teams in result.items():
            if teams:
                print(f"  - {section_name}: {len(teams)} équipes")

        return result

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import json

    print("="*70)
    print("TEST: Scraping Tables Overview COMPLET")
    print("="*70 + "\n")

    data = get_tables_overview("england")

    if data:
        # Afficher un aperçu de chaque section
        print("\n" + "="*70)
        print("APERÇU DES DONNÉES")
        print("="*70)

        # Classement général - Top 5
        if data['standings']:
            print("\nCLASSEMENT GÉNÉRAL (Top 5):")
            for team in data['standings'][:5]:
                print(f"  {team['position']}. {team['team']}: {team['played']}J - {team['points']} pts")

        # Forme récente - Top 5
        if data['form_last_8']:
            print("\nFORME (8 derniers) - Top 5:")
            for team in data['form_last_8'][:5]:
                print(f"  {team['position']}. {team['team']}: {team['points']}/24 pts")

        # Domicile - Top 3
        if data['home']:
            print("\nMEILLEURS À DOMICILE (Top 3):")
            for team in data['home'][:3]:
                print(f"  {team['position']}. {team['team']}: {team['points']} pts")

        # Attaque - Top 3
        if data['offence']:
            print("\nMEILLEURES ATTAQUES:")
            for team in data['offence'][:3]:
                print(f"  {team['position']}. {team['team']}: {team['goals_for']} buts")

        # Défense - Top 3
        if data['defence']:
            print("\nMEILLEURES DÉFENSES:")
            for team in data['defence'][:3]:
                print(f"  {team['position']}. {team['team']}: {team['goals_against']} buts encaissés")

        # Sauvegarder tout
        with open('tables_overview.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("\n" + "="*70)
        print("[SUCCESS] Toutes les données sauvegardées: tables_overview.json")
        print("="*70)

    else:
        print("\n[ERREUR] Échec du scraping")
