"""
Script pour générer la prédiction Tottenham vs Crystal Palace AVEC lineup
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lineup_service import get_lineup_service
from services.sqlite_database_service import get_sqlite_db
from core.dynamic_prediction import DynamicPredictor
from datetime import datetime

def main():
    print("=" * 70)
    print("GENERATION AVEC LINEUP: Tottenham vs Crystal Palace")
    print("=" * 70)

    # Paramètres du match
    home_team = 'Tottenham'
    away_team = 'Crystal Palace'
    league_code = 'E0'
    match_date = datetime(2026, 3, 5, 20, 0)
    match_id = f"{league_code}_{match_date.strftime('%Y%m%d')}_{home_team}_{away_team}".replace(' ', '_')

    db = get_sqlite_db()
    lineup_service = get_lineup_service()

    # ETAPE 1: Récupérer lineup via SerpAPI
    print(f"\n[1/3] Appel SerpAPI pour lineup...")

    try:
        lineup_data = lineup_service.get_lineups(home_team, away_team, match_date.strftime('%Y-%m-%d'))

        if lineup_data and lineup_data.get('raw_text'):
            lineup_raw_text = lineup_data['raw_text']
            print(f"[OK] Lineup recuperee ({len(lineup_raw_text)} caracteres)")
            print(f"\nContenu lineup:")
            print("-" * 70)
            print(lineup_raw_text[:500])
            print("-" * 70)

            # Sauvegarder en DB
            db.insert_lineup({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'league_code': league_code,
                'match_date': match_date,
                'lineup_raw_text': lineup_raw_text,
                'source': 'serpapi'
            })
            print("[OK] Lineup sauvegardee en DB")

        else:
            print("[WARNING] Lineup non trouvee via SerpAPI")
            print("La prediction continuera sans lineup...")

    except Exception as e:
        print(f"[ERREUR] SerpAPI: {e}")
        print("La prediction continuera sans lineup...")

    # ETAPE 2: Générer prédiction (qui utilisera la lineup en DB)
    print(f"\n[2/3] Generation prediction METHODE 1...")

    predictor = DynamicPredictor()

    try:
        result = predictor.predict_match(home_team, away_team, 'england', match_date)

        if 'error' in result:
            print(f"\n[ERREUR] {result['error']}")
            return

        predictions = result.get('predictions', {})
        confidence = result.get('confidence', {})
        context = result.get('context', {})

        print(f"\n[OK] Prediction generee!")
        print(f"  Home shots: {predictions.get('home_shots', 'N/A')}")
        print(f"  Away shots: {predictions.get('away_shots', 'N/A')}")
        print(f"  Home corners: {predictions.get('home_corners', 'N/A')}")
        print(f"  Away corners: {predictions.get('away_corners', 'N/A')}")
        print(f"  Total tirs: {predictions.get('total_shots', 'N/A')}")
        print(f"  Total corners: {predictions.get('total_corners', 'N/A')}")

        # ETAPE 3: Sauvegarder (REPLACE l'ancienne prédiction)
        print(f"\n[3/3] Sauvegarde en base de donnees...")

        prediction_data = {
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'league_code': league_code,
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
            print(f"[OK] Prediction mise a jour! (ID: {prediction_id})")
        else:
            print(f"[WARNING] Erreur lors de la sauvegarde")

        print("\n" + "=" * 70)
        print("TERMINEE! La prediction AVEC lineup est maintenant disponible.")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
