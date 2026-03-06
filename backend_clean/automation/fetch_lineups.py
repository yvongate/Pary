"""
Automatisation: Récupération des lineups via SerpAPI 1h avant les matchs
ET génération IMMEDIATE des prédictions avec ces lineups

Appelé par cron job toutes les 15 minutes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from services.sqlite_database_service import get_sqlite_db
from services.lineup_service import get_lineup_service
from core.dynamic_prediction import DynamicPredictor
from services.data_service import get_data_service


def get_upcoming_matches_from_fixtures(time_window_minutes: int = 60, buffer_minutes: int = 15) -> List[Dict]:
    """
    Lit fixtures.csv et récupère les matchs qui commencent dans ~1h

    Args:
        time_window_minutes: Temps avant le match (défaut: 60 min)
        buffer_minutes: Marge de tolérance (défaut: 15 min = fenêtre 45-75 min)

    Returns:
        Liste de matchs dans la fenêtre de temps
    """
    data_service = get_data_service()
    fixtures = data_service.load_fixtures()

    if fixtures is None or fixtures.empty:
        print("[WARNING] Aucune fixture trouvée")
        return []

    # Filtrer uniquement les championnats supportés
    SUPPORTED_LEAGUES = ['E0', 'SP1', 'I1', 'F1', 'D1']
    fixtures = fixtures[fixtures['Div'].isin(SUPPORTED_LEAGUES)]

    current_time = datetime.now()
    min_time = time_window_minutes - buffer_minutes
    max_time = time_window_minutes + buffer_minutes

    upcoming = []

    for idx, fixture in fixtures.iterrows():
        try:
            # Parser la date du match
            date_str = fixture['Date']
            time_str = fixture.get('Time', '')

            if isinstance(date_str, pd.Timestamp):
                match_date = date_str
                if time_str and not pd.isna(time_str):
                    try:
                        hour, minute = map(int, str(time_str).split(':'))
                        match_date = match_date.replace(hour=hour, minute=minute)
                    except:
                        pass
            elif pd.isna(date_str):
                continue
            else:
                if time_str and not pd.isna(time_str):
                    datetime_str = f"{date_str} {time_str}"
                    match_date = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M', errors='coerce')
                else:
                    match_date = pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')

            if pd.isna(match_date):
                continue

            # Calculer temps avant le match
            time_until_match = match_date - current_time
            time_until_match_minutes = time_until_match.total_seconds() / 60

            # Vérifier si dans la fenêtre
            if min_time <= time_until_match_minutes <= max_time:
                upcoming.append({
                    'home_team': fixture['HomeTeam'],
                    'away_team': fixture['AwayTeam'],
                    'league_code': fixture['Div'],
                    'match_date': match_date,
                    'time_until_match_minutes': time_until_match_minutes
                })

        except Exception as e:
            continue

    return upcoming


def fetch_lineups_for_upcoming_matches(time_window_minutes: int = 60, buffer_minutes: int = 15) -> Dict:
    """
    Récupère les lineups pour les matchs qui commencent dans environ 1 heure
    ET génère IMMEDIATEMENT les prédictions avec ces lineups

    Args:
        time_window_minutes: Temps avant le match pour récupérer les lineups (défaut: 60 min)
        buffer_minutes: Marge de tolérance (défaut: 15 min)

    Returns:
        Rapport d'exécution
    """
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print(f"[FETCH LINEUPS + PREDICTIONS] Démarrage - {start_time.isoformat()}")
    print(f"{'='*70}")

    db = get_sqlite_db()
    lineup_service = get_lineup_service()
    predictor = DynamicPredictor()

    # Mapping codes soccerstats
    soccerstats_codes = {
        'E0': 'england',
        'SP1': 'spain',
        'I1': 'italy',
        'F1': 'france',
        'D1': 'germany'
    }

    # 1. Récupérer les matchs depuis fixtures.csv
    print(f"\n[ETAPE 1] Lecture de fixtures.csv...")
    upcoming_matches = get_upcoming_matches_from_fixtures(time_window_minutes, buffer_minutes)
    print(f"[INFO] {len(upcoming_matches)} matchs trouvés dans la fenêtre de temps")

    if not upcoming_matches:
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': 0,
            'matches_found': 0,
            'lineups_fetched': 0,
            'predictions_generated': 0,
            'results': []
        }

    # 2. Pour chaque match, fetch lineup ET génère prédiction
    lineups_fetched = 0
    predictions_generated = 0
    results = []

    for match in upcoming_matches:
        home_team = match['home_team']
        away_team = match['away_team']
        league_code = match['league_code']
        match_date = match['match_date']
        match_id = f"{league_code}_{match_date.strftime('%Y%m%d')}_{home_team}_{away_team}".replace(' ', '_')

        print(f"\n{'='*70}")
        print(f"[MATCH] {home_team} vs {away_team} ({league_code})")
        print(f"  Date: {match_date}")
        print(f"  Dans: {match['time_until_match_minutes']:.1f} minutes")
        print(f"{'='*70}")

        try:
            # VÉRIFIER SI LINEUP DÉJÀ EN DB (éviter doublons SerpAPI)
            existing_lineup = db.get_lineup_by_match_id(match_id)

            lineup_raw_text = None

            if existing_lineup and existing_lineup.get('lineup_raw_text'):
                # Lineup déjà récupéré précédemment
                print(f"[SKIP] Lineup déjà en DB pour ce match (économie 1 crédit SerpAPI)")
                lineup_raw_text = existing_lineup['lineup_raw_text']
            else:
                # Pas encore en DB → Appeler SerpAPI
                print(f"\n[SERPAPI] Récupération lineup...")
                lineup_data = lineup_service.get_lineups(home_team, away_team, match_date.strftime('%Y-%m-%d'))

                if lineup_data and lineup_data.get('raw_text'):
                    lineup_raw_text = lineup_data['raw_text']
                    print(f"[OK] Lineup récupérée ({len(lineup_raw_text)} caractères)")

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

                    lineups_fetched += 1
                else:
                    print(f"[WARNING] Lineup non trouvée via SerpAPI")

            # VÉRIFIER SI PREDICTION DÉJÀ GÉNÉRÉE (éviter regénérations inutiles)
            existing_prediction = db.get_prediction_by_match_id(match_id)

            if existing_prediction:
                # Prédiction déjà générée précédemment
                print(f"[SKIP] Prédiction déjà générée pour ce match (économie 2 appels IA)")

                predictions_generated += 1  # Compter comme "traitée"
                results.append({
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'status': 'already_exists',
                    'lineup_fetched': lineup_raw_text is not None,
                    'prediction_generated': True,
                    'from_cache': True
                })
            else:
                # Pas encore générée → Générer maintenant
                print(f"\n[PREDICTION] Génération immédiate...")
                soccerstats_code = soccerstats_codes.get(league_code, 'england')

                prediction_result = predictor.predict_match(
                    home_team=home_team,
                    away_team=away_team,
                    league_code=soccerstats_code,
                    match_date=match_date
                )

                if 'error' not in prediction_result:
                    # Sauvegarder la prédiction en DB
                    predictions = prediction_result.get('predictions', {})
                    confidence = prediction_result.get('confidence', {})
                    context = prediction_result.get('context', {})

                    db.insert_prediction({
                        'match_id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'league_code': league_code,
                        'match_date': match_date,
                        'shots_min': int(predictions.get('total_shots', 20) * 0.8),
                        'shots_max': int(predictions.get('total_shots', 20) * 1.2),
                        'shots_confidence': confidence.get('overall', 0.0),
                        'corners_min': int(predictions.get('total_corners', 8) * 0.8),
                        'corners_max': int(predictions.get('total_corners', 8) * 1.2),
                        'corners_confidence': confidence.get('overall', 0.0),
                        'analysis_shots': predictions.get('shots_analysis'),
                        'analysis_corners': predictions.get('corners_analysis'),
                        'ai_reasoning_shots': predictions.get('ai_reasoning_shots'),
                        'ai_reasoning_corners': predictions.get('ai_reasoning_corners'),
                        'weather': context.get('weather'),
                        'rankings_used': context.get('rankings')
                    })

                    predictions_generated += 1
                    print(f"[OK] Prédiction générée et sauvegardée")

                    results.append({
                        'match_id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'status': 'success',
                        'lineup_fetched': lineup_raw_text is not None,
                        'prediction_generated': True,
                        'total_shots': predictions.get('total_shots'),
                        'total_corners': predictions.get('total_corners')
                    })
                else:
                    print(f"[ERROR] Prédiction échouée: {prediction_result['error']}")
                    results.append({
                        'match_id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'status': 'prediction_failed',
                        'lineup_fetched': lineup_raw_text is not None,
                        'error': prediction_result['error']
                    })

        except Exception as e:
            print(f"[ERROR] {e}")
            results.append({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'status': 'error',
                'error': str(e)
            })

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    report = {
        'timestamp': end_time.isoformat(),
        'duration_seconds': duration,
        'matches_found': len(upcoming_matches),
        'lineups_fetched': lineups_fetched,
        'predictions_generated': predictions_generated,
        'results': results
    }

    print(f"\n{'='*70}")
    print(f"[RAPPORT FINAL]")
    print(f"  Matchs trouvés dans fenêtre 1h: {len(upcoming_matches)}")
    print(f"  Lineups récupérées: {lineups_fetched}")
    print(f"  Prédictions générées: {predictions_generated}")
    print(f"  Durée: {duration:.2f}s")
    print(f"{'='*70}\n")

    return report


if __name__ == "__main__":
    # Test direct
    report = fetch_lineups_for_upcoming_matches()
    print(f"\n[DONE] {report['lineups_fetched']} lineups + {report['predictions_generated']} prédictions générées")
