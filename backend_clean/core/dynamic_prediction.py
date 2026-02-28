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

import scrapers.soccerstats_overview as soccerstats_overview
import scrapers.soccerstats_working as soccerstats_working
from core.data_collector import DataCollector
from core.formation_analyzer import FormationAnalyzer
import scrapers.sofascore_api as sofascore_api


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

    def predict_match(self, home_team: str, away_team: str, league_code: str = "england",
                     match_date: Optional[datetime] = None,
                     home_formation: Optional[str] = None,
                     away_formation: Optional[str] = None) -> Dict:
        """
        PRDICTION DYNAMIQUE - Calcule tout en temps rel pour ce match spcifique

        Args:
            home_team: quipe  domicile
            away_team: quipe  l'extrieur
            league_code: england, spain, italy, france, germany
            match_date: Date du match (pour la mto)
            home_formation: Formation quipe domicile (ex: "4-3-3") - si None, utilise dfaut
            away_formation: Formation quipe extrieur (ex: "5-3-2") - si None, utilise dfaut

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

        # 2b. Enrichir avec les formations (si activ)
        if self.use_formations:
            print(f"\n tape 2b: Enrichissement avec formations (peut prendre du temps)...")
            # Note: On limite  50 matchs pour ne pas tre trop lent
            home_history = self.formation_analyzer.enrich_history_with_formations(
                home_history[:50], home_team
            )
            away_history = self.formation_analyzer.enrich_history_with_formations(
                away_history[:50], away_team
            )

        if len(home_history) < 5 or len(away_history) < 5:
            return {
                'error': 'Pas assez de matchs historiques',
                'home_matches': len(home_history),
                'away_matches': len(away_history)
            }

        # 3. Analyser la corrlation pour l'quipe  domicile
        print(f"\n tape 3: Analyse de corrlation pour {home_team} (domicile)...")
        home_correlation = self.analyze_correlation_multiple(home_history, current_rankings, home_team, is_home=True)

        if 'error' in home_correlation:
            return home_correlation

        # 4. Analyser la corrlation pour l'quipe  l'extrieur
        print(f"\n tape 4: Analyse de corrlation pour {away_team} (extrieur)...")
        away_correlation = self.analyze_correlation_multiple(away_history, current_rankings, away_team, is_home=False)

        if 'error' in away_correlation:
            return away_correlation

        # 5. Rcuprer les rangs dfensifs ACTUELS des adversaires
        print(f"\n tape 5: Rcupration des rangs dfensifs ACTUELS...")
        away_def_rank = self._get_team_rank(away_team, 'defence_away', current_rankings)
        home_def_rank = self._get_team_rank(home_team, 'defence_home', current_rankings)

        print(f"    {away_team} (dfense extrieur): {away_def_rank}e")
        print(f"    {home_team} (dfense domicile): {home_def_rank}e")

        # 6. Calculer les prdictions brutes (REGRESSION MULTIPLE)
        print(f"\n tape 6: Calcul des prdictions...")

        # Rcuprer TOUS les rangs ncessaires pour la rgression multiple
        max_rank = 20

        # Rangs pour l'quipe  DOMICILE
        home_off_rank = self._get_team_rank(home_team, 'offence_home', current_rankings)
        home_form_rank = self._get_team_rank(home_team, 'form_last_8', current_rankings)

        # Rangs pour l'quipe  L'EXTERIEUR
        away_off_rank = self._get_team_rank(away_team, 'offence_away', current_rankings)
        away_form_rank = self._get_team_rank(away_team, 'form_last_8', current_rankings)

        # INVERSER tous les rangs (1 = meilleur → valeur haute)
        home_off_inv = (max_rank + 1) - home_off_rank
        away_def_inv = (max_rank + 1) - away_def_rank
        home_form_inv = (max_rank + 1) - home_form_rank

        away_off_inv = (max_rank + 1) - away_off_rank
        home_def_inv = (max_rank + 1) - home_def_rank
        away_form_inv = (max_rank + 1) - away_form_rank

        print(f"    {home_team}: Attaque={home_off_rank}({home_off_inv}), Forme={home_form_rank}({home_form_inv})")
        print(f"    {away_team}: Dfense={away_def_rank}({away_def_inv})")
        print(f"    {away_team}: Attaque={away_off_rank}({away_off_inv}), Forme={away_form_rank}({away_form_inv})")
        print(f"    {home_team}: Dfense={home_def_rank}({home_def_inv})")

        # Prdiction quipe DOMICILE (3 variables)
        # Tirs = coef_offence×Attaque_home + coef_defence×Dfense_away + coef_form×Forme_home + intercept
        home_shots_raw = (
            home_correlation['shots']['coef_offence'] * home_off_inv +
            home_correlation['shots']['coef_defence'] * away_def_inv +
            home_correlation['shots']['coef_form'] * home_form_inv +
            home_correlation['shots']['intercept']
        )
        home_corners_raw = (
            home_correlation['corners']['coef_offence'] * home_off_inv +
            home_correlation['corners']['coef_defence'] * away_def_inv +
            home_correlation['corners']['coef_form'] * home_form_inv +
            home_correlation['corners']['intercept']
        )

        # Prdiction quipe EXTERIEUR (3 variables)
        away_shots_raw = (
            away_correlation['shots']['coef_offence'] * away_off_inv +
            away_correlation['shots']['coef_defence'] * home_def_inv +
            away_correlation['shots']['coef_form'] * away_form_inv +
            away_correlation['shots']['intercept']
        )
        away_corners_raw = (
            away_correlation['corners']['coef_offence'] * away_off_inv +
            away_correlation['corners']['coef_defence'] * home_def_inv +
            away_correlation['corners']['coef_form'] * away_form_inv +
            away_correlation['corners']['intercept']
        )

        # 7. Rcuprer les donnes contextuelles EN TEMPS REL
        print(f"\n tape 7: Rcupration des donnes contextuelles...")

        # Mto du jour (INFORMATIF UNIQUEMENT - pas d'ajustement)
        city = self.collector.get_team_city(home_team)
        weather = self.collector.get_weather(city, match_date)
        print(f"    Mto  {city}: {weather['temperature']}C, vent {weather['wind_speed']} km/h, {weather['condition']}")

        # Interprtation de l'impact (informatif, pas de calcul)
        weather_impact = self._interpret_weather_impact(weather)
        print(f"    Impact potentiel: {weather_impact}")

        # 7b. Rcuprer les formations prvues (si disponibles)
        formation_shots_factor = 1.0
        formation_corners_factor = 1.0
        formation_analysis = None

        if self.use_formations:
            print(f"\n tape 7b: Utilisation des formations...")

            # Utiliser les formations passées en paramètre OU défaut
            if not home_formation:
                home_formation = '4-3-3'  # Défaut
                print(f"     {home_team}: 4-3-3 (defaut)")
            else:
                print(f"     {home_team}: {home_formation}")

            if not away_formation:
                away_formation = '4-3-3'  # Défaut
                print(f"     {away_team}: 4-3-3 (defaut)")
            else:
                print(f"     {away_team}: {away_formation}")

            try:
                if home_formation and away_formation:
                    # Calculer les facteurs RELS  partir des donnes historiques
                    home_shots_f, home_corners_f, home_stats = (
                        self.formation_analyzer.get_formation_factor_from_data(
                            home_formation, away_formation, home_history
                        )
                    )

                    away_shots_f, away_corners_f, away_stats = (
                        self.formation_analyzer.get_formation_factor_from_data(
                            away_formation, home_formation, away_history
                        )
                    )

                    # Utiliser les facteurs de l'quipe  domicile (principale)
                    formation_shots_factor = home_shots_f
                    formation_corners_factor = home_corners_f
                    formation_analysis = {
                        'home_stats': home_stats,
                        'away_stats': away_stats
                    }

                    print(f"\n    Analyse {home_team} en {home_formation}:")
                    print(f"      Matchs analyss: {home_stats.get('matches_analyzed', 0)}")
                    if home_stats.get('method') == 'data_driven':
                        print(f"      Moy. tirs (cette formation): {home_stats.get('avg_shots_with_formation', 0)}")
                        print(f"      Moy. tirs (toutes formations): {home_stats.get('avg_shots_global', 0)}")
                        print(f"       Facteur tirs: {home_shots_f:.3f} ({home_stats.get('shots_change_pct', 0):+.1f}%)")
                        print(f"       Facteur corners: {home_corners_f:.3f} ({home_stats.get('corners_change_pct', 0):+.1f}%)")
                    else:
                        print(f"       {home_stats.get('reason', 'Donnes insuffisantes')}")
                else:
                    print(f"     Formations non disponibles encore")
            except Exception as e:
                print(f"     Erreur rcupration formations: {e}")

        # Appliquer SEULEMENT l'ajustement formations (PAS mto)
        home_shots = max(0, home_shots_raw * formation_shots_factor)
        home_corners = max(0, home_corners_raw * formation_corners_factor)
        away_shots = max(0, away_shots_raw * formation_shots_factor)
        away_corners = max(0, away_corners_raw * formation_corners_factor)

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
                'total_shots': round(home_shots + away_shots, 1),
                'total_corners': round(home_corners + away_corners, 1)
            },
            'confidence': {
                'home_shots_r2': round(home_correlation['shots']['r2'], 3),
                'home_corners_r2': round(home_correlation['corners']['r2'], 3),
                'away_shots_r2': round(away_correlation['shots']['r2'], 3),
                'away_corners_r2': round(away_correlation['corners']['r2'], 3),
                'overall': round((home_correlation['shots']['r2'] +
                                home_correlation['corners']['r2'] +
                                away_correlation['shots']['r2'] +
                                away_correlation['corners']['r2']) / 4, 3)
            },
            'analysis': {
                'home_team': {
                    'matches_analyzed': home_correlation['stats']['matches_analyzed'],
                    'formula_shots': home_correlation['shots']['formula'],
                    'formula_corners': home_correlation['corners']['formula'],
                    'opponent_defence_rank': away_def_rank,
                    'match_history': [m for m in home_history if m['home'] == True][:30]
                },
                'away_team': {
                    'matches_analyzed': away_correlation['stats']['matches_analyzed'],
                    'formula_shots': away_correlation['shots']['formula'],
                    'formula_corners': away_correlation['corners']['formula'],
                    'opponent_defence_rank': home_def_rank,
                    'match_history': [m for m in away_history if m['home'] == False][:30]
                }
            },
            'context': {
                'weather': {
                    **weather,
                    'impact_description': weather_impact  # Description de l'impact (informatif)
                },
                'formations': {
                    'home_formation': home_formation,
                    'away_formation': away_formation,
                    'home_type': self.formation_analyzer.classify_formation(home_formation) if home_formation else None,
                    'away_type': self.formation_analyzer.classify_formation(away_formation) if away_formation else None,
                    'analysis': formation_analysis  # Statistiques RELLES
                },
                'adjustments': {
                    'formation_shots_factor': round(formation_shots_factor, 3),
                    'formation_corners_factor': round(formation_corners_factor, 3),
                    'note': 'Mto non utilise dans le calcul - affiche  titre informatif uniquement'
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

        print(f"\n Prdiction termine!")
        print(f"    {home_team}: {result['predictions']['home_shots']} tirs, {result['predictions']['home_corners']} corners")
        if home_formation:
            print(f"     Formation: {home_formation} ({result['context']['formations']['home_type']})")
        print(f"    {away_team}: {result['predictions']['away_shots']} tirs, {result['predictions']['away_corners']} corners")
        if away_formation:
            print(f"     Formation: {away_formation} ({result['context']['formations']['away_type']})")
        print(f"    Confiance globale: {result['confidence']['overall']:.1%}")
        if home_formation and away_formation:
            print(f"    Ajustement formations: {formation_shots_factor:.2f}x (tirs), {formation_corners_factor:.2f}x (corners)")
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
