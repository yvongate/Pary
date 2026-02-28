#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper soccerstats.com - VERSION QUI FONCTIONNE!
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict


def get_standings(league_code: str = "england") -> Optional[List[Dict]]:
    """
    Récupère le classement complet depuis soccerstats.com

    Returns:
        Liste de 20 équipes avec stats complètes
    """
    url = f"https://www.soccerstats.com/latest.asp?league={league_code}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"[SCRAPING] {url}")

    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')

    all_standings = []

    # Parcourir toutes les tables
    for table in soup.find_all('table'):
        rows = table.find_all('tr')

        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]

            # Le classement principal a ce format:
            # [Pos, Team, GP, W, D, L, GF, GA, GD, Pts, ...]
            # Les 10 premières colonnes sont les stats, après c'est les matchs récents

            if (len(cells) >= 10 and
                cells[0].isdigit() and  # Position
                cells[2].isdigit() and  # GP (games played)
                cells[9].isdigit()):    # Points

                try:
                    position = int(cells[0])
                    team = cells[1]
                    played = int(cells[2])
                    points = int(cells[9])

                    # Vérifier que c'est du foot (max 38 matchs en PL)
                    if played > 40:
                        continue

                    # Extraire toutes les stats
                    team_data = {
                        "position": position,
                        "team": team,
                        "played": played,
                        "won": int(cells[3]),
                        "drawn": int(cells[4]),
                        "lost": int(cells[5]),
                        "goals_for": int(cells[6]),
                        "goals_against": int(cells[7]),
                        "goal_difference": int(cells[8].replace('+', '')),
                        "points": points
                    }

                    all_standings.append(team_data)

                except (ValueError, IndexError):
                    continue

    # Dédupliquer par équipe (garder celle avec le plus de matchs joués)
    unique_teams = {}
    for team in all_standings:
        key = team['team']
        if key not in unique_teams or team['played'] >= unique_teams[key]['played']:
            unique_teams[key] = team

    standings = list(unique_teams.values())
    standings.sort(key=lambda x: x['position'])

    print(f"[SUCCESS] {len(standings)} équipes trouvées")

    return standings


def get_team_context(team_name: str, league_code: str = "england") -> Optional[Dict]:
    """
    Récupère le classement d'une équipe avec contexte complet
    """
    standings = get_standings(league_code)

    if not standings:
        return None

    # Chercher l'équipe
    team_data = None
    for team in standings:
        if team_name.lower() in team['team'].lower() or team['team'].lower() in team_name.lower():
            team_data = team.copy()
            break

    if not team_data:
        print(f"[ERREUR] Équipe '{team_name}' non trouvée")
        return None

    # Ajouter le contexte
    if len(standings) > 0:
        first_team = standings[0]
        team_data['gap_to_top'] = team_data['points'] - first_team['points']

    # Top 4 (Champions League)
    if len(standings) >= 4:
        fourth_team = standings[3]
        team_data['gap_to_top4'] = team_data['points'] - fourth_team['points']

    # Relégation (18e en Premier League)
    if len(standings) >= 18:
        relegation_team = standings[17]
        team_data['gap_to_relegation'] = team_data['points'] - relegation_team['points']

    return team_data


if __name__ == "__main__":
    print("="*70)
    print("TEST: Scraping soccerstats.com - VERSION FINALE")
    print("="*70)

    standings = get_standings("england")

    if standings and len(standings) > 0:
        print(f"\n{'='*70}")
        print("PREMIER LEAGUE - CLASSEMENT COMPLET")
        print(f"{'='*70}")
        print(f"{'Pos':<4} {'Équipe':<22} {'J':<3} {'V-N-D':<10} {'Buts':<10} {'Diff':<6} {'Pts':<4}")
        print("-"*70)

        for team in standings:
            record = f"{team['won']}-{team['drawn']}-{team['lost']}"
            goals = f"{team['goals_for']}-{team['goals_against']}"
            diff = f"{team['goal_difference']:+d}"

            print(f"{team['position']:<4} {team['team']:<22} {team['played']:<3} "
                  f"{record:<10} {goals:<10} {diff:<6} {team['points']:<4}")

        # Test équipe spécifique
        print(f"\n{'='*70}")
        print("DÉTAILS AVEC CONTEXTE: Liverpool")
        print(f"{'='*70}")

        liverpool = get_team_context("Liverpool", "england")

        if liverpool:
            print(f"\nClassement: {liverpool['position']}e place")
            print(f"Points: {liverpool['points']} pts")
            print(f"Matchs: {liverpool['played']} joués")
            print(f"Bilan: {liverpool['won']}V - {liverpool['drawn']}N - {liverpool['lost']}D")
            print(f"Buts: {liverpool['goals_for']} marqués / {liverpool['goals_against']} encaissés")
            print(f"Différence: {liverpool['goal_difference']:+d}")
            print(f"\n[CONTEXTE COMPÉTITION]")
            print(f"Écart avec le leader: {liverpool['gap_to_top']:+d} pts")

            if 'gap_to_top4' in liverpool:
                gap = liverpool['gap_to_top4']
                if gap < 0:
                    print(f"Écart avec le Top 4: {gap:+d} pts (HORS Top 4)")
                elif gap == 0:
                    print(f"Position: 4e place (BARRAGE Champions League)")
                else:
                    print(f"Avance sur la 5e place: {gap:+d} pts (QUALIFIÉ Top 4)")

            if 'gap_to_relegation' in liverpool:
                print(f"Avance sur la relégation (18e): {liverpool['gap_to_relegation']:+d} pts")

    else:
        print("[ERREUR] Aucune donnée récupérée")
