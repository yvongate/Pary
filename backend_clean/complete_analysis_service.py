"""
Service d'Analyse Complte - Analyse les 2 quipes sparment pour TIRS et CORNERS

Structure:
- Analyse TIRS: home + away + conclusion
- Analyse CORNERS: home + away + conclusion
"""

from typing import Dict, List, Tuple
from datetime import datetime
import time
import os

from core.dynamic_prediction import DynamicPredictor
from core.data_collector import DataCollector
import scrapers.soccerstats_overview
import scrapers.ruedesjoueurs_finder
import core.ai_deep_reasoning


class CompleteAnalysisService:
    """
    Service qui fait l'analyse complte pour un match:
    - Analyse TIRS (2 quipes + conclusion)
    - Analyse CORNERS (2 quipes + conclusion)
    """

    def __init__(self):
        self.predictor = DynamicPredictor(use_formations=False)  # Formations désactivées
        self.collector = DataCollector()

    def analyze_match(self, home_team: str, away_team: str, league_code: str,
                     match_date: datetime = None) -> Dict:
        """
        Analyse COMPLTE d'un match (tirs ET corners)

        Args:
            home_team: quipe  domicile
            away_team: quipe  l'extrieur
            league_code: Code championnat (england, spain, etc.)
            match_date: Date du match

        Returns:
            {
                'shots_analysis': {...},  # Analyse tirs
                'corners_analysis': {...},  # Analyse corners
                'predictions': {...},  # Prdictions finales
                'metadata': {...}  # Mtadonnes
            }
        """
        print(f"\n{'='*70}")
        print(f"[ANALYSE COMPLETE] {home_team} vs {away_team}")
        print(f"{'='*70}\n")

        start_time = time.time()

        # 1. Faire la prdiction complte
        print("[ETAPE 1] Prediction dynamique...")
        prediction_result = self.predictor.predict_match(
            home_team=home_team,
            away_team=away_team,
            league_code=league_code,
            match_date=match_date or datetime.now()
        )

        if 'error' in prediction_result:
            return {'error': prediction_result['error']}

        # 2. Rcuprer CONTEXTE et JOUEURS ABSENTS depuis Rue des Joueurs
        print("\n[ETAPE 2] Recuperation contexte Rue des Joueurs...")
        rdj_data = self._get_ruedesjoueurs_context(home_team, away_team, league_code)

        # 3. Analyser TIRS (2 quipes + conclusion)
        print("\n[ETAPE 3] Analyse detaillee TIRS...")
        shots_analysis = self._analyze_shots(
            home_team, away_team, prediction_result, rdj_data
        )

        # 4. Analyser CORNERS (2 quipes + conclusion)
        print("\n[ETAPE 4] Analyse detaillee CORNERS...")
        corners_analysis = self._analyze_corners(
            home_team, away_team, prediction_result, rdj_data
        )

        # 5. Calculer intervalles de confiance
        print("\n[ETAPE 5] Calcul des intervalles...")
        shots_interval = self._calculate_confidence_interval(
            prediction_result['predictions']['home_shots'] +
            prediction_result['predictions']['away_shots'],
            prediction_result['confidence']['overall']
        )

        corners_interval = self._calculate_confidence_interval(
            prediction_result['predictions']['home_corners'] +
            prediction_result['predictions']['away_corners'],
            prediction_result['confidence']['overall']
        )

        # NOUVELLE ETAPE: VERIFICATION IA DEEP REASONING
        print("\n[ETAPE 6] Verification IA - Raisonnement profond...")

        # Recuperer historique complet et classements
        league_csv = self.predictor._get_league_csv_code(league_code)
        home_history = self.predictor.load_team_history(home_team, league_csv)
        away_history = self.predictor.load_team_history(away_team, league_csv)
        current_rankings = self.predictor.get_current_rankings(league_code)

        ai_verification = ai_deep_reasoning.generate_deep_analysis_prediction(
            match={
                'home_team': home_team,
                'away_team': away_team,
                'league': league_code
            },
            home_history=home_history,
            away_history=away_history,
            current_rankings=current_rankings,
            rdj_context=rdj_data,
            weather=prediction_result.get('context', {}).get('weather'),
            formations={
                'home_formation': prediction_result.get('context', {}).get('formations', {}).get('home'),
                'away_formation': prediction_result.get('context', {}).get('formations', {}).get('away')
            }
        )

        # Comparaison des predictions
        calc_shots = (shots_interval['min'] + shots_interval['max']) / 2
        ai_shots = (ai_verification['shots_min'] + ai_verification['shots_max']) / 2
        shots_diff = abs(calc_shots - ai_shots)
        shots_agreement = 100 - min(100, (shots_diff / calc_shots) * 100)

        calc_corners = (corners_interval['min'] + corners_interval['max']) / 2
        ai_corners = (ai_verification['corners_min'] + ai_verification['corners_max']) / 2
        corners_diff = abs(calc_corners - ai_corners)
        corners_agreement = 100 - min(100, (corners_diff / calc_corners) * 100)

        print(f"   [COMPARAISON]")
        print(f"   Calcul: {shots_interval['min']}-{shots_interval['max']} tirs")
        print(f"   IA: {ai_verification['shots_min']}-{ai_verification['shots_max']} tirs")
        print(f"   Accord: {shots_agreement:.0f}%")

        execution_time = time.time() - start_time

        result = {
            'match': {
                'home_team': home_team,
                'away_team': away_team,
                'league': league_code,
                'match_date': match_date.isoformat() if match_date else None
            },

            # Analyse TIRS complte
            'shots_analysis': shots_analysis,

            # Analyse CORNERS complte
            'corners_analysis': corners_analysis,

            # Prdictions finales
            'predictions': {
                'shots': {
                    'min': shots_interval['min'],
                    'max': shots_interval['max'],
                    'confidence': prediction_result['confidence']['overall'],
                    'predicted_value': prediction_result['predictions']['home_shots'] +
                                      prediction_result['predictions']['away_shots']
                },
                'corners': {
                    'min': corners_interval['min'],
                    'max': corners_interval['max'],
                    'confidence': prediction_result['confidence']['overall'],
                    'predicted_value': prediction_result['predictions']['home_corners'] +
                                      prediction_result['predictions']['away_corners']
                }
            },

            # Verification IA avec raisonnement profond
            'ai_verification': {
                'shots_min': ai_verification['shots_min'],
                'shots_max': ai_verification['shots_max'],
                'corners_min': ai_verification['corners_min'],
                'corners_max': ai_verification['corners_max'],
                'confidence': ai_verification['confidence'],
                'reasoning': ai_verification.get('full_reasoning', ''),
                'agreement_shots': round(shots_agreement, 1),
                'agreement_corners': round(corners_agreement, 1)
            },

            # Mtadonnes
            'metadata': {
                'execution_time_seconds': round(execution_time, 2),
                'formations_used': prediction_result['context']['formations'],
                'weather': prediction_result['context']['weather'],
                'rankings_used': prediction_result['rankings_used'],
                'ruedesjoueurs_used': rdj_data is not None,
                'ai_verification_used': 'error' not in ai_verification,
                'created_at': datetime.now().isoformat()
            }
        }

        # Ajouter contexte Rue des Joueurs si disponible
        if rdj_data:
            result['metadata']['ruedesjoueurs_context'] = {
                'injuries': rdj_data.get('injuries_summary', 'Aucune info'),
                'preview_length': len(rdj_data.get('full_text', ''))
            }

        print(f"\n[OK] Analyse terminee en {execution_time:.2f}s")
        return result

    def _get_ruedesjoueurs_context(self, home_team: str, away_team: str, league_code: str = None) -> Dict:
        """
        Rcupre le contexte et joueurs absents depuis Rue des Joueurs
        NOUVEAU: Scraping direct GRATUIT (sans SerpAPI)

        Args:
            home_team: quipe  domicile
            away_team: quipe  l'extrieur
            league_code: Code ligue (E0, SP1, I1, F1, D1)

        Returns:
            Dictionnaire avec contexte ou None
        """
        try:
            if not league_code:
                print("     League code non fourni - contexte RDJ desactive")
                return None

            # Chercher et scraper l'analyse (GRATUIT - sans SerpAPI)
            print(f"     Recherche {home_team} vs {away_team}...")
            rdj_analysis = ruedesjoueurs_finder.get_match_analysis_auto(
                home_team, away_team, league_code=league_code
            )

            if not rdj_analysis:
                print("     Aucune analyse trouvee sur Rue des Joueurs")
                return None

            print(f"     [OK] Analyse recuperee ({len(rdj_analysis.get('full_text', ''))} caracteres)")

            # Extraire rsumer des joueurs absents
            injuries_text = rdj_analysis.get('injuries_text', '')
            injuries_summary = ""
            if injuries_text:
                # Limiter  500 caractres
                injuries_summary = injuries_text[:500]
                if len(injuries_text) > 500:
                    injuries_summary += "..."

            return {
                'full_text': rdj_analysis.get('full_text', ''),
                'sections': rdj_analysis.get('sections', {}),
                'injuries_text': injuries_text,
                'injuries_summary': injuries_summary,
                'lineups_text': rdj_analysis.get('lineups_text', ''),
                'url': rdj_analysis.get('url', '')
            }

        except Exception as e:
            print(f"     Erreur recuperation RDJ: {e}")
            return None

    def _analyze_shots(self, home_team: str, away_team: str, prediction: Dict, rdj_data: Dict = None) -> Dict:
        """
        Analyse TIRS - 2 quipes + conclusion

        Returns:
            {
                'home_team_analysis': {...},
                'away_team_analysis': {...},
                'conclusion': str
            }
        """
        home_analysis = self._analyze_team_shots(
            home_team,
            prediction['analysis']['home_team'],
            prediction['predictions']['home_shots'],
            prediction['confidence']['home_shots_r2'],
            is_home=True
        )

        away_analysis = self._analyze_team_shots(
            away_team,
            prediction['analysis']['away_team'],
            prediction['predictions']['away_shots'],
            prediction['confidence']['away_shots_r2'],
            is_home=False
        )

        # Conclusion globale
        total_shots = prediction['predictions']['home_shots'] + prediction['predictions']['away_shots']
        conclusion = self._generate_shots_conclusion(
            home_team, away_team, home_analysis, away_analysis, total_shots
        )

        return {
            'home_team_analysis': home_analysis,
            'away_team_analysis': away_analysis,
            'conclusion': conclusion
        }

    def _analyze_corners(self, home_team: str, away_team: str, prediction: Dict, rdj_data: Dict = None) -> Dict:
        """
        Analyse CORNERS - 2 quipes + conclusion

        Returns:
            {
                'home_team_analysis': {...},
                'away_team_analysis': {...},
                'conclusion': str
            }
        """
        home_analysis = self._analyze_team_corners(
            home_team,
            prediction['analysis']['home_team'],
            prediction['predictions']['home_corners'],
            prediction['confidence']['home_corners_r2'],
            is_home=True
        )

        away_analysis = self._analyze_team_corners(
            away_team,
            prediction['analysis']['away_team'],
            prediction['predictions']['away_corners'],
            prediction['confidence']['away_corners_r2'],
            is_home=False
        )

        # Conclusion globale
        total_corners = prediction['predictions']['home_corners'] + prediction['predictions']['away_corners']
        conclusion = self._generate_corners_conclusion(
            home_team, away_team, home_analysis, away_analysis, total_corners
        )

        return {
            'home_team_analysis': home_analysis,
            'away_team_analysis': away_analysis,
            'conclusion': conclusion
        }

    def _analyze_team_shots(self, team_name: str, team_analysis: Dict,
                           predicted_shots: float, confidence: float,
                           is_home: bool) -> Dict:
        """
        Analyse TIRS pour UNE quipe

        Returns:
            {
                'team': str,
                'predicted_shots': float,
                'confidence': float,
                'steps': [...],
                'conclusion': str
            }
        """
        steps = [
            {
                'step': 1,
                'action': f"Chargement historique {team_name}",
                'result': f"{team_analysis['matches_analyzed']} matchs analyss"
            },
            {
                'step': 2,
                'action': "Analyse corrlation tirs/dfense adverse",
                'result': f"Formule: {team_analysis['formula_shots']}"
            },
            {
                'step': 3,
                'action': "Rcupration rang dfensif adversaire",
                'result': f"Adversaire class {team_analysis['opponent_defence_rank']}e en dfense"
            },
            {
                'step': 4,
                'action': "Calcul prdiction brute",
                'result': f"~{predicted_shots:.1f} tirs prdits"
            },
            {
                'step': 5,
                'action': "valuation confiance",
                'result': f"R = {confidence:.3f} ({'Excellente' if confidence > 0.85 else 'Bonne' if confidence > 0.7 else 'Acceptable'} corrlation)"
            }
        ]

        location = " domicile" if is_home else " l'extrieur"

        # Crer une analyse DTAILLE match-par-match
        history = team_analysis.get('match_history', [])
        detailed_analysis = self._create_detailed_match_analysis(history, 'shots')

        conclusion = (
            f"{team_name} {location} - Analyse dtaille de {len(history)} matchs:\n"
            f"{detailed_analysis}\n"
            f"Prdiction finale: {predicted_shots:.1f} tirs (confiance {confidence:.1%})"
        )

        return {
            'team': team_name,
            'predicted_shots': round(predicted_shots, 1),
            'confidence': round(confidence, 3),
            'location': location,
            'steps': steps,
            'conclusion': conclusion
        }

    def _analyze_team_corners(self, team_name: str, team_analysis: Dict,
                             predicted_corners: float, confidence: float,
                             is_home: bool) -> Dict:
        """
        Analyse CORNERS pour UNE quipe

        Returns:
            {
                'team': str,
                'predicted_corners': float,
                'confidence': float,
                'steps': [...],
                'conclusion': str
            }
        """
        steps = [
            {
                'step': 1,
                'action': f"Chargement historique {team_name}",
                'result': f"{team_analysis['matches_analyzed']} matchs analyss"
            },
            {
                'step': 2,
                'action': "Analyse corrlation corners/dfense adverse",
                'result': f"Formule: {team_analysis['formula_corners']}"
            },
            {
                'step': 3,
                'action': "Rcupration rang dfensif adversaire",
                'result': f"Adversaire class {team_analysis['opponent_defence_rank']}e en dfense"
            },
            {
                'step': 4,
                'action': "Calcul prdiction brute",
                'result': f"~{predicted_corners:.1f} corners prdits"
            },
            {
                'step': 5,
                'action': "valuation confiance",
                'result': f"R = {confidence:.3f} ({'Excellente' if confidence > 0.85 else 'Bonne' if confidence > 0.7 else 'Acceptable'} corrlation)"
            }
        ]

        location = " domicile" if is_home else " l'extrieur"

        # Crer une analyse DTAILLE match-par-match
        history = team_analysis.get('match_history', [])
        detailed_analysis = self._create_detailed_match_analysis(history, 'corners')

        conclusion = (
            f"{team_name} {location} - Analyse dtaille de {len(history)} matchs:\n"
            f"{detailed_analysis}\n"
            f"Prdiction finale: {predicted_corners:.1f} corners (confiance {confidence:.1%})"
        )

        return {
            'team': team_name,
            'predicted_corners': round(predicted_corners, 1),
            'confidence': round(confidence, 3),
            'location': location,
            'steps': steps,
            'conclusion': conclusion
        }

    def _generate_shots_conclusion(self, home_team: str, away_team: str,
                                   home_analysis: Dict, away_analysis: Dict,
                                   total_shots: float) -> str:
        """Gnre la conclusion globale pour les TIRS"""
        home_shots = home_analysis['predicted_shots']
        away_shots = away_analysis['predicted_shots']

        if home_shots > away_shots * 1.5:
            dominance = f"{home_team} devrait largement dominer"
        elif home_shots > away_shots * 1.2:
            dominance = f"{home_team} devrait dominer"
        elif away_shots > home_shots * 1.2:
            dominance = f"{away_team} devrait dominer"
        else:
            dominance = "Match quilibr"

        return (
            f"Au total, environ {total_shots:.0f} tirs sont attendus dans ce match. "
            f"{dominance} avec {home_shots:.1f} tirs contre {away_shots:.1f}. "
            f"Confiances: {home_analysis['confidence']:.1%} (dom.) et {away_analysis['confidence']:.1%} (ext.)."
        )

    def _generate_corners_conclusion(self, home_team: str, away_team: str,
                                     home_analysis: Dict, away_analysis: Dict,
                                     total_corners: float) -> str:
        """Gnre la conclusion globale pour les CORNERS"""
        home_corners = home_analysis['predicted_corners']
        away_corners = away_analysis['predicted_corners']

        if total_corners > 12:
            intensity = "Beaucoup de corners"
        elif total_corners > 9:
            intensity = "Nombre normal de corners"
        else:
            intensity = "Peu de corners"

        return (
            f"Au total, environ {total_corners:.0f} corners sont attendus. "
            f"{intensity}: {home_corners:.1f} pour {home_team} et {away_corners:.1f} pour {away_team}. "
            f"Confiances: {home_analysis['confidence']:.1%} (dom.) et {away_analysis['confidence']:.1%} (ext.)."
        )

    def _calculate_confidence_interval(self, predicted_value: float, confidence: float) -> Dict:
        """
        Calcule l'intervalle de confiance (min/max)

        Args:
            predicted_value: Valeur prdite
            confidence: Score de confiance (R)

        Returns:
            {'min': int, 'max': int}
        """
        # Marge d'erreur selon la confiance
        if confidence >= 0.85:
            margin_pct = 0.15  # 15%
        elif confidence >= 0.70:
            margin_pct = 0.20  # 20%
        else:
            margin_pct = 0.25  # 25%

        margin = predicted_value * margin_pct

        return {
            'min': max(0, int(predicted_value - margin)),
            'max': int(predicted_value + margin) + 1  # +1 pour arrondir au-dessus
        }

    def _create_detailed_match_analysis(self, match_history: List[Dict], metric: str) -> str:
        """
        Cre une analyse DTAILLE match-par-match (pas de moyennes!)

        Args:
            match_history: Liste des matchs historiques
            metric: 'shots' ou 'corners'

        Returns:
            Texte d'analyse dtaille
        """
        if not match_history or len(match_history) == 0:
            return "Historique insuffisant pour analyse dtaille."

        # Limiter  30 matchs les plus rcents pour ne pas surcharger
        recent_matches = match_history[:30]

        analysis_lines = []

        # Grouper par adversaire pour trouver des patterns
        opponents_data = {}
        for match in recent_matches:
            opponent = match.get('opponent', 'Inconnu')
            value = match.get(metric, 0)

            if opponent not in opponents_data:
                opponents_data[opponent] = []
            opponents_data[opponent].append({
                'value': value,
                'goals_for': match.get('goals_for'),
                'goals_against': match.get('goals_against'),
                'date': match.get('date', '')
            })

        # Crer l'analyse dtaille
        analysis_lines.append(f"Comparaison DTAILLE des {len(recent_matches)} derniers matchs:")

        for opponent, matches_vs_opponent in list(opponents_data.items())[:15]:  # Top 15 adversaires
            if len(matches_vs_opponent) == 1:
                m = matches_vs_opponent[0]
                score_info = ""
                if m['goals_for'] is not None and m['goals_against'] is not None:
                    score_info = f" (score: {m['goals_for']}-{m['goals_against']})"

                analysis_lines.append(
                    f"  - Vs {opponent}: {m['value']} {metric}{score_info}"
                )
            else:
                values = [m['value'] for m in matches_vs_opponent]
                avg = sum(values) / len(values)

                analysis_lines.append(
                    f"  - Vs {opponent} ({len(matches_vs_opponent)}x): {', '.join(map(str, values))} {metric} (moy: {avg:.1f})"
                )

        # Ajouter stats globales
        all_values = [m.get(metric, 0) for m in recent_matches]
        min_val = min(all_values)
        max_val = max(all_values)
        median_val = sorted(all_values)[len(all_values) // 2]

        analysis_lines.append(f"\nStats globales: min={min_val}, max={max_val}, mdiane={median_val}")

        return "\n".join(analysis_lines)


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    service = CompleteAnalysisService()

    result = service.analyze_match(
        home_team="Tottenham",
        away_team="Arsenal",
        league_code="england"
    )

    if 'error' not in result:
        print("\n" + "=" * 70)
        print("[RESULTATS] ANALYSE")
        print("=" * 70)

        # Afficher rsultats tirs
        print("\n[TIRS]")
        print(f"  Min: {result['predictions']['shots']['min']}")
        print(f"  Max: {result['predictions']['shots']['max']}")
        print(f"  Confiance: {result['predictions']['shots']['confidence']:.1%}")

        # Afficher rsultats corners
        print("\n[CORNERS]")
        print(f"  Min: {result['predictions']['corners']['min']}")
        print(f"  Max: {result['predictions']['corners']['max']}")
        print(f"  Confiance: {result['predictions']['corners']['confidence']:.1%}")

        print("\n" + "=" * 70)
