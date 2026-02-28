"""
Analyseur de formations - Analyse les performances selon les formations utilises

Pour chaque match historique:
1. Rcuprer la formation de l'quipe
2. Rcuprer la formation de l'adversaire
3. Analyser: "En 4-3-3 contre 5-4-1, combien de tirs?"
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class FormationAnalyzer:
    """
    Analyse les performances d'une quipe selon:
    - Sa formation
    - La formation de l'adversaire
    - Le contexte du match
    """

    def __init__(self):
        self.formation_cache = {}

    def classify_formation(self, formation: str) -> str:
        """
        Classifie une formation en catgorie tactique

        Args:
            formation: Formation (ex: "4-3-3", "3-5-2")

        Returns:
            Catgorie: "offensive", "balanced", "defensive"
        """
        if not formation:
            return "unknown"

        # Formations offensives (3 attaquants ou plus)
        offensive = ["4-3-3", "4-2-4", "3-4-3", "4-1-4-1"]
        if formation in offensive:
            return "offensive"

        # Formations dfensives (1 attaquant, 5 dfenseurs)
        defensive = ["5-4-1", "5-3-2", "4-5-1", "5-2-3"]
        if formation in defensive:
            return "defensive"

        # Formations quilibres
        balanced = ["4-4-2", "4-2-3-1", "3-5-2", "4-1-2-1-2"]
        if formation in balanced:
            return "balanced"

        return "unknown"

    def count_wingers(self, formation: str) -> int:
        """
        Compte le nombre d'ailiers dans une formation

        Args:
            formation: Formation (ex: "4-3-3")

        Returns:
            Nombre d'ailiers (0-2)
        """
        # Formations avec 2 ailiers
        with_wingers = ["4-3-3", "3-4-3", "4-2-3-1", "3-5-2"]
        if formation in with_wingers:
            return 2

        # Formations avec 1 ailier
        one_winger = ["4-4-1-1", "4-5-1"]
        if formation in one_winger:
            return 1

        return 0

    def get_formation_for_match(self, team: str, opponent: str, date: str) -> Optional[str]:
        """
        Rcupre la formation utilise pour un match historique

        Args:
            team: Nom de l'quipe
            opponent: Adversaire
            date: Date du match (DD/MM/YYYY ou YYYY-MM-DD)

        Returns:
            Formation (ex: "4-3-3") ou None
        """
        # NOTE: SofaScore abandonné - fonction désactivée
        # On retourne None pour utiliser valeur par défaut
        return None

    def enrich_history_with_formations(self, matches: List[Dict], team_name: str) -> List[Dict]:
        """
        Enrichit l'historique des matchs avec les formations

        Args:
            matches: Liste des matchs historiques
            team_name: Nom de l'quipe

        Returns:
            Matchs enrichis avec formations (NOTE: SofaScore abandonné, formations par défaut)
        """
        enriched = []
        total = len(matches)

        print(f"\n Enrichissement avec formations pour {team_name}...")
        print(f"   Total matchs: {total}")
        print(f"   NOTE: SofaScore desactive - utilisation formation par defaut 4-3-3")

        for i, match in enumerate(matches):
            # Copier le match
            enriched_match = match.copy()

            # Utiliser formation par défaut (SofaScore abandonné)
            enriched_match['formation'] = '4-3-3'
            enriched_match['formation_type'] = 'offensive'
            enriched_match['num_wingers'] = 2

            enriched.append(enriched_match)

        print(f"    Formations par defaut appliquees: {total}/{total}")

        return enriched

    def analyze_by_formation_matchup(self, matches: List[Dict]) -> Dict:
        """
        Analyse les performances par type de match-up de formations

        Args:
            matches: Matchs enrichis avec formations

        Returns:
            Statistiques par match-up
        """
        # Grouper par match-up
        matchups = {}

        for match in matches:
            if match.get('formation_type') == 'unknown':
                continue

            formation_type = match['formation_type']

            if formation_type not in matchups:
                matchups[formation_type] = {
                    'count': 0,
                    'shots': [],
                    'corners': [],
                    'goals': []
                }

            matchups[formation_type]['count'] += 1
            matchups[formation_type]['shots'].append(match['shots'])
            matchups[formation_type]['corners'].append(match['corners'])
            if match.get('goals_for') is not None:
                matchups[formation_type]['goals'].append(match['goals_for'])

        # Calculer les moyennes
        stats = {}
        for formation_type, data in matchups.items():
            stats[formation_type] = {
                'count': data['count'],
                'avg_shots': sum(data['shots']) / len(data['shots']) if data['shots'] else 0,
                'avg_corners': sum(data['corners']) / len(data['corners']) if data['corners'] else 0,
                'avg_goals': sum(data['goals']) / len(data['goals']) if data['goals'] else 0
            }

        return stats

    def get_formation_factor_from_data(self, team_formation: str, opponent_formation: str,
                                      team_history: List[Dict]) -> Tuple[float, float, Dict]:
        """
        Calcule le facteur d'ajustement selon les formations EN ANALYSANT LES VRAIES DONNES

        Args:
            team_formation: Formation de l'quipe pour ce match
            opponent_formation: Formation de l'adversaire pour ce match
            team_history: Historique enrichi avec formations

        Returns:
            (shots_factor, corners_factor, stats)
        """
        team_type = self.classify_formation(team_formation)
        opponent_type = self.classify_formation(opponent_formation)

        # Filtrer les matchs selon les types de formations
        # 1. Matchs avec cette formation
        matches_with_formation = [m for m in team_history
                                 if m.get('formation_type') == team_type]

        # 2. Matchs avec cette formation contre ce type d'adversaire
        # (On ne peut pas toujours avoir la formation exacte de l'adversaire historique,
        #  donc on utilise des heuristiques bases sur les performances)

        if len(matches_with_formation) < 3:
            # Pas assez de donnes - utiliser valeur neutre
            return 1.0, 1.0, {
                'method': 'default',
                'reason': f'Pas assez de matchs avec formation {team_type} ({len(matches_with_formation)} matchs)',
                'matches_analyzed': 0
            }

        # Calculer les moyennes avec cette formation
        avg_shots_with_formation = sum(m['shots'] for m in matches_with_formation) / len(matches_with_formation)
        avg_corners_with_formation = sum(m['corners'] for m in matches_with_formation) / len(matches_with_formation)

        # Calculer les moyennes GLOBALES (toutes formations)
        all_matches = [m for m in team_history if 'shots' in m]
        if not all_matches:
            return 1.0, 1.0, {'method': 'default', 'reason': 'Pas de matchs historiques'}

        avg_shots_global = sum(m['shots'] for m in all_matches) / len(all_matches)
        avg_corners_global = sum(m['corners'] for m in all_matches) / len(all_matches)

        # Calculer les facteurs RELS bass sur les donnes
        shots_factor = avg_shots_with_formation / avg_shots_global if avg_shots_global > 0 else 1.0
        corners_factor = avg_corners_with_formation / avg_corners_global if avg_corners_global > 0 else 1.0

        # Limiter les facteurs (viter les extrmes)
        shots_factor = max(0.5, min(1.5, shots_factor))
        corners_factor = max(0.5, min(1.5, corners_factor))

        stats = {
            'method': 'data_driven',
            'team_formation_type': team_type,
            'opponent_formation_type': opponent_type,
            'matches_analyzed': len(matches_with_formation),
            'avg_shots_with_formation': round(avg_shots_with_formation, 2),
            'avg_shots_global': round(avg_shots_global, 2),
            'avg_corners_with_formation': round(avg_corners_with_formation, 2),
            'avg_corners_global': round(avg_corners_global, 2),
            'shots_factor': round(shots_factor, 3),
            'corners_factor': round(corners_factor, 3),
            'shots_change_pct': round((shots_factor - 1) * 100, 1),
            'corners_change_pct': round((corners_factor - 1) * 100, 1)
        }

        return shots_factor, corners_factor, stats


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    analyzer = FormationAnalyzer()

    # Test classification
    print("=" * 60)
    print("TEST CLASSIFICATION DES FORMATIONS")
    print("=" * 60)

    formations = ["4-3-3", "4-4-2", "5-4-1", "3-5-2", "4-2-3-1"]
    for formation in formations:
        f_type = analyzer.classify_formation(formation)
        wingers = analyzer.count_wingers(formation)
        print(f"{formation:10}  Type: {f_type:10} | Ailiers: {wingers}")

    print("\n" + "=" * 60)
    print("TEST FACTEURS D'AJUSTEMENT")
    print("=" * 60)

    matchups = [
        ("4-3-3", "5-4-1"),  # Offensive vs Dfensive
        ("4-3-3", "4-3-3"),  # Offensive vs Offensive
        ("5-4-1", "4-3-3"),  # Dfensive vs Offensive
        ("4-4-2", "4-2-3-1"),  # Balanced vs Balanced
    ]

    for team_form, opp_form in matchups:
        shots_f, corners_f = analyzer.get_formation_factor(team_form, opp_form, {})
        print(f"\n{team_form} vs {opp_form}:")
        print(f"  Tirs: {shots_f:.2f}x | Corners: {corners_f:.2f}x")
