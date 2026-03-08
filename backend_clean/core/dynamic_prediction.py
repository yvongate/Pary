"""
Systme de Prdiction Dynamique - Calcul  la vole pour chaque match

PAS de machine learning pr-entran!
Pour chaque match demand:
1. Rcuprer les donnes EN TEMPS REL (classements actuels, blessures, mto)
2. Analyser TOUS les matchs historiques de l'quipe
3. Faire la corrlation  LA VOLE
4. Prdire avec la situation ACTUELLE
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from scipy.optimize import minimize
from scipy.special import gammaln  # Pour log-vraisemblance Poisson

import scrapers.soccerstats_overview as soccerstats_overview
import scrapers.soccerstats_working as soccerstats_working
from core.data_collector import DataCollector
from core.formation_analyzer import FormationAnalyzer
from core.ai_deep_reasoning import generate_deep_analysis_prediction
import scrapers.ruedesjoueurs_finder as rdj_finder
import scrapers.ruedesjoueurs_scraper as rdj_scraper
from services.sqlite_database_service import get_sqlite_db


class DynamicPredictor:
    """
    Prdiction dynamique base sur les donnes en temps rel
    Aucun modle pr-entran - tout est calcul  la demande
    """

    def __init__(self, use_formations: bool = True):
        """
        Args:
            use_formations: Si True, analyse les formations (plus lent mais plus prcis)
        """
        self.collector = DataCollector()
        self.formation_analyzer = FormationAnalyzer()
        self.use_formations = use_formations

    def load_team_history(self, team_name: str, league_code: str, max_matches: int = 200) -> List[Dict]:
        """
        Charge TOUS les matchs historiques d'une quipe depuis les CSV

        Args:
            team_name: Nom de l'quipe
            league_code: Code du championnat (E0, SP1, etc.)
            max_matches: Nombre max de matchs  charger

        Returns:
            Liste des matchs avec stats
        """
        # Essayer plusieurs saisons
        current_year = datetime.now().year
        seasons = [
            f"{str(current_year-1)[2:]}{str(current_year)[2:]}",  # 2526
            f"{str(current_year-2)[2:]}{str(current_year-1)[2:]}",  # 2425
            f"{str(current_year-3)[2:]}{str(current_year-2)[2:]}",  # 2324
        ]

        all_matches = []

        for season in seasons:
            filepath = f"data/{league_code}_{season}.csv"
            if not os.path.exists(filepath):
                continue

            try:
                df = pd.read_csv(filepath)

                # Matchs  domicile
                home_matches = df[df['HomeTeam'].str.lower() == team_name.lower()].copy()
                for _, row in home_matches.iterrows():
                    if pd.notna(row.get('HS')) and pd.notna(row.get('HC')):
                        all_matches.append({
                            'team': team_name,
                            'opponent': row['AwayTeam'],
                            'home': True,
                            'shots': int(row['HS']),
                            'corners': int(row['HC']),
                            'goals_for': int(row['FTHG']) if pd.notna(row.get('FTHG')) else None,
                            'goals_against': int(row['FTAG']) if pd.notna(row.get('FTAG')) else None,
                            'date': row.get('Date'),
                            'season': season
                        })

                # Matchs  l'extrieur
                away_matches = df[df['AwayTeam'].str.lower() == team_name.lower()].copy()
                for _, row in away_matches.iterrows():
                    if pd.notna(row.get('AS')) and pd.notna(row.get('AC')):
                        all_matches.append({
                            'team': team_name,
                            'opponent': row['HomeTeam'],
                            'home': False,
                            'shots': int(row['AS']),
                            'corners': int(row['AC']),
                            'goals_for': int(row['FTAG']) if pd.notna(row.get('FTAG')) else None,
                            'goals_against': int(row['FTHG']) if pd.notna(row.get('FTHG')) else None,
                            'date': row.get('Date'),
                            'season': season
                        })

            except Exception as e:
                print(f"Erreur lecture {filepath}: {e}")
                continue

            if len(all_matches) >= max_matches:
                break

        return all_matches[:max_matches]

    def get_current_rankings(self, league_code: str) -> Dict:
        """
        Rcupre les classements ACTUELS en temps rel

        Args:
            league_code: england, spain, italy, france, germany

        Returns:
            Dict avec tous les classements (12 tableaux)
        """
        rankings = soccerstats_overview.get_tables_overview(league_code)
        return rankings if rankings else {}

    def analyze_correlation(self, team_history: List[Dict], current_rankings: Dict,
                          is_home: bool = True) -> Dict:
        """
        Analyse la corrlation entre les matchs historiques et les rangs dfensifs

        Args:
            team_history: Historique des matchs de l'quipe
            current_rankings: Classements actuels
            is_home: True si l'quipe joue  domicile

        Returns:
            Coefficients de corrlation et statistiques
        """
        # Filtrer par domicile/extrieur
        matches = [m for m in team_history if m['home'] == is_home]

        if len(matches) < 5:
            return {
                'error': 'Pas assez de matchs historiques',
                'min_required': 5,
                'found': len(matches)
            }

        # Pour chaque match, estimer le rang dfensif de l'adversaire  l'poque
        # (On utilise les rangs actuels comme approximation - pas parfait mais mieux que rien)
        X_defence = []  # Rangs dfensifs des adversaires (INVERSS)
        X_attack = []   # Rangs attaque de l'quipe (estim)
        y_shots = []
        y_corners = []

        for match in matches:
            opponent = match['opponent']

            # Estimer le rang dfensif de l'adversaire (utiliser rang actuel comme proxy)
            opponent_def_rank = self._get_team_rank(opponent, 'defence', current_rankings)

            # Filtrer les matchs sans donnes valides
            if opponent_def_rank > 0:
                X_defence.append(opponent_def_rank)
                y_shots.append(match['shots'])
                y_corners.append(match['corners'])

        if len(X_defence) < 5:
            return {
                'error': 'Pas assez de donnes valides',
                'matches_total': len(matches),
                'matches_valid': len(X_defence)
            }

        # INVERSER les rangs dfensifs pour corriger la logique
        # Rang 1 (meilleure dfense) devient valeur HAUTE (difficile  battre)
        # Rang 20 (pire dfense) devient valeur BASSE (facile  battre)
        max_rank = max(X_defence)
        X_defence_inverted = [(max_rank + 1) - rank for rank in X_defence]

        # Rgression linaire simple: y = ax + b
        # Tirs en fonction du rang dfensif adverse (INVERS)
        coeffs_shots = np.polyfit(X_defence_inverted, y_shots, 1)
        a_shots, b_shots = coeffs_shots

        # Calculer R pour mesurer la qualit de la corrlation
        y_pred_shots = np.polyval(coeffs_shots, X_defence_inverted)
        ss_res_shots = np.sum((np.array(y_shots) - y_pred_shots) ** 2)
        ss_tot_shots = np.sum((np.array(y_shots) - np.mean(y_shots)) ** 2)
        r2_shots = 1 - (ss_res_shots / ss_tot_shots) if ss_tot_shots > 0 else 0

        # Corners en fonction du rang dfensif adverse (INVERS)
        coeffs_corners = np.polyfit(X_defence_inverted, y_corners, 1)
        a_corners, b_corners = coeffs_corners

        y_pred_corners = np.polyval(coeffs_corners, X_defence_inverted)
        ss_res_corners = np.sum((np.array(y_corners) - y_pred_corners) ** 2)
        ss_tot_corners = np.sum((np.array(y_corners) - np.mean(y_corners)) ** 2)
        r2_corners = 1 - (ss_res_corners / ss_tot_corners) if ss_tot_corners > 0 else 0

        return {
            'shots': {
                'coefficient': a_shots,
                'intercept': b_shots,
                'r2': r2_shots,
                'formula': f'Tirs = {a_shots:.2f}  (qualit_dfense_inverse) + {b_shots:.2f}',
                'max_rank': max_rank  # Stocker pour utiliser lors de la prdiction
            },
            'corners': {
                'coefficient': a_corners,
                'intercept': b_corners,
                'r2': r2_corners,
                'formula': f'Corners = {a_corners:.2f}  (qualit_dfense_inverse) + {b_corners:.2f}',
                'max_rank': max_rank  # Stocker pour utiliser lors de la prdiction
            },
            'stats': {
                'matches_analyzed': len(X_defence),
                'avg_shots': np.mean(y_shots),
                'avg_corners': np.mean(y_corners),
                'location': 'home' if is_home else 'away'
            }
        }

    def analyze_correlation_multiple(self, team_history, current_rankings,
                                      team_name, is_home=True):
        """
        Régression MULTIPLE avec 3 variables au lieu d'une seule
    
        Variables:
        1. Rang offensif de l'équipe (offence_home ou offence_away)
        2. Rang défensif de l'adversaire (defence_away ou defence_home)
        3. Forme récente (form_last_8)
    
        Args:
            team_history: Historique des matchs
            current_rankings: Tous les classements soccerstats
            team_name: Nom de l'équipe
            is_home: True si domicile
    
        Returns:
            Dict avec coefficients et R²
        """
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score
    
        # Filtrer par domicile/extérieur
        matches = [m for m in team_history if m['home'] == is_home]
    
        if len(matches) < 5:
            return {
                'error': 'Pas assez de matchs historiques',
                'min_required': 5,
                'found': len(matches)
            }
    
        # VARIABLES
        X_defence = []   # Rang défensif adversaire
        X_offence = []   # Rang offensif équipe
        X_form = []      # Forme récente équipe
        y_shots = []
        y_corners = []
    
        # Types de classement selon domicile/extérieur
        offence_type = 'offence_home' if is_home else 'offence_away'
        defence_opponent_type = 'defence_away' if is_home else 'defence_home'
    
        for match in matches:
            opponent = match['opponent']
    
            # Récupérer les 3 rangs
            opponent_def_rank = self._get_team_rank(opponent, defence_opponent_type, current_rankings)
            team_off_rank = self._get_team_rank(team_name, offence_type, current_rankings)
            team_form_rank = self._get_team_rank(team_name, 'form_last_8', current_rankings)
    
            if opponent_def_rank > 0 and team_off_rank > 0 and team_form_rank > 0:
                X_defence.append(opponent_def_rank)
                X_offence.append(team_off_rank)
                X_form.append(team_form_rank)
                y_shots.append(match['shots'])
                y_corners.append(match['corners'])
    
        if len(X_defence) < 5:
            return {
                'error': 'Pas assez de données valides',
                'matches_total': len(matches),
                'matches_valid': len(X_defence)
            }
    
        # INVERSER les rangs (1 = meilleur → valeur haute)
        max_rank = 20
        X_defence_inv = [(max_rank + 1) - r for r in X_defence]
        X_offence_inv = [(max_rank + 1) - r for r in X_offence]
        X_form_inv = [(max_rank + 1) - r for r in X_form]
    
        # Matrice X (n_samples, 3_features)
        X = np.column_stack([X_offence_inv, X_defence_inv, X_form_inv])
    
        # REGRESSION MULTIPLE - TIRS
        model_shots = LinearRegression()
        model_shots.fit(X, y_shots)
        y_pred_shots = model_shots.predict(X)
        r2_shots = r2_score(y_shots, y_pred_shots)
    
        # REGRESSION MULTIPLE - CORNERS
        model_corners = LinearRegression()
        model_corners.fit(X, y_corners)
        y_pred_corners = model_corners.predict(X)
        r2_corners = r2_score(y_corners, y_pred_corners)
    
        # Extraire coefficients
        coef_shots = model_shots.coef_
        intercept_shots = model_shots.intercept_
        coef_corners = model_corners.coef_
        intercept_corners = model_corners.intercept_
    
        return {
            'shots': {
                'coef_offence': float(coef_shots[0]),
                'coef_defence': float(coef_shots[1]),
                'coef_form': float(coef_shots[2]),
                'intercept': float(intercept_shots),
                'r2': float(r2_shots),
                'formula': f'Tirs = {coef_shots[0]:.2f}×Attaque + {coef_shots[1]:.2f}×Défense_adv + {coef_shots[2]:.2f}×Forme + {intercept_shots:.2f}',
                'max_rank': max_rank,
                'model': model_shots
            },
            'corners': {
                'coef_offence': float(coef_corners[0]),
                'coef_defence': float(coef_corners[1]),
                'coef_form': float(coef_corners[2]),
                'intercept': float(intercept_corners),
                'r2': float(r2_corners),
                'formula': f'Corners = {coef_corners[0]:.2f}×Attaque + {coef_corners[1]:.2f}×Défense_adv + {coef_corners[2]:.2f}×Forme + {intercept_corners:.2f}',
                'max_rank': max_rank,
                'model': model_corners
            },
            'stats': {
                'matches_analyzed': len(X_defence),
                'avg_shots': float(np.mean(y_shots)),
                'avg_corners': float(np.mean(y_corners)),
                'location': 'home' if is_home else 'away'
            }
        }
    

    def _get_team_rank(self, team_name: str, ranking_type: str, rankings: Dict) -> int:
        """Rcupre le rang d'une quipe dans un classement"""
        if not rankings or ranking_type not in rankings:
            return 10  # Rang moyen par dfaut

        for team in rankings[ranking_type]:
            if team['team'].lower() == team_name.lower():
                return team['position']

        return 10  # Pas trouv = rang moyen

    def get_ai_tactical_adjustment(self,
                                   lambda_home_base: float,
                                   lambda_away_base: float,
                                   lambda_home_base_corners: float,
                                   lambda_away_base_corners: float,
                                   home_team: str,
                                   away_team: str,
                                   rdj_context: Optional[Dict],
                                   lineups: Optional[Dict],
                                   weather: Optional[Dict],
                                   is_derby: bool,
                                   current_rankings: Optional[Dict] = None,
                                   home_formation_stats: Optional[Dict] = None,
                                   away_formation_stats: Optional[Dict] = None) -> Dict:
        """
        IA qui RAISONNE sur tous les contextes et ajuste intelligemment TIRS ET CORNERS

        Args:
            lambda_home_base: Résultat Poisson brut tirs home
            lambda_away_base: Résultat Poisson brut tirs away
            lambda_home_base_corners: Résultat Poisson brut corners home
            lambda_away_base_corners: Résultat Poisson brut corners away
            home_team: Équipe domicile
            away_team: Équipe extérieur
            rdj_context: Contexte RDJ (blessures, analyses)
            lineups: Compositions confirmées (texte brut)
            weather: Météo
            is_derby: Si c'est un derby
            current_rankings: Classements actuels (12 tableaux soccerstats)
            home_formation_stats: Stats Understat formation équipe domicile
            away_formation_stats: Stats Understat formation équipe extérieur

        Returns:
            {
                'lambda_home_adjusted': 13.0,
                'lambda_away_adjusted': 9.0,
                'reasoning': "Explication du raisonnement"
            }
        """
        import anthropic
        import os

        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        # Préparer le contexte
        injuries_text = ""
        if rdj_context and rdj_context.get('injuries_text'):
            injuries_text = rdj_context['injuries_text'][:500]

        lineup_text = ""
        if lineups and lineups.get('lineup_raw_text'):
            lineup_text = lineups['lineup_raw_text'][:1000]

        weather_text = ""
        if weather:
            temp = weather.get('temperature', 15)
            conditions = weather.get('conditions', 'Temps clair')
            weather_text = f"{conditions}, {temp}°C"

        derby_text = "OUI - Derby local" if is_derby else "NON"

        # Construire le prompt enrichi
        prompt = f"""Tu es un analyste tactique football expert. Tu dois AJUSTER intelligemment un résultat de calcul mathématique en fonction du CONTEXTE RÉEL du match.

MATCH: {home_team} (DOMICILE) vs {away_team} (EXTÉRIEUR)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RÉSULTAT CALCULS POISSON (baseline mathématique):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{home_team}: {lambda_home_base:.1f} tirs attendus
{away_team}: {lambda_away_base:.1f} tirs attendus
Total: {lambda_home_base + lambda_away_base:.1f} tirs

Ce calcul est basé sur l'historique récent et les statistiques des équipes.
"""

        # SECTION 1: CLASSEMENTS (si disponibles)
        if current_rankings:
            prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1: CLASSEMENTS ACTUELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team}:
  - Classement général: {self._get_team_rank(home_team, 'standings', current_rankings)}e
  - Forme récente: {self._get_team_rank(home_team, 'form_last_8', current_rankings)}e
  - Attaque domicile: {self._get_team_rank(home_team, 'offence_home', current_rankings)}e
  - Défense domicile: {self._get_team_rank(home_team, 'defence_home', current_rankings)}e

{away_team}:
  - Classement général: {self._get_team_rank(away_team, 'standings', current_rankings)}e
  - Forme récente: {self._get_team_rank(away_team, 'form_last_8', current_rankings)}e
  - Attaque extérieur: {self._get_team_rank(away_team, 'offence_away', current_rankings)}e
  - Défense extérieur: {self._get_team_rank(away_team, 'defence_away', current_rankings)}e
"""

        # SECTION 2: FORMATIONS CONFIRMÉES (si disponibles)
        if home_formation_stats and away_formation_stats:
            prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2: FORMATIONS CONFIRMÉES (Statistiques Historiques)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ {home_team} joue en {home_formation_stats['formation']}:
  OFFENSIVE (quand ils attaquent):
    - Tirs/90: {home_formation_stats['shots_per_90']}
    - xG/90: {home_formation_stats['xg_per_90']}
    - Minutes jouées: {home_formation_stats['minutes']} ({home_formation_stats['percentage_used']}% du temps)

  DÉFENSIVE (quand ils défendent):
    - Tirs concédés/90: {home_formation_stats['shots_against_per_90']}
    - xGA/90: {home_formation_stats['xga_per_90']}

⚽ {away_team} joue en {away_formation_stats['formation']}:
  OFFENSIVE (quand ils attaquent):
    - Tirs/90: {away_formation_stats['shots_per_90']}
    - xG/90: {away_formation_stats['xg_per_90']}
    - Minutes jouées: {away_formation_stats['minutes']} ({away_formation_stats['percentage_used']}% du temps)

  DÉFENSIVE (quand ils défendent):
    - Tirs concédés/90: {away_formation_stats['shots_against_per_90']}
    - xGA/90: {away_formation_stats['xga_per_90']}

CALCUL BASELINE FORMATIONS (approche symétrique):

POUR {home_team}:
  - Offensive {home_team}: {home_formation_stats['shots_per_90']} tirs/90
  - Défensive {away_team}: concède {away_formation_stats['shots_against_per_90']} tirs/90
  - Moyenne: ({home_formation_stats['shots_per_90']} + {away_formation_stats['shots_against_per_90']}) / 2 = {(home_formation_stats['shots_per_90'] + away_formation_stats['shots_against_per_90']) / 2:.1f} tirs
  - Ratio xG: {home_formation_stats['xg_per_90']} / {away_formation_stats['xga_per_90']} = {home_formation_stats['xg_per_90'] / away_formation_stats['xga_per_90'] if away_formation_stats['xga_per_90'] > 0 else 'N/A':.2f} {"→ Dominance" if away_formation_stats['xga_per_90'] > 0 and home_formation_stats['xg_per_90'] / away_formation_stats['xga_per_90'] > 1.3 else ""}

POUR {away_team}:
  - Offensive {away_team}: {away_formation_stats['shots_per_90']} tirs/90
  - Défensive {home_team}: concède {home_formation_stats['shots_against_per_90']} tirs/90
  - Moyenne: ({away_formation_stats['shots_per_90']} + {home_formation_stats['shots_against_per_90']}) / 2 = {(away_formation_stats['shots_per_90'] + home_formation_stats['shots_against_per_90']) / 2:.1f} tirs
  - Ratio xG: {away_formation_stats['xg_per_90']} / {home_formation_stats['xga_per_90']} = {away_formation_stats['xg_per_90'] / home_formation_stats['xga_per_90'] if home_formation_stats['xga_per_90'] > 0 else 'N/A':.2f} {"→ Dominance" if home_formation_stats['xga_per_90'] > 0 and away_formation_stats['xg_per_90'] / home_formation_stats['xga_per_90'] > 1.3 else ""}
"""

        # SECTION 3: CONTEXTE ADDITIONNEL
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3: CONTEXTE ADDITIONNEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JOUEURS ABSENTS / BLESSURES:
{injuries_text if injuries_text else "Aucune information disponible"}

COMPOSITIONS CONFIRMÉES (texte brut):
{lineup_text if lineup_text else "Lineups non disponibles"}

DERBY:
{derby_text}

MÉTÉO:
{weather_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TON TRAVAIL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RAISONNE SYMÉTRIQUEMENT comme un expert et ajuste les résultats Poisson:

POUR {home_team}:
  ETAPE 1: Déterminer baseline
    - SI formations disponibles: utiliser baseline formations
      * Moyenne (offensive + défensive adverse) / 2
      * Valider avec ratio xG/xGA (dominance si > 1.3)
    - SINON: utiliser baseline Poisson historique (lambda_home_base = {lambda_home_base:.1f})

  ETAPE 2: Pondérer selon fiabilité des données
    - Formations avec >900 min: HAUTE fiabilité
    - Formations 450-900 min: MOYENNE fiabilité
    - Formations <450 min ou absentes: utiliser Poisson historique

  ETAPE 3: Ajuster avec contexte
    - Blessures: joueur clé absent → impact négatif
    - Classements: cohérence avec position
    - Derby: match tendu → légère réduction
    - Météo: conditions difficiles → légère réduction

POUR {away_team}:
  [MÊME PROCESSUS SYMÉTRIQUE]
  ETAPE 1: Baseline (formations si disponibles, sinon Poisson historique = {lambda_away_base:.1f})
  ETAPE 2: Pondérer selon fiabilité
  ETAPE 3: Ajuster avec contexte

BASELINE CORNERS POISSON:
  {home_team}: {lambda_home_base_corners:.1f} corners
  {away_team}: {lambda_away_base_corners:.1f} corners
  Total: {lambda_home_base_corners + lambda_away_base_corners:.1f} corners (~11 corners attendus)

CONTRAINTES IMPORTANTES:
TIRS:
- Le total des tirs doit rester entre 24 et 32 tirs
- Ne pas s'écarter de plus de ±4 tirs du baseline Poisson
CORNERS:
- Le total des corners doit rester entre 9 et 13 corners
- Ne pas s'écarter de plus de ±2 corners du baseline Poisson
GÉNÉRAL:
- Aucune équipe priorisée, raisonnement OBJECTIF
- Si formations disponibles, les prioriser (données réelles > historique général)
- Si formations manquantes, utiliser baseline Poisson avec ajustements contextuels uniquement

FORMAT DE RÉPONSE (JSON uniquement):
{{
  "lambda_home_adjusted": 15.5,
  "lambda_away_adjusted": 11.2,
  "lambda_home_adjusted_corners": 6.2,
  "lambda_away_adjusted_corners": 4.8,
  "reasoning": "Symétrique: {home_team} offensive+défensive {away_team} = X tirs, Y corners. {away_team} offensive+défensive {home_team} = Z tirs, W corners. Ajusté avec contexte."
}}

IMPORTANT: Retourne UNIQUEMENT le JSON, sans texte additionnel.

Analyse et ajuste maintenant:"""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = message.content[0].text.strip()

            # Parser le JSON
            import json
            import re

            # Extraire JSON (supporter les code blocks markdown)
            # Essayer d'abord avec ```json ... ```
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', result_text)
            if json_match:
                result_text = json_match.group(1)
            else:
                # Sinon chercher le JSON brut
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    result_text = json_match.group(0)

            result = json.loads(result_text)

            # Validation TIRS
            home_adj = result.get('lambda_home_adjusted', lambda_home_base)
            away_adj = result.get('lambda_away_adjusted', lambda_away_base)

            # Limites de sécurité TIRS
            home_adj = max(lambda_home_base - 4, min(lambda_home_base + 4, home_adj))
            away_adj = max(lambda_away_base - 4, min(lambda_away_base + 4, away_adj))

            # Vérifier contrainte totale TIRS (24-32 tirs)
            total = home_adj + away_adj
            if total < 24 or total > 32:
                # Réajuster proportionnellement
                target = 28
                ratio = target / total
                home_adj *= ratio
                away_adj *= ratio

            # Validation CORNERS
            home_adj_corners = result.get('lambda_home_adjusted_corners', lambda_home_base_corners)
            away_adj_corners = result.get('lambda_away_adjusted_corners', lambda_away_base_corners)

            # Limites de sécurité CORNERS
            home_adj_corners = max(lambda_home_base_corners - 2, min(lambda_home_base_corners + 2, home_adj_corners))
            away_adj_corners = max(lambda_away_base_corners - 2, min(lambda_away_base_corners + 2, away_adj_corners))

            # Vérifier contrainte totale CORNERS (9-13 corners)
            total_corners = home_adj_corners + away_adj_corners
            if total_corners < 9 or total_corners > 13:
                # Réajuster proportionnellement
                target_corners = 11
                ratio_corners = target_corners / total_corners
                home_adj_corners *= ratio_corners
                away_adj_corners *= ratio_corners

            reasoning = result.get('reasoning', '')

            print(f"\n[IA TACTIQUE] Ajustement intelligent:")
            print(f"  {home_team}: {lambda_home_base:.1f} -> {home_adj:.1f} tirs, {lambda_home_base_corners:.1f} -> {home_adj_corners:.1f} corners")
            print(f"  {away_team}: {lambda_away_base:.1f} -> {away_adj:.1f} tirs, {lambda_away_base_corners:.1f} -> {away_adj_corners:.1f} corners")
            # Encoder pour éviter erreurs Unicode sur Windows
            try:
                print(f"  Raisonnement: {reasoning[:200]}...")
            except UnicodeEncodeError:
                print(f"  Raisonnement: {reasoning.encode('ascii', errors='ignore').decode()[:200]}...")

            return {
                'lambda_home_adjusted': home_adj,
                'lambda_away_adjusted': away_adj,
                'lambda_home_adjusted_corners': home_adj_corners,
                'lambda_away_adjusted_corners': away_adj_corners,
                'reasoning': reasoning
            }

        except Exception as e:
            print(f"[WARNING] IA tactique echouee: {repr(e)}")
            # Fallback: garder baseline
            return {
                'lambda_home_adjusted': lambda_home_base,
                'lambda_away_adjusted': lambda_away_base,
                'lambda_home_adjusted_corners': lambda_home_base_corners,
                'lambda_away_adjusted_corners': lambda_away_base_corners,
                'reasoning': 'Ajustement IA non disponible, baseline Poisson conservé'
            }

    def analyze_poisson_bidirectional(self, home_history: List[Dict], away_history: List[Dict],
                                     current_rankings: Dict, home_team: str, away_team: str) -> Dict:
        """
        Modèle de Poisson BIDIRECTIONNEL pour prédire les tirs et corners

        Au lieu de 2 régressions indépendantes, ce modèle prédit :
        - λ_home (taux de tirs pour home)
        - λ_away (taux de tirs pour away)

        Avec la contrainte que λ_home + λ_away ≈ total réaliste (28 tirs, 11 corners)

        Modèle :
        λ_home = exp(β₀ + β₁×attaque_home + β₂×défense_away + β₃×forme_home)
        λ_away = exp(β₀ + β₁×attaque_away + β₂×défense_home + β₃×forme_away)

        Args:
            home_history: Historique matchs domicile
            away_history: Historique matchs extérieur
            current_rankings: Classements actuels
            home_team: Nom équipe domicile
            away_team: Nom équipe extérieur

        Returns:
            Dict avec paramètres Poisson pour home et away
        """

        # Préparer les données HOME
        home_matches = [m for m in home_history if m['home'] == True]

        if len(home_matches) < 5:
            return {'error': 'Pas assez de matchs historiques pour home', 'min_required': 5}

        # Préparer les données AWAY
        away_matches = [m for m in away_history if m['home'] == False]

        if len(away_matches) < 5:
            return {'error': 'Pas assez de matchs historiques pour away', 'min_required': 5}

        max_rank = 20

        # Collecter données HOME
        X_home = []
        y_shots_home = []
        y_corners_home = []

        for match in home_matches:
            opponent = match['opponent']
            team_off_rank = self._get_team_rank(home_team, 'offence_home', current_rankings)
            opp_def_rank = self._get_team_rank(opponent, 'defence_away', current_rankings)
            team_form_rank = self._get_team_rank(home_team, 'form_last_8', current_rankings)

            if team_off_rank > 0 and opp_def_rank > 0 and team_form_rank > 0:
                # Inverser (1 = meilleur → valeur haute)
                off_inv = (max_rank + 1) - team_off_rank
                def_inv = (max_rank + 1) - opp_def_rank
                form_inv = (max_rank + 1) - team_form_rank

                X_home.append([1.0, off_inv, def_inv, form_inv])  # Ajouter intercept (1.0)
                y_shots_home.append(match['shots'])
                y_corners_home.append(match['corners'])

        # Collecter données AWAY
        X_away = []
        y_shots_away = []
        y_corners_away = []

        for match in away_matches:
            opponent = match['opponent']
            team_off_rank = self._get_team_rank(away_team, 'offence_away', current_rankings)
            opp_def_rank = self._get_team_rank(opponent, 'defence_home', current_rankings)
            team_form_rank = self._get_team_rank(away_team, 'form_last_8', current_rankings)

            if team_off_rank > 0 and opp_def_rank > 0 and team_form_rank > 0:
                off_inv = (max_rank + 1) - team_off_rank
                def_inv = (max_rank + 1) - opp_def_rank
                form_inv = (max_rank + 1) - team_form_rank

                X_away.append([1.0, off_inv, def_inv, form_inv])  # Ajouter intercept (1.0)
                y_shots_away.append(match['shots'])
                y_corners_away.append(match['corners'])

        X_home = np.array(X_home)
        y_shots_home = np.array(y_shots_home)
        y_corners_home = np.array(y_corners_home)
        X_away = np.array(X_away)
        y_shots_away = np.array(y_shots_away)
        y_corners_away = np.array(y_corners_away)

        # Fonction de log-vraisemblance Poisson pour TIRS (bidirectionnel)
        def poisson_log_likelihood_shots(params):
            """
            Params = [β₀_home, β₁_home, β₂_home, β₃_home, β₀_away, β₁_away, β₂_away, β₃_away]
            """
            # Paramètres HOME
            beta_home = params[0:4]
            # Paramètres AWAY
            beta_away = params[4:8]

            # Prédictions λ (taux Poisson)
            lambda_home = np.exp(X_home @ beta_home)
            lambda_away = np.exp(X_away @ beta_away)

            # Log-vraisemblance Poisson : y*log(λ) - λ - log(y!)
            # On ignore log(y!) car constant
            ll_home = np.sum(y_shots_home * np.log(lambda_home + 1e-10) - lambda_home)
            ll_away = np.sum(y_shots_away * np.log(lambda_away + 1e-10) - lambda_away)

            # Contrainte : on veut que la moyenne de (λ_home + λ_away) ≈ 28
            avg_total = np.mean(lambda_home) + np.mean(lambda_away)
            penalty = 10 * (avg_total - 28)**2  # Pénalité si total != 28

            # Maximiser log-vraisemblance = minimiser négatif
            return -(ll_home + ll_away) + penalty

        # Fonction de log-vraisemblance Poisson pour CORNERS (bidirectionnel)
        def poisson_log_likelihood_corners(params):
            beta_home = params[0:4]
            beta_away = params[4:8]

            lambda_home = np.exp(X_home @ beta_home)
            lambda_away = np.exp(X_away @ beta_away)

            ll_home = np.sum(y_corners_home * np.log(lambda_home + 1e-10) - lambda_home)
            ll_away = np.sum(y_corners_away * np.log(lambda_away + 1e-10) - lambda_away)

            avg_total = np.mean(lambda_home) + np.mean(lambda_away)
            penalty = 10 * (avg_total - 11)**2  # Pénalité si total != 11 corners

            return -(ll_home + ll_away) + penalty

        # Valeurs initiales (régression linéaire simple comme point de départ)
        initial_params = np.array([0.5, 0.1, 0.1, 0.05, 0.5, 0.1, 0.1, 0.05])

        # Optimisation TIRS
        result_shots = minimize(
            poisson_log_likelihood_shots,
            initial_params,
            method='L-BFGS-B',
            options={'maxiter': 1000}
        )

        # Optimisation CORNERS
        result_corners = minimize(
            poisson_log_likelihood_corners,
            initial_params,
            method='L-BFGS-B',
            options={'maxiter': 1000}
        )

        return {
            'shots': {
                'beta_home': result_shots.x[0:4].tolist(),
                'beta_away': result_shots.x[4:8].tolist(),
                'success': result_shots.success,
                'log_likelihood': -result_shots.fun
            },
            'corners': {
                'beta_home': result_corners.x[0:4].tolist(),
                'beta_away': result_corners.x[4:8].tolist(),
                'success': result_corners.success,
                'log_likelihood': -result_corners.fun
            },
            'stats': {
                'home_matches_analyzed': len(X_home),
                'away_matches_analyzed': len(X_away),
                'avg_shots_home': float(np.mean(y_shots_home)),
                'avg_shots_away': float(np.mean(y_shots_away)),
                'avg_corners_home': float(np.mean(y_corners_home)),
                'avg_corners_away': float(np.mean(y_corners_away))
            },
            'max_rank': max_rank
        }

    def predict_match(self, home_team: str, away_team: str, league_code: str = "england",
                     match_date: Optional[datetime] = None) -> Dict:
        """
        PRDICTION DYNAMIQUE - Calcule tout en temps rel pour ce match spcifique

        Args:
            home_team: quipe  domicile
            away_team: quipe  l'extrieur
            league_code: england, spain, italy, france, germany
            match_date: Date du match (pour la mto)

        Returns:
            Prdiction complte avec explications
        """
        print(f"\n{'='*60}")
        print(f"[PREDICTION DYNAMIQUE] {home_team} vs {away_team}")
        print(f"{'='*60}")

        # 1. Rcuprer les classements ACTUELS
        print("\n tape 1: Rcupration des classements EN TEMPS REL...")
        current_rankings = self.get_current_rankings(league_code)

        if not current_rankings:
            return {'error': 'Impossible de rcuprer les classements actuels'}

        # 2. Charger l'historique des deux quipes
        print(f"\n tape 2: Chargement de l'historique des matchs...")
        home_history = self.load_team_history(home_team, self._get_league_csv_code(league_code))
        away_history = self.load_team_history(away_team, self._get_league_csv_code(league_code))

        print(f"    {home_team}: {len(home_history)} matchs trouvs")
        print(f"    {away_team}: {len(away_history)} matchs trouvs")

        if len(home_history) < 5 or len(away_history) < 5:
            return {
                'error': 'Pas assez de matchs historiques',
                'home_matches': len(home_history),
                'away_matches': len(away_history)
            }

        # 2c. NOUVEAU - Scraper Rue des Joueurs pour contexte blessures/analyses
        print(f"\n tape 2c: Rcupration du contexte Rue des Joueurs...")
        rdj_context = None
        try:
            # Convertir le league_code pour RDJ (england → E0, spain → SP1, etc.)
            rdj_league_code = self._get_league_csv_code(league_code)

            # Essayer de trouver l'URL du match
            rdj_url = rdj_finder.find_match_url(home_team, away_team, league_code=rdj_league_code)

            if rdj_url:
                print(f"    [OK] URL trouve: {rdj_url[:60]}...")
                # Scraper l'analyse
                rdj_data = rdj_scraper.scrape_match_preview(rdj_url)

                if rdj_data:
                    rdj_context = {
                        'url': rdj_url,
                        'injuries_text': rdj_data.get('injuries_text', ''),
                        'lineups_text': rdj_data.get('lineups_text', ''),
                        'full_text': rdj_data.get('full_text', ''),
                        'sections': rdj_data.get('sections', {})
                    }
                    print(f"    [OK] Analyse rcupre ({len(rdj_context['full_text'])} caractres)")
                    if rdj_context['injuries_text']:
                        print(f"    [INFO] Blessures/suspensions dtectes")
                else:
                    print(f"    [WARNING] chec scraping RDJ")
            else:
                print(f"    [INFO] Aucune analyse RDJ trouve pour ce match")
        except Exception as e:
            print(f"    [WARNING] Erreur RDJ: {e}")
            rdj_context = None

        # 2d. NOUVEAU - Récupérer stats détaillées soccerstats_working
        print(f"\n tape 2d: Rcupration des stats dtailles (W-D-L, buts, gaps)...")
        home_detailed_stats = None
        away_detailed_stats = None
        try:
            home_detailed_stats = soccerstats_working.get_team_context(home_team, league_code)
            away_detailed_stats = soccerstats_working.get_team_context(away_team, league_code)

            if home_detailed_stats:
                print(f"    {home_team}: {home_detailed_stats['won']}V-{home_detailed_stats['drawn']}N-{home_detailed_stats['lost']}D, "
                      f"{home_detailed_stats['goals_for']}-{home_detailed_stats['goals_against']} buts, "
                      f"{home_detailed_stats['points']} pts (pos {home_detailed_stats['position']})")
            if away_detailed_stats:
                print(f"    {away_team}: {away_detailed_stats['won']}V-{away_detailed_stats['drawn']}N-{away_detailed_stats['lost']}D, "
                      f"{away_detailed_stats['goals_for']}-{away_detailed_stats['goals_against']} buts, "
                      f"{away_detailed_stats['points']} pts (pos {away_detailed_stats['position']})")
        except Exception as e:
            print(f"    [WARNING] Erreur stats dtailles: {e}")

        # 3. NOUVEAU - Modle de Poisson BIDIRECTIONNEL
        print(f"\n tape 3: Modlisation Poisson bidirectionnelle...")
        poisson_model = self.analyze_poisson_bidirectional(
            home_history, away_history, current_rankings, home_team, away_team
        )

        if 'error' in poisson_model:
            return poisson_model

        print(f"    [OK] Modle Poisson entran")
        print(f"    Home matchs analyss: {poisson_model['stats']['home_matches_analyzed']}")
        print(f"    Away matchs analyss: {poisson_model['stats']['away_matches_analyzed']}")

        # 4. Rcuprer les rangs ACTUELS pour prdire CE match
        print(f"\n tape 4: Rcupration des rangs actuels...")

        max_rank = poisson_model['max_rank']

        # Rangs pour l'quipe  DOMICILE
        home_off_rank = self._get_team_rank(home_team, 'offence_home', current_rankings)
        home_form_rank = self._get_team_rank(home_team, 'form_last_8', current_rankings)
        away_def_rank = self._get_team_rank(away_team, 'defence_away', current_rankings)

        # Rangs pour l'quipe  L'EXTERIEUR
        away_off_rank = self._get_team_rank(away_team, 'offence_away', current_rankings)
        away_form_rank = self._get_team_rank(away_team, 'form_last_8', current_rankings)
        home_def_rank = self._get_team_rank(home_team, 'defence_home', current_rankings)

        # INVERSER tous les rangs (1 = meilleur → valeur haute)
        home_off_inv = (max_rank + 1) - home_off_rank
        away_def_inv = (max_rank + 1) - away_def_rank
        home_form_inv = (max_rank + 1) - home_form_rank

        away_off_inv = (max_rank + 1) - away_off_rank
        home_def_inv = (max_rank + 1) - home_def_rank
        away_form_inv = (max_rank + 1) - away_form_rank

        print(f"    {home_team}: Attaque={home_off_rank}({home_off_inv}), Dfense={home_def_rank}({home_def_inv}), Forme={home_form_rank}({home_form_inv})")
        print(f"    {away_team}: Attaque={away_off_rank}({away_off_inv}), Dfense={away_def_rank}({away_def_inv}), Forme={away_form_rank}({away_form_inv})")

        # 5. Calculer λ (taux Poisson) pour CE match
        print(f"\n tape 5: Calcul des prdictions (modle de Poisson)...")

        # Vecteur caractristiques HOME : [intercept, attaque_home, dfense_away, forme_home]
        X_home_match = np.array([1.0, home_off_inv, away_def_inv, home_form_inv])

        # Vecteur caractristiques AWAY : [intercept, attaque_away, dfense_home, forme_away]
        X_away_match = np.array([1.0, away_off_inv, home_def_inv, away_form_inv])

        # λ = exp(β · X)
        beta_shots_home = np.array(poisson_model['shots']['beta_home'])
        beta_shots_away = np.array(poisson_model['shots']['beta_away'])
        beta_corners_home = np.array(poisson_model['corners']['beta_home'])
        beta_corners_away = np.array(poisson_model['corners']['beta_away'])

        # Prdictions TIRS
        lambda_shots_home = np.exp(np.dot(beta_shots_home, X_home_match))
        lambda_shots_away = np.exp(np.dot(beta_shots_away, X_away_match))

        # Prdictions CORNERS
        lambda_corners_home = np.exp(np.dot(beta_corners_home, X_home_match))
        lambda_corners_away = np.exp(np.dot(beta_corners_away, X_away_match))

        home_shots_raw = float(lambda_shots_home)
        away_shots_raw = float(lambda_shots_away)
        home_corners_raw = float(lambda_corners_home)
        away_corners_raw = float(lambda_corners_away)

        print(f"    {home_team}: lambda_tirs={home_shots_raw:.1f}, lambda_corners={home_corners_raw:.1f}")
        print(f"    {away_team}: lambda_tirs={away_shots_raw:.1f}, lambda_corners={away_corners_raw:.1f}")
        print(f"    Total prdictions (base): {home_shots_raw + away_shots_raw:.1f} tirs, {home_corners_raw + away_corners_raw:.1f} corners")
        print(f"    NOTE: Le total est contraint  ~28 tirs et ~11 corners via le modle de Poisson")

        # 5b. NOUVEAU - Rcuprer mto pour ajustements contextuels
        print(f"\n tape 5b: Rcupration mto et analyse contexte...")
        city = self.collector.get_team_city(home_team)
        weather = self.collector.get_weather(city, match_date)
        print(f"    Mto  {city}: {weather['temperature']}C, vent {weather['wind_speed']} km/h, {weather['condition']}")

        # Sauvegarder les valeurs baseline Poisson (avant ajustement IA)
        baseline_home_shots = home_shots_raw
        baseline_away_shots = away_shots_raw

        # 5c. NOUVEAU - Récupérer les lineups (si disponibles en DB)
        lineups = None
        try:
            db = get_sqlite_db()
            effective_match_date = match_date if match_date else datetime.now()
            match_id = f"{self._get_league_csv_code(league_code)}_{effective_match_date.strftime('%Y%m%d')}_{home_team}_{away_team}".replace(' ', '_')
            lineups = db.get_lineup_by_match_id(match_id)

            if lineups:
                print(f"[INFO] Lineups trouvées en DB: {lineups.get('home_formation', 'N/A')} vs {lineups.get('away_formation', 'N/A')}")
            else:
                print(f"[INFO] Aucune lineup en DB pour ce match")
        except Exception as e:
            print(f"[WARNING] Erreur récupération lineups: {e}")
            lineups = None

        # 5d. NOUVEAU - IA de raisonnement tactique global
        print(f"\n tape 5d: Raisonnement IA tactique sur le contexte global...")

        # Détecter si c'est un derby via RDJ
        is_derby = False
        if rdj_context and rdj_context.get('full_text'):
            full_text = rdj_context['full_text'].lower()
            is_derby = any(word in full_text for word in ['derby', 'classique', 'choc', 'affiche'])

        # 5e. NOUVEAU - Récupérer stats formations Understat (si lineups disponibles)
        home_formation_stats = None
        away_formation_stats = None

        if lineups and lineups.get('lineup_raw_text'):
            try:
                print(f"\n    Extraction formations des lineups...")
                lineup_text = lineups['lineup_raw_text']

                # Validation du texte lineup
                if not lineup_text or len(lineup_text.strip()) == 0:
                    print(f"      [WARNING] Lineup vide ou invalide")
                else:
                    # Parser les formations (regex simple)
                    import re
                    formation_pattern = r'\b(\d+-\d+-\d+(?:-\d+)?)\b'
                    formations_found = re.findall(formation_pattern, lineup_text)

                    if len(formations_found) == 0:
                        print(f"      [INFO] Aucune formation trouvée dans le texte lineup")
                        print(f"      [INFO] L'IA utilisera l'historique général comme baseline")
                    elif len(formations_found) == 1:
                        print(f"      [WARNING] Une seule formation trouvée: {formations_found[0]}")
                        print(f"      [INFO] Impossible de récupérer stats Understat (besoin de 2 formations)")
                    elif len(formations_found) >= 2:
                        home_formation = formations_found[0]
                        away_formation = formations_found[1]
                        print(f"      Formations détectées:")
                        print(f"        {home_team}: {home_formation}")
                        print(f"        {away_team}: {away_formation}")

                        # Récupérer stats Understat pour ces formations
                        try:
                            from services.understat_service import get_understat_service
                            understat = get_understat_service()

                            # Déterminer la saison (année en cours ou précédente selon la date)
                            current_year = datetime.now().year
                            if isinstance(match_date, str):
                                match_year = int(match_date.split('-')[0]) if '-' in match_date else current_year
                            else:
                                match_year = match_date.year if hasattr(match_date, 'year') else current_year

                            # Understat utilise l'année de début de saison (ex: 2024 pour 2024/2025)
                            season = match_year if match_date.month >= 8 else match_year - 1

                            print(f"      Requête Understat saison {season}...")
                            home_formation_stats = understat.get_formation_stats(home_team, home_formation, season)
                            away_formation_stats = understat.get_formation_stats(away_team, away_formation, season)

                            # Gérer les cas partiels
                            if home_formation_stats and away_formation_stats:
                                print(f"\n      [OK] Stats Understat récupérées pour les 2 équipes:")
                                print(f"        {home_team} {home_formation}: {home_formation_stats['shots_per_90']} tirs/90, xG/90={home_formation_stats['xg_per_90']}")
                                print(f"        {away_team} {away_formation}: {away_formation_stats['shots_per_90']} tirs/90, xG/90={away_formation_stats['xg_per_90']}")
                            elif home_formation_stats and not away_formation_stats:
                                print(f"      [WARNING] Stats disponibles uniquement pour {home_team}")
                                print(f"        L'IA utilisera les stats partielles avec prudence")
                            elif away_formation_stats and not home_formation_stats:
                                print(f"      [WARNING] Stats disponibles uniquement pour {away_team}")
                                print(f"        L'IA utilisera les stats partielles avec prudence")
                            else:
                                print(f"      [INFO] Stats Understat non disponibles pour ces formations")
                                print(f"      [INFO] Possible: formations jamais utilisées cette saison ou équipe non suivie")

                        except ImportError as e:
                            print(f"      [ERROR] Service Understat non disponible: {e}")
                            home_formation_stats = None
                            away_formation_stats = None
                        except Exception as e:
                            print(f"      [WARNING] Erreur lors de la récupération Understat: {e}")
                            logger.error(f"[Formations] Erreur Understat pour {home_team} vs {away_team}: {e}")
                            home_formation_stats = None
                            away_formation_stats = None

            except Exception as e:
                print(f"      [ERROR] Erreur extraction formations: {e}")
                logger.error(f"[Formations] Erreur parsing lineup pour {home_team} vs {away_team}: {e}")
                home_formation_stats = None
                away_formation_stats = None

        # L'IA raisonne sur tous les contextes et ajuste intelligemment TIRS ET CORNERS
        if lineups or rdj_context or weather:
            tactical_result = self.get_ai_tactical_adjustment(
                lambda_home_base=home_shots_raw,
                lambda_away_base=away_shots_raw,
                lambda_home_base_corners=home_corners_raw,
                lambda_away_base_corners=away_corners_raw,
                home_team=home_team,
                away_team=away_team,
                rdj_context=rdj_context,
                lineups=lineups,
                weather=weather,
                is_derby=is_derby,
                current_rankings=current_rankings,
                home_formation_stats=home_formation_stats,
                away_formation_stats=away_formation_stats
            )

            home_shots_adjusted = tactical_result['lambda_home_adjusted']
            away_shots_adjusted = tactical_result['lambda_away_adjusted']
            home_corners_adjusted = tactical_result.get('lambda_home_adjusted_corners', home_corners_raw)
            away_corners_adjusted = tactical_result.get('lambda_away_adjusted_corners', away_corners_raw)
            tactical_reasoning = tactical_result['reasoning']

            print(f"\n    Baseline Poisson:")
            print(f"      {home_team}: {home_shots_raw:.1f} tirs, {home_corners_raw:.1f} corners")
            print(f"      {away_team}: {away_shots_raw:.1f} tirs, {away_corners_raw:.1f} corners")
            print(f"\n    Aprs raisonnement IA:")
            print(f"      {home_team}: {home_shots_raw:.1f} -> {home_shots_adjusted:.1f} tirs, {home_corners_raw:.1f} -> {home_corners_adjusted:.1f} corners")
            print(f"      {away_team}: {away_shots_raw:.1f} -> {away_shots_adjusted:.1f} tirs, {away_corners_raw:.1f} -> {away_corners_adjusted:.1f} corners")
            print(f"      Total: {home_shots_adjusted + away_shots_adjusted:.1f} tirs, {home_corners_adjusted + away_corners_adjusted:.1f} corners")
            # Encoder pour éviter erreurs Unicode sur Windows
            try:
                print(f"\n    Raisonnement: {tactical_reasoning[:150]}...")
            except UnicodeEncodeError:
                print(f"\n    Raisonnement: {tactical_reasoning.encode('ascii', errors='ignore').decode()[:150]}...")
        else:
            # Pas de contexte disponible, garder baseline
            home_shots_adjusted = home_shots_raw
            away_shots_adjusted = away_shots_raw
            home_corners_adjusted = home_corners_raw
            away_corners_adjusted = away_corners_raw
            tactical_reasoning = "Baseline Poisson conservé (aucun contexte disponible)"
            print(f"    Aucun contexte disponible, baseline Poisson conserv")

        # Utiliser les valeurs ajustées
        home_shots_raw = home_shots_adjusted
        away_shots_raw = away_shots_adjusted
        home_corners_raw = home_corners_adjusted
        away_corners_raw = away_corners_adjusted

        # 6. Estimer la possession (informatif)
        print(f"\n tape 6: Estimation de la possession...")
        home_possession, away_possession = self._estimate_possession_split(
            home_off_rank, away_off_rank,
            home_def_rank, away_def_rank,
            max_rank
        )
        print(f"    Possession estime: {home_team} {home_possession*100:.1f}% - {away_team} {away_possession*100:.1f}%")

        # 7. Interprtation impact mto (informatif)
        print(f"\n tape 7: Interprtation impact mto...")

        # Interprtation de l'impact (informatif, pas de calcul)
        weather_impact = self._interpret_weather_impact(weather)
        print(f"    Impact potentiel: {weather_impact}")

        # Prédictions finales (déjà ajustées pour blessures/derbies)
        home_shots = max(0, home_shots_raw)
        home_corners = max(0, home_corners_raw)
        away_shots = max(0, away_shots_raw)
        away_corners = max(0, away_corners_raw)

        # Calculer fourchettes par équipe (±15% pour créer une plage réaliste)
        variance_shots = 0.15  # 15% de variance
        variance_corners = 0.15

        home_shots_min = int(max(0, home_shots * (1 - variance_shots)))
        home_shots_max = int(home_shots * (1 + variance_shots))
        away_shots_min = int(max(0, away_shots * (1 - variance_shots)))
        away_shots_max = int(away_shots * (1 + variance_shots))

        home_corners_min = int(max(0, home_corners * (1 - variance_corners)))
        home_corners_max = int(home_corners * (1 + variance_corners))
        away_corners_min = int(max(0, away_corners * (1 - variance_corners)))
        away_corners_max = int(away_corners * (1 + variance_corners))

        # 8. Construire le rsultat
        result = {
            'match': {
                'home_team': home_team,
                'away_team': away_team,
                'league': league_code,
                'date': match_date.isoformat() if match_date else None
            },
            'predictions': {
                'home_shots': round(home_shots, 1),
                'home_corners': round(home_corners, 1),
                'away_shots': round(away_shots, 1),
                'away_corners': round(away_corners, 1),
                'home_shots_min': home_shots_min,
                'home_shots_max': home_shots_max,
                'away_shots_min': away_shots_min,
                'away_shots_max': away_shots_max,
                'home_corners_min': home_corners_min,
                'home_corners_max': home_corners_max,
                'away_corners_min': away_corners_min,
                'away_corners_max': away_corners_max,
                'total_shots': round(home_shots + away_shots, 1),
                'total_corners': round(home_corners + away_corners, 1),
                'baseline_home_shots': round(baseline_home_shots, 1),
                'baseline_away_shots': round(baseline_away_shots, 1)
            },
            'confidence': {
                'model_type': 'Poisson bidirectionnel',
                'shots_log_likelihood': round(poisson_model['shots']['log_likelihood'], 2),
                'corners_log_likelihood': round(poisson_model['corners']['log_likelihood'], 2),
                'shots_optimization_success': poisson_model['shots']['success'],
                'corners_optimization_success': poisson_model['corners']['success'],
                'note': 'Confiance basée sur log-vraisemblance du modèle de Poisson (plus élevé = meilleur)'
            },
            'analysis': {
                'home_team': {
                    'matches_analyzed': poisson_model['stats']['home_matches_analyzed'],
                    'model': 'Poisson: λ = exp(β₀ + β₁×Attaque + β₂×Défense_adv + β₃×Forme)',
                    'avg_shots_historical': round(poisson_model['stats']['avg_shots_home'], 1),
                    'avg_corners_historical': round(poisson_model['stats']['avg_corners_home'], 1),
                    'opponent_defence_rank': away_def_rank,
                    'match_history': [m for m in home_history if m['home'] == True][:30]
                },
                'away_team': {
                    'matches_analyzed': poisson_model['stats']['away_matches_analyzed'],
                    'model': 'Poisson: λ = exp(β₀ + β₁×Attaque + β₂×Défense_adv + β₃×Forme)',
                    'avg_shots_historical': round(poisson_model['stats']['avg_shots_away'], 1),
                    'avg_corners_historical': round(poisson_model['stats']['avg_corners_away'], 1),
                    'opponent_defence_rank': home_def_rank,
                    'match_history': [m for m in away_history if m['home'] == False][:30]
                }
            },
            'context': {
                'weather': {
                    **weather,
                    'impact_description': weather_impact  # Description de l'impact (informatif UNIQUEMENT)
                },
                'detailed_stats': {
                    'home': home_detailed_stats,
                    'away': away_detailed_stats
                },
                'adjustments': {
                    'model_type': 'Poisson bidirectionnel + IA tactique',
                    'possession_home': round(home_possession * 100, 1),
                    'possession_away': round(away_possession * 100, 1),
                    'total_shots_constraint': 28.0,
                    'total_corners_constraint': 11.0,
                    'tactical_reasoning': tactical_reasoning,
                    'note': 'Modèle de Poisson bidirectionnel avec contrainte sur le total (~28 tirs, ~11 corners). IA analyse blessures, lineups, derbies et météo pour ajuster intelligemment le résultat.'
                }
            },
            'rankings_used': {
                'home_attack_rank': self._get_team_rank(home_team, 'offence_home', current_rankings),
                'away_attack_rank': self._get_team_rank(away_team, 'offence_away', current_rankings),
                'home_defence_rank': home_def_rank,
                'away_defence_rank': away_def_rank,
                'timestamp': datetime.now().isoformat()
            }
        }

        # 9. Gnrer le raisonnement IA (Deep Reasoning)
        print(f"\n tape 8: Gnration du raisonnement IA profond...")
        try:
            ai_result = generate_deep_analysis_prediction(
                match={
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': league_code
                },
                home_history=home_history,
                away_history=away_history,
                current_rankings=current_rankings,
                rdj_context=rdj_context,  # Contexte complet avec blessures/analyses RDJ
                weather=weather,
                detailed_stats={
                    'home': home_detailed_stats,
                    'away': away_detailed_stats
                },
                lineups=lineups,  # Compositions confirmées si disponibles
                home_formation_stats=home_formation_stats,  # Stats Understat formation domicile
                away_formation_stats=away_formation_stats  # Stats Understat formation extérieur
            )

            # Ajouter le raisonnement IA au rsultat
            result['predictions']['ai_reasoning_shots'] = ai_result.get('full_reasoning', '')
            result['predictions']['ai_reasoning_corners'] = ai_result.get('full_reasoning', '')

            # Prédictions séparées par équipe
            result['predictions']['ai_home_shots_min'] = ai_result.get('home_shots_min')
            result['predictions']['ai_home_shots_max'] = ai_result.get('home_shots_max')
            result['predictions']['ai_home_corners_min'] = ai_result.get('home_corners_min')
            result['predictions']['ai_home_corners_max'] = ai_result.get('home_corners_max')

            result['predictions']['ai_away_shots_min'] = ai_result.get('away_shots_min')
            result['predictions']['ai_away_shots_max'] = ai_result.get('away_shots_max')
            result['predictions']['ai_away_corners_min'] = ai_result.get('away_corners_min')
            result['predictions']['ai_away_corners_max'] = ai_result.get('away_corners_max')

            # Total (pour compatibilité)
            result['predictions']['ai_shots_min'] = ai_result.get('home_shots_min', 0) + ai_result.get('away_shots_min', 0)
            result['predictions']['ai_shots_max'] = ai_result.get('home_shots_max', 0) + ai_result.get('away_shots_max', 0)
            result['predictions']['ai_corners_min'] = ai_result.get('home_corners_min', 0) + ai_result.get('away_corners_min', 0)
            result['predictions']['ai_corners_max'] = ai_result.get('home_corners_max', 0) + ai_result.get('away_corners_max', 0)

            result['predictions']['ai_confidence'] = ai_result.get('confidence', 0)

            print(f"    [OK] Raisonnement IA gnr ({len(ai_result.get('full_reasoning', ''))//100*100}+ caractres)")
            print(f"    IA suggre:")
            print(f"      {home_team}: {ai_result.get('home_shots_min')}-{ai_result.get('home_shots_max')} tirs, {ai_result.get('home_corners_min')}-{ai_result.get('home_corners_max')} corners")
            print(f"      {away_team}: {ai_result.get('away_shots_min')}-{ai_result.get('away_shots_max')} tirs, {ai_result.get('away_corners_min')}-{ai_result.get('away_corners_max')} corners")
            print(f"      Total: {result['predictions']['ai_shots_min']}-{result['predictions']['ai_shots_max']} tirs")

        except Exception as e:
            print(f"    [WARNING] chec gnration IA: {e}")
            result['predictions']['ai_reasoning_shots'] = None
            result['predictions']['ai_reasoning_corners'] = None

        print(f"\n Prdiction termine!")
        print(f"    {home_team}: {result['predictions']['home_shots']} tirs, {result['predictions']['home_corners']} corners")
        print(f"    {away_team}: {result['predictions']['away_shots']} tirs, {result['predictions']['away_corners']} corners")
        print(f"\n     Mto (informatif): {weather_impact}")
        print(f"{'='*60}\n")

        return result

    def _interpret_weather_impact(self, weather: Dict) -> str:
        """
        Interprte l'impact potentiel de la mto (INFORMATIF UNIQUEMENT)

        Args:
            weather: Donnes mto {temperature, wind_speed, precipitation, condition}

        Returns:
            Description textuelle de l'impact potentiel
        """
        temp = weather.get('temperature', 15)
        wind = weather.get('wind_speed', 10)
        rain = weather.get('precipitation', 0)

        impacts = []

        # Temprature
        if temp < 5:
            impacts.append("Froid intense - joueurs moins ractifs, muscles raides")
        elif temp < 10:
            impacts.append("Froid - peut affecter le contrle du ballon")
        elif temp > 30:
            impacts.append("Chaleur intense - fatigue rapide, dshydratation")
        elif temp > 25:
            impacts.append("Chaleur - endurance rduite en fin de match")
        else:
            impacts.append("Temprature idale - conditions optimales")

        # Vent
        if wind > 40:
            impacts.append("Vent trs fort - trajectoires imprvisibles, corners difficiles")
        elif wind > 25:
            impacts.append("Vent fort - peut affecter les passes longues et centres")
        elif wind > 15:
            impacts.append("Vent modr - impact minimal")

        # Pluie
        if rain > 5:
            impacts.append("Pluie forte - terrain glissant, ballon difficile  contrler")
        elif rain > 1:
            impacts.append("Pluie lgre - pelouse humide, quelques glissades possibles")

        return " | ".join(impacts) if impacts else "Conditions normales"

    def _estimate_possession_split(self, home_off_rank: int, away_off_rank: int,
                                   home_def_rank: int, away_def_rank: int,
                                   max_rank: int = 20) -> Tuple[float, float]:
        """
        Estime le % de possession basé sur les forces offensives/défensives

        Logique :
        - Équipe avec meilleure attaque + meilleure défense = plus de possession
        - Possession ≈ contrôle du ballon ≈ opportunités de tirer

        Args:
            home_off_rank: Rang offensif domicile (1 = meilleur)
            away_off_rank: Rang offensif extérieur
            home_def_rank: Rang défensif domicile
            away_def_rank: Rang défensif extérieur
            max_rank: Nombre d'équipes dans le championnat

        Returns:
            (home_possession, away_possession) - somme = 1.0
        """
        # Score composite : moyenne des rangs (plus bas = meilleur)
        # Une bonne attaque garde le ballon, une bonne défense le récupère
        home_control_score = (home_off_rank + home_def_rank) / 2
        away_control_score = (away_off_rank + away_def_rank) / 2

        # Convertir en % de possession (entre 35-65% pour réalisme)
        # Plus le score est BAS, plus la possession est HAUTE
        total_score = home_control_score + away_control_score

        if total_score == 0:
            return 0.5, 0.5

        # Inversion : meilleur score (bas) → haute possession
        # away_control / total donne la part de "faiblesse" de away
        # ce qui correspond à la "force" de home
        home_possession = 0.35 + (0.30 * (away_control_score / total_score))
        away_possession = 1.0 - home_possession

        return home_possession, away_possession

    def _normalize_total_shots(self, home_shots: float, away_shots: float,
                              expected_total: float = 28.0) -> Tuple[float, float]:
        """
        Force le total de tirs à être réaliste

        Un match typique = 25-30 tirs totaux (toutes compétitions confondues)
        Si home + away est aberrant, ajuste proportionnellement

        Args:
            home_shots: Tirs prédits pour domicile
            away_shots: Tirs prédits pour extérieur
            expected_total: Total attendu pour un match typique

        Returns:
            (home_normalized, away_normalized) - total ≈ expected_total
        """
        current_total = home_shots + away_shots

        if current_total <= 0:
            return home_shots, away_shots

        # Facteur de normalisation
        adjustment_factor = expected_total / current_total

        # Limiter l'ajustement pour éviter des changements trop brutaux
        # Si le total est dans une fourchette acceptable (23-33), ajustement léger
        if 23 <= current_total <= 33:
            adjustment_factor = 0.7 + (0.3 * adjustment_factor)  # Ajustement partiel

        return home_shots * adjustment_factor, away_shots * adjustment_factor

    def _normalize_total_corners(self, home_corners: float, away_corners: float,
                                expected_total: float = 11.0) -> Tuple[float, float]:
        """
        Force le total de corners à être réaliste

        Un match typique = 10-12 corners totaux

        Args:
            home_corners: Corners prédits pour domicile
            away_corners: Corners prédits pour extérieur
            expected_total: Total attendu pour un match typique

        Returns:
            (home_normalized, away_normalized) - total ≈ expected_total
        """
        current_total = home_corners + away_corners

        if current_total <= 0:
            return home_corners, away_corners

        adjustment_factor = expected_total / current_total

        # Limiter l'ajustement si dans fourchette acceptable (9-13)
        if 9 <= current_total <= 13:
            adjustment_factor = 0.7 + (0.3 * adjustment_factor)

        return home_corners * adjustment_factor, away_corners * adjustment_factor

    def _get_league_csv_code(self, soccerstats_code: str) -> str:
        """Convertit le code soccerstats vers le code CSV"""
        mapping = {
            'england': 'E0',
            'spain': 'SP1',
            'italy': 'I1',
            'france': 'F1',
            'germany': 'D1'
        }
        return mapping.get(soccerstats_code, 'E0')


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    predictor = DynamicPredictor()

    result = predictor.predict_match(
        home_team="Tottenham",
        away_team="Arsenal",
        league_code="england"
    )

    if 'error' not in result:
        print("\n RSULTAT COMPLET:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
