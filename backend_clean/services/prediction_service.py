"""
Service de prédictions - Orchestre l'analyse complète
Combine analysis dynamique, formations, IA et sauvegarde BDD
"""
from typing import Dict, Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.database_service import get_database
from services.ai_service import get_ai_service
from services.lineup_service import get_lineup_service
from complete_analysis_service import CompleteAnalysisService
from config.settings import settings


class PredictionService:
    """Service principal de génération de prédictions"""

    def __init__(self):
        self.db = get_database()
        self.ai = get_ai_service()
        self.lineup = get_lineup_service()
        self.analysis = CompleteAnalysisService()

    def generate_prediction_for_match(self, match: Dict) -> Optional[int]:
        """
        Génère une prédiction complète pour un match

        Args:
            match: {
                'match_id': str,
                'home_team': str,
                'away_team': str,
                'league_code': str,
                'match_date': datetime
            }

        Returns:
            ID de la prédiction créée ou None
        """
        print(f"\n{'='*70}")
        print(f"MATCH: {match['home_team']} vs {match['away_team']}")
        print(f"{'='*70}")

        # 1. Vérifier si prédiction existe déjà
        existing = self.db.get_prediction_by_match_id(match['match_id'])
        if existing:
            print("[INFO] Prédiction déjà existante")
            return existing.get('id')

        # 2. Récupérer les compositions
        print("\n[COMPOSITIONS] Vérification disponibilité...")
        lineups = self._get_lineups(match)

        if not lineups:
            print("[ATTENTE] Compositions indisponibles - utilisation formations par défaut")
            lineups = {
                'home_formation': '4-3-3',
                'away_formation': '4-3-3',
                'source': 'default'
            }

        print(f"[OK] Compositions:")
        print(f"   - {match['home_team']}: {lineups.get('home_formation', 'N/A')}")
        print(f"   - {match['away_team']}: {lineups.get('away_formation', 'N/A')}")
        print(f"   - Source: {lineups.get('source', 'N/A')}")

        # 3. Analyse complète
        print("\n[ANALYSE] Lancement analyse complète...")
        soccerstats_code = settings.SOCCERSTATS_CODES.get(match['league_code'], 'england')

        analysis_result = self.analysis.analyze_match(
            home_team=match['home_team'],
            away_team=match['away_team'],
            league_code=soccerstats_code,
            match_date=match['match_date']
        )

        if 'error' in analysis_result:
            print(f"[ERREUR] Analyse: {analysis_result['error']}")
            return None

        # 4. Génération textes IA
        print("\n[IA] Génération analyses IA...")

        ai_shots = self.ai.generate_shots_reasoning(analysis_result)
        print(f"   [OK] Analyse TIRS générée ({len(ai_shots)} caractères)")

        ai_corners = self.ai.generate_corners_reasoning(analysis_result)
        print(f"   [OK] Analyse CORNERS générée ({len(ai_corners)} caractères)")

        # 5. Préparation des données
        prediction_data = {
            'match_id': match['match_id'],
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'league_code': match['league_code'],
            'match_date': match['match_date'],

            # Prédictions TIRS
            'shots_min': analysis_result['predictions']['shots']['min'],
            'shots_max': analysis_result['predictions']['shots']['max'],
            'shots_confidence': analysis_result['predictions']['shots']['confidence'],

            # Prédictions CORNERS
            'corners_min': analysis_result['predictions']['corners']['min'],
            'corners_max': analysis_result['predictions']['corners']['max'],
            'corners_confidence': analysis_result['predictions']['corners']['confidence'],

            # Analyses détaillées
            'analysis_shots': analysis_result['shots_analysis'],
            'analysis_corners': analysis_result['corners_analysis'],

            # Textes IA
            'ai_reasoning_shots': ai_shots,
            'ai_reasoning_corners': ai_corners,

            # Métadonnées
            'home_formation': lineups.get('home_formation'),
            'away_formation': lineups.get('away_formation'),
            'weather': analysis_result['metadata'].get('weather'),
            'rankings_used': analysis_result['metadata'].get('rankings_used')
        }

        # 6. Sauvegarde en BDD
        print("\n[BDD] Sauvegarde dans Supabase...")
        pred_id = self.db.insert_prediction(prediction_data)

        if pred_id:
            print(f"[OK] Prédiction sauvegardée (ID: {pred_id})")
        else:
            print("[ERREUR] Échec sauvegarde BDD")

        return pred_id

    def _get_lineups(self, match: Dict) -> Optional[Dict]:
        """
        Récupère les compositions pour un match via SerpAPI

        Args:
            match: Info du match

        Returns:
            {home_formation, away_formation} ou None
        """
        try:
            lineups = self.lineup.get_lineups_simple(
                match['home_team'],
                match['away_team']
            )

            # Vérifier qu'on a au moins les formations
            if lineups and (lineups.get('home_formation') or lineups.get('away_formation')):
                return lineups

        except Exception as e:
            print(f"[ERREUR] Récupération compositions: {e}")

        return None

    def get_upcoming_predictions(self, league_code: Optional[str] = None, limit: int = 20) -> list:
        """
        Récupère les prédictions à venir formatées pour l'API

        Args:
            league_code: Code de la ligue (optionnel)
            limit: Nombre max de résultats

        Returns:
            Liste des prédictions formatées
        """
        predictions = self.db.get_upcoming_predictions(league_code, limit)

        formatted = []
        for pred in predictions:
            formatted.append({
                'match_id': pred['match_id'],
                'home_team': pred['home_team'],
                'away_team': pred['away_team'],
                'league_code': pred['league_code'],
                'match_date': pred['match_date'].isoformat() if pred['match_date'] else None,

                'shots': {
                    'min': pred['shots_min'],
                    'max': pred['shots_max'],
                    'confidence': float(pred['shots_confidence']),
                    'home_team_message': f"{pred['home_team']} fera PLUS de {pred.get('home_shots_min', 'N/A')} et MOINS de {pred.get('home_shots_max', 'N/A')} tirs",
                    'away_team_message': f"{pred['away_team']} fera PLUS de {pred.get('away_shots_min', 'N/A')} et MOINS de {pred.get('away_shots_max', 'N/A')} tirs",
                    'message_min': f"Total: Il y aura PLUS de {pred['shots_min']} tirs",
                    'message_max': f"Total: Il y aura MOINS de {pred['shots_max']} tirs"
                },

                'corners': {
                    'min': pred['corners_min'],
                    'max': pred['corners_max'],
                    'confidence': float(pred['corners_confidence']),
                    'home_team_message': f"{pred['home_team']} fera PLUS de {pred.get('home_corners_min', 'N/A')} et MOINS de {pred.get('home_corners_max', 'N/A')} corners",
                    'away_team_message': f"{pred['away_team']} fera PLUS de {pred.get('away_corners_min', 'N/A')} et MOINS de {pred.get('away_corners_max', 'N/A')} corners",
                    'message_min': f"Total: Il y aura PLUS de {pred['corners_min']} corners",
                    'message_max': f"Total: Il y aura MOINS de {pred['corners_max']} corners"
                },

                'ai_reasoning_shots': pred.get('ai_reasoning_shots'),
                'ai_reasoning_corners': pred.get('ai_reasoning_corners'),

                'formations': {
                    'home': pred.get('home_formation'),
                    'away': pred.get('away_formation')
                } if pred.get('home_formation') else None,

                'created_at': pred['created_at'].isoformat() if pred.get('created_at') else None
            })

        return formatted

    def get_prediction_detail(self, match_id: str) -> Optional[Dict]:
        """
        Récupère le détail complet d'une prédiction

        Args:
            match_id: ID du match

        Returns:
            Prédiction détaillée ou None
        """
        pred = self.db.get_prediction_by_match_id(match_id)

        if not pred:
            return None

        return {
            'match_id': pred['match_id'],
            'home_team': pred['home_team'],
            'away_team': pred['away_team'],
            'league_code': pred['league_code'],
            'match_date': pred['match_date'].isoformat() if pred['match_date'] else None,

            'shots': {
                'min': pred['shots_min'],
                'max': pred['shots_max'],
                'confidence': float(pred['shots_confidence']),
                'home_team_message': f"{pred['home_team']} fera PLUS de {pred.get('home_shots_min', 'N/A')} et MOINS de {pred.get('home_shots_max', 'N/A')} tirs",
                'away_team_message': f"{pred['away_team']} fera PLUS de {pred.get('away_shots_min', 'N/A')} et MOINS de {pred.get('away_shots_max', 'N/A')} tirs",
                'message_min': f"Total: Il y aura PLUS de {pred['shots_min']} tirs",
                'message_max': f"Total: Il y aura MOINS de {pred['shots_max']} tirs",
                'analysis': pred.get('analysis_shots'),
                'ai_reasoning': pred.get('ai_reasoning_shots')
            },

            'corners': {
                'min': pred['corners_min'],
                'max': pred['corners_max'],
                'confidence': float(pred['corners_confidence']),
                'home_team_message': f"{pred['home_team']} fera PLUS de {pred.get('home_corners_min', 'N/A')} et MOINS de {pred.get('home_corners_max', 'N/A')} corners",
                'away_team_message': f"{pred['away_team']} fera PLUS de {pred.get('away_corners_min', 'N/A')} et MOINS de {pred.get('away_corners_max', 'N/A')} corners",
                'message_min': f"Total: Il y aura PLUS de {pred['corners_min']} corners",
                'message_max': f"Total: Il y aura MOINS de {pred['corners_max']} corners",
                'analysis': pred.get('analysis_corners'),
                'ai_reasoning': pred.get('ai_reasoning_corners')
            },

            'formations': {
                'home': pred.get('home_formation'),
                'away': pred.get('away_formation')
            } if pred.get('home_formation') else None,

            'weather': pred.get('weather'),
            'rankings_used': pred.get('rankings_used'),
            'created_at': pred['created_at'].isoformat() if pred.get('created_at') else None,
            'updated_at': pred['updated_at'].isoformat() if pred.get('updated_at') else None
        }


# Instance globale
_prediction_instance = None

def get_prediction_service() -> PredictionService:
    """Retourne l'instance singleton du service de prédictions"""
    global _prediction_instance
    if _prediction_instance is None:
        _prediction_instance = PredictionService()
    return _prediction_instance
