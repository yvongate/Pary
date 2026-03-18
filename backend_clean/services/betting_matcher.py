#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service pour identifier les matchs pertinents pour les paris
Grands vs 5 derniers
"""

import pandas as pd
from collections import defaultdict
import os

# Grands clubs par championnat
BIG_TEAMS = {
    'F1': ['Paris SG', 'Marseille'],
    'E0': ['Arsenal', 'Man City', 'Man United'],
    'SP1': ['Barcelona', 'Real Madrid', 'Atletico Madrid'],
    'I1': ['Inter', 'AC Milan', 'Como'],
    'P1': ['Porto', 'Sp Lisbon', 'Benfica'],
    'B1': ['St. Gilloise', 'Club Brugge'],
    'T1': ['Galatasaray', 'Fenerbahce']
}

def get_bottom_5_teams(league_code):
    """Identifie les 5 derniers du championnat par points"""
    csv_path = f'data/{league_code}_2526.csv'

    if not os.path.exists(csv_path):
        return []

    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception:
        return []

    team_points = defaultdict(int)

    for _, row in df.iterrows():
        home_team = row['HomeTeam']
        away_team = row['AwayTeam']

        if pd.isna(row['FTHG']) or pd.isna(row['FTAG']):
            continue

        home_goals = int(row['FTHG'])
        away_goals = int(row['FTAG'])

        if home_goals > away_goals:
            team_points[home_team] += 3
        elif away_goals > home_goals:
            team_points[away_team] += 3
        else:
            team_points[home_team] += 1
            team_points[away_team] += 1

    sorted_teams = sorted(team_points.items(), key=lambda x: x[1])
    bottom_5_names = [team for team, points in sorted_teams[:5]]  # [:5] = les 5 avec le moins de points

    return bottom_5_names

def is_betting_match(home_team, away_team, league_code):
    """
    Vérifie si un match est pertinent pour les paris
    (Grand vs 5 derniers)

    Returns:
        dict avec is_betting_match (bool) et infos supplémentaires
    """
    big_teams = BIG_TEAMS.get(league_code, [])
    bottom_5 = get_bottom_5_teams(league_code)

    if not big_teams or not bottom_5:
        return {
            'is_betting_match': False,
            'big_team': None,
            'weak_team': None,
            'reason': None
        }

    # Grand à domicile vs faible à l'extérieur
    if home_team in big_teams and away_team in bottom_5:
        return {
            'is_betting_match': True,
            'big_team': home_team,
            'weak_team': away_team,
            'weak_team_location': 'away',
            'reason': f'{home_team} (Grand) vs {away_team} (5 derniers)'
        }

    # Grand à l'extérieur vs faible à domicile
    if away_team in big_teams and home_team in bottom_5:
        return {
            'is_betting_match': True,
            'big_team': away_team,
            'weak_team': home_team,
            'weak_team_location': 'home',
            'reason': f'{home_team} (5 derniers) vs {away_team} (Grand)'
        }

    return {
        'is_betting_match': False,
        'big_team': None,
        'weak_team': None,
        'reason': None
    }

def get_all_bottom_5():
    """Récupère les 5 derniers de tous les championnats"""
    all_bottom_5 = {}

    for league_code in BIG_TEAMS.keys():
        bottom_5 = get_bottom_5_teams(league_code)
        if bottom_5:
            all_bottom_5[league_code] = bottom_5

    return all_bottom_5

def get_all_big_teams():
    """Récupère tous les grands clubs"""
    return BIG_TEAMS
