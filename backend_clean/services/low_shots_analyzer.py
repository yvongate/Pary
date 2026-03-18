#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service d'analyse des tirs faibles contre les grands clubs
Utilisé par l'endpoint /analysis/low-shots
"""

import pandas as pd
from collections import defaultdict
from datetime import datetime
import os

# Configuration des championnats
BIG_TEAMS = {
    'F1': ['Paris SG', 'Marseille'],
    'E0': ['Arsenal', 'Man City', 'Man United'],
    'SP1': ['Barcelona', 'Real Madrid', 'Atletico Madrid'],
    'I1': ['Inter', 'AC Milan', 'Como'],
    'P1': ['Porto', 'Sp Lisbon', 'Benfica'],
    'B1': ['St. Gilloise', 'Club Brugge'],
    'T1': ['Galatasaray', 'Fenerbahce']
}

LEAGUES_INFO = {
    'E0': {'name': 'Premier League', 'country': 'England', 'emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
    'SP1': {'name': 'La Liga', 'country': 'Spain', 'emoji': '🇪🇸'},
    'I1': {'name': 'Serie A', 'country': 'Italy', 'emoji': '🇮🇹'},
    'F1': {'name': 'Ligue 1', 'country': 'France', 'emoji': '🇫🇷'},
    'P1': {'name': 'Primeira Liga', 'country': 'Portugal', 'emoji': '🇵🇹'},
    'B1': {'name': 'Jupiler Pro League', 'country': 'Belgium', 'emoji': '🇧🇪'},
    'T1': {'name': 'Süper Lig', 'country': 'Turkey', 'emoji': '🇹🇷'}
}

def get_bottom_5_teams(df):
    """Identifie les 5 derniers du championnat par points"""
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
    bottom_5 = [{'team': team, 'points': points} for team, points in sorted_teams[:5]]  # [:5] = les 5 avec le moins de points

    return bottom_5

def analyze_team_vs_bigs(team_name, big_teams, df):
    """Analyse les tirs d'une équipe contre les grands"""
    shots_vs_bigs = []
    shots_by_big_team = defaultdict(list)

    for _, row in df.iterrows():
        home_team = row['HomeTeam']
        away_team = row['AwayTeam']

        if pd.isna(row['HS']) or pd.isna(row['AS']):
            continue

        home_shots = int(row['HS'])
        away_shots = int(row['AS'])

        # Team à domicile vs grand à l'extérieur
        if home_team == team_name and away_team in big_teams:
            shots_vs_bigs.append(home_shots)
            shots_by_big_team[away_team].append(home_shots)

        # Team à l'extérieur vs grand à domicile
        if away_team == team_name and home_team in big_teams:
            shots_vs_bigs.append(away_shots)
            shots_by_big_team[home_team].append(away_shots)

    if not shots_vs_bigs:
        return None

    avg_shots = sum(shots_vs_bigs) / len(shots_vs_bigs)
    under_10_count = sum(1 for s in shots_vs_bigs if s <= 10)
    under_8_5_count = sum(1 for s in shots_vs_bigs if s <= 8.5)
    percentage_under_10 = (under_10_count / len(shots_vs_bigs)) * 100
    percentage_under_8_5 = (under_8_5_count / len(shots_vs_bigs)) * 100

    # Prédictions par grand club (seulement si ≤8.5 projeté)
    predictions = []
    for big_team in big_teams:
        if big_team in shots_by_big_team and shots_by_big_team[big_team]:
            # Historique réel disponible
            avg_vs_this_big = sum(shots_by_big_team[big_team]) / len(shots_by_big_team[big_team])
            if avg_vs_this_big <= 8.5:
                predictions.append({
                    'big_team': big_team,
                    'projected_shots': round(avg_vs_this_big, 1),
                    'confidence': 'high' if len(shots_by_big_team[big_team]) >= 2 else 'medium',
                    'historical_shots': shots_by_big_team[big_team],
                    'recommendation': 'bet' if avg_vs_this_big <= 8.5 else 'avoid'
                })
        else:
            # Projection basée sur la moyenne globale
            if avg_shots <= 8.5:
                predictions.append({
                    'big_team': big_team,
                    'projected_shots': round(avg_shots, 1),
                    'confidence': 'low',
                    'historical_shots': [],
                    'recommendation': 'bet' if avg_shots <= 7 else 'caution'
                })

    return {
        'total_matches': len(shots_vs_bigs),
        'avg_shots': round(avg_shots, 1),
        'percentage_under_10': round(percentage_under_10, 1),
        'percentage_under_8_5': round(percentage_under_8_5, 1),
        'shots_list': shots_vs_bigs,
        'predictions': predictions,
        'reliability': 'excellent' if percentage_under_8_5 == 100 else
                      'very_good' if percentage_under_8_5 >= 80 else
                      'good' if percentage_under_8_5 >= 60 else 'risky'
    }

def analyze_big_team_defense(big_team, bottom_5_teams, df):
    """Analyse la défense d'un grand club contre les faibles"""
    opponent_shots = []

    for _, row in df.iterrows():
        home_team = row['HomeTeam']
        away_team = row['AwayTeam']

        if pd.isna(row['HS']) or pd.isna(row['AS']):
            continue

        home_shots = int(row['HS'])
        away_shots = int(row['AS'])

        # Grand à domicile vs faible à l'extérieur
        if home_team == big_team and away_team in [t['team'] for t in bottom_5_teams]:
            opponent_shots.append(away_shots)

        # Grand à l'extérieur vs faible à domicile
        if away_team == big_team and home_team in [t['team'] for t in bottom_5_teams]:
            opponent_shots.append(home_shots)

    if not opponent_shots:
        return None

    avg_opponent_shots = sum(opponent_shots) / len(opponent_shots)
    under_10_count = sum(1 for s in opponent_shots if s <= 10)
    percentage = (under_10_count / len(opponent_shots)) * 100

    return {
        'total_matches': len(opponent_shots),
        'avg_opponent_shots': round(avg_opponent_shots, 1),
        'percentage_under_10': round(percentage, 1),
        'reliability': 'excellent' if percentage == 100 else
                      'very_good' if percentage >= 85 else
                      'good' if percentage >= 70 else 'average'
    }

def get_full_analysis():
    """Analyse complète de tous les championnats"""

    global_stats = {
        'total_matches': 0,
        'under_10_count': 0,
        'total_shots': 0
    }

    leagues_analysis = {}

    for league_code, big_teams in BIG_TEAMS.items():
        csv_path = f'data/{league_code}_2526.csv'

        if not os.path.exists(csv_path):
            continue

        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except Exception:
            continue

        # Identifier les 5 derniers
        bottom_5 = get_bottom_5_teams(df)
        bottom_5_names = [t['team'] for t in bottom_5]

        # Stats globales du championnat
        league_matches = []
        for _, row in df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']

            if pd.isna(row['HS']) or pd.isna(row['AS']):
                continue

            home_shots = int(row['HS'])
            away_shots = int(row['AS'])

            # Grand à domicile vs faible à l'extérieur
            if home_team in big_teams and away_team in bottom_5_names:
                league_matches.append(away_shots)

            # Grand à l'extérieur vs faible à domicile
            if away_team in big_teams and home_team in bottom_5_names:
                league_matches.append(home_shots)

        if league_matches:
            under_10 = sum(1 for s in league_matches if s <= 10)
            avg_shots = sum(league_matches) / len(league_matches)

            global_stats['total_matches'] += len(league_matches)
            global_stats['under_10_count'] += under_10
            global_stats['total_shots'] += sum(league_matches)

            league_stats = {
                'total_matches': len(league_matches),
                'percentage_under_10': round((under_10 / len(league_matches)) * 100, 1),
                'avg_shots': round(avg_shots, 1)
            }
        else:
            league_stats = {'total_matches': 0, 'percentage_under_10': 0, 'avg_shots': 0}

        # Analyser chaque grand club
        big_teams_analysis = []
        for big_team in big_teams:
            analysis = analyze_big_team_defense(big_team, bottom_5, df)
            if analysis:
                big_teams_analysis.append({
                    'name': big_team,
                    **analysis
                })

        # Analyser les 5 derniers
        bottom_5_analysis = []
        for team_info in bottom_5:
            team_name = team_info['team']
            analysis = analyze_team_vs_bigs(team_name, big_teams, df)
            if analysis:
                bottom_5_analysis.append({
                    'name': team_name,
                    'points': team_info['points'],
                    **analysis
                })

        # Trier par fiabilité
        big_teams_analysis.sort(key=lambda x: x['percentage_under_10'], reverse=True)
        bottom_5_analysis.sort(key=lambda x: x['percentage_under_8_5'], reverse=True)

        leagues_analysis[league_code] = {
            **LEAGUES_INFO[league_code],
            'stats': league_stats,
            'big_teams': big_teams_analysis,
            'bottom_5': bottom_5_analysis
        }

    # Calculer les stats globales
    if global_stats['total_matches'] > 0:
        global_percentage = (global_stats['under_10_count'] / global_stats['total_matches']) * 100
        global_avg = global_stats['total_shots'] / global_stats['total_matches']
    else:
        global_percentage = 0
        global_avg = 0

    return {
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'global_stats': {
            'total_matches': global_stats['total_matches'],
            'percentage_under_10': round(global_percentage, 1),
            'average_shots': round(global_avg, 1)
        },
        'leagues': leagues_analysis
    }
