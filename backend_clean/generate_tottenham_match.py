"""
Script pour générer manuellement la prédiction Tottenham vs Crystal Palace
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_prediction import DynamicPredictor
from services.sqlite_database_service import get_sqlite_db
from datetime import datetime

def main():
    print("=" * 70)
    print("GENERATION MANUELLE: Tottenham vs Crystal Palace")
    print("=" * 70)

    # Créer les instances
    predictor = DynamicPredictor()
    db = get_sqlite_db()

    # Paramètres du match
    home_team = 'Tottenham'
    away_team = 'Crystal Palace'
    league_code = 'england'
    match_date = datetime(2026, 3, 5, 20, 0)

    print(f"\n[1/3] Generation prediction...")
    try:
        result = predictor.predict_match(home_team, away_team, league_code, match_date)

        if 'error' in result:
            print(f"\n[ERREUR] {result['error']}")
            return

        predictions = result.get('predictions', {})
        confidence = result.get('confidence', {})
        context = result.get('context', {})

        print(f"\n[OK] Prediction generee!")
        print(f"  Tirs totaux: {predictions.get('total_shots', 'N/A')}")
        print(f"  Corners totaux: {predictions.get('total_corners', 'N/A')}")
        print(f"  Home shots: {predictions.get('home_shots', 'N/A')}")
        print(f"  Away shots: {predictions.get('away_shots', 'N/A')}")
        print(f"  Home corners: {predictions.get('home_corners', 'N/A')}")
        print(f"  Away corners: {predictions.get('away_corners', 'N/A')}")

        # Préparer les données pour la DB
        print(f"\n[2/3] Sauvegarde en base de donnees...")

        match_id = f"E0_20260305_{home_team}_{away_team}".replace(' ', '_')

        prediction_data = {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'league_code': 'E0',
            'match_date': match_date,
            'shots_min': predictions.get('shots_min', int(predictions.get('total_shots', 27) * 0.8)),
            'shots_max': predictions.get('shots_max', int(predictions.get('total_shots', 27) * 1.2)),
            'shots_confidence': confidence.get('overall', 0.75),
            'corners_min': predictions.get('corners_min', int(predictions.get('total_corners', 11) * 0.8)),
            'corners_max': predictions.get('corners_max', int(predictions.get('total_corners', 11) * 1.2)),
            'corners_confidence': confidence.get('overall', 0.75),
            'analysis_shots': predictions.get('shots_analysis', ''),
            'analysis_corners': predictions.get('corners_analysis', ''),
            'ai_reasoning_shots': predictions.get('ai_reasoning_shots', ''),
            'ai_reasoning_corners': predictions.get('ai_reasoning_corners', ''),
            'home_shots': predictions.get('home_shots'),
            'away_shots': predictions.get('away_shots'),
            'home_corners': predictions.get('home_corners'),
            'away_corners': predictions.get('away_corners'),
            'home_shots_min': predictions.get('home_shots_min'),
            'home_shots_max': predictions.get('home_shots_max'),
            'away_shots_min': predictions.get('away_shots_min'),
            'away_shots_max': predictions.get('away_shots_max'),
            'home_corners_min': predictions.get('home_corners_min'),
            'home_corners_max': predictions.get('home_corners_max'),
            'away_corners_min': predictions.get('away_corners_min'),
            'away_corners_max': predictions.get('away_corners_max'),
            'weather': context.get('weather'),
            'rankings_used': context.get('rankings'),
            'method': 'calculs'
        }

        prediction_id = db.insert_prediction(prediction_data)

        if prediction_id:
            print(f"[OK] Prediction sauvegardee! (ID: {prediction_id})")
        else:
            print(f"[WARNING] Erreur lors de la sauvegarde")

        print(f"\n[3/3] Verification...")
        saved_prediction = db.get_prediction_by_match_id(match_id)

        if saved_prediction:
            print(f"[OK] Prediction disponible en DB!")
            print(f"  Match ID: {saved_prediction['match_id']}")
            print(f"  Tirs: {saved_prediction['shots_min']}-{saved_prediction['shots_max']}")
            print(f"  Corners: {saved_prediction['corners_min']}-{saved_prediction['corners_max']}")
        else:
            print(f"[WARNING] Prediction non trouvee en DB")

        print("\n" + "=" * 70)
        print("TERMINEE! La prediction est maintenant disponible sur le frontend.")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
