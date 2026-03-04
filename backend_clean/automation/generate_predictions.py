"""
Script d'automatisation - Génération des prédictions
Génère les prédictions pour les matchs des prochaines 24-48h
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_service import get_data_service
from core.dynamic_prediction import DynamicPredictor
from services.sqlite_database_service import SQLiteDatabaseService
from services.supabase_client import SupabaseClient


def get_upcoming_matches(hours_ahead: int = 48) -> List[Dict]:
    """
    Récupère les matchs des prochaines X heures

    Args:
        hours_ahead: Nombre d'heures dans le futur

    Returns:
        Liste des matchs à venir
    """
    data_service = get_data_service()

    # Charger les fixtures
    fixtures = data_service.load_fixtures()

    if fixtures is None or fixtures.empty:
        print("[WARNING] Aucune fixture trouvée")
        return []

    # Filtrer uniquement les championnats supportés
    SUPPORTED_LEAGUES = ['E0', 'SP1', 'I1', 'F1', 'D1']
    fixtures = fixtures[fixtures['Div'].isin(SUPPORTED_LEAGUES)]

    if fixtures.empty:
        print(f"[WARNING] Aucune fixture trouvée pour les championnats supportés: {SUPPORTED_LEAGUES}")
        return []

    # Filtrer les matchs des prochaines heures (depuis maintenant)
    now = datetime.now()
    future_limit = now + timedelta(hours=hours_ahead)

    print(f"[DEBUG] Now: {now}")
    print(f"[DEBUG] Future limit: {future_limit}")

    upcoming = []
    print(f"[DEBUG] Fixtures DataFrame shape: {fixtures.shape}")
    print(f"[DEBUG] Columns: {list(fixtures.columns)}")
    print(f"[DEBUG] First 3 rows:")
    print(fixtures.head(3).to_dict('records'))

    for idx, fixture in fixtures.iterrows():
        try:
            # Parser la date du match
            date_str = fixture['Date']
            time_str = fixture.get('Time', '')

            if idx < 3:  # Debug les 3 premières lignes
                print(f"[DEBUG] Row {idx}: Date='{date_str}' (type={type(date_str)}), Time='{time_str}'")

            # Si la date est déjà un Timestamp pandas (déjà parsée par load_fixtures)
            if isinstance(date_str, pd.Timestamp):
                match_date = date_str
                # Ajouter l'heure si disponible
                if time_str and not pd.isna(time_str):
                    try:
                        hour, minute = map(int, str(time_str).split(':'))
                        match_date = match_date.replace(hour=hour, minute=minute)
                    except:
                        pass
            elif pd.isna(date_str):
                continue
            else:
                # Parser manuellement (ne devrait pas arriver si load_fixtures fonctionne)
                if time_str and not pd.isna(time_str):
                    datetime_str = f"{date_str} {time_str}"
                    match_date = pd.to_datetime(datetime_str, format='%d/%m/%Y %H:%M', errors='coerce')
                else:
                    match_date = pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')

            if pd.isna(match_date):
                continue

            # Vérifier si c'est dans la fenêtre
            if now <= match_date <= future_limit:
                if idx < 10:  # Debug les 10 premiers matchs trouvés
                    print(f"[DEBUG] ✓ Match trouvé: {fixture['HomeTeam']} vs {fixture['AwayTeam']} le {match_date}")
                upcoming.append({
                    'home_team': fixture['HomeTeam'],
                    'away_team': fixture['AwayTeam'],
                    'league_code': fixture['Div'],
                    'match_date': match_date,
                    'fixture': fixture
                })
        except Exception as e:
            print(f"[DEBUG] ERREUR row {idx}: {e}")
            continue

    return upcoming


def generate_prediction_for_match(match: Dict, predictor: DynamicPredictor, db: SQLiteDatabaseService) -> Dict:
    """
    Génère une prédiction pour un match

    Args:
        match: Dict avec infos du match
        predictor: Instance DynamicPredictor
        db: Instance base de données

    Returns:
        Résultat de la prédiction
    """
    home_team = match['home_team']
    away_team = match['away_team']
    league_code = match['league_code']
    match_date = match['match_date']

    print(f"\n[PREDICTION] {home_team} vs {away_team} ({league_code})")
    print(f"  Date: {match_date}")

    try:
        # Mapping league code pour soccerstats
        soccerstats_codes = {
            'E0': 'england',
            'SP1': 'spain',
            'I1': 'italy',
            'F1': 'france',
            'D1': 'germany'
        }

        soccerstats_code = soccerstats_codes.get(league_code, 'england')

        # Générer la prédiction
        result = predictor.predict_match(
            home_team=home_team,
            away_team=away_team,
            league_code=soccerstats_code,
            match_date=match_date
        )

        if 'error' in result:
            print(f"  [ERROR] {result['error']}")
            return {
                'success': False,
                'error': result['error'],
                'match': f"{home_team} vs {away_team}"
            }

        # Extraire les prédictions
        predictions = result.get('predictions', {})
        total_shots = predictions.get('total_shots', 0)
        total_corners = predictions.get('total_corners', 0)

        print(f"  [OK] Prédiction générée:")
        print(f"       Tirs: {total_shots}")
        print(f"       Corners: {total_corners}")

        # Sauvegarder dans la base de données
        match_id = f"{league_code}_{match_date.strftime('%Y%m%d')}_{home_team}_{away_team}".replace(' ', '_')

        # Extraire les données de confiance et contexte
        confidence = result.get('confidence', {})
        context = result.get('context', {})

        db.insert_prediction({
            'match_id': match_id,
            'home_team': home_team,
            'away_team': away_team,
            'league_code': league_code,
            'match_date': match_date,
            'shots_min': int(total_shots * 0.8),
            'shots_max': int(total_shots * 1.2),
            'shots_confidence': confidence.get('overall', 0.0),
            'corners_min': int(total_corners * 0.8),
            'corners_max': int(total_corners * 1.2),
            'corners_confidence': confidence.get('overall', 0.0),
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
            'analysis_shots': predictions.get('shots_analysis'),
            'analysis_corners': predictions.get('corners_analysis'),
            'ai_reasoning_shots': predictions.get('ai_reasoning_shots'),
            'ai_reasoning_corners': predictions.get('ai_reasoning_corners'),
            'home_formation': context.get('home_formation'),
            'away_formation': context.get('away_formation'),
            'weather': context.get('weather'),
            'rankings_used': context.get('rankings')
        })

        return {
            'success': True,
            'match': f"{home_team} vs {away_team}",
            'league': league_code,
            'predictions': predictions
        }

    except Exception as e:
        print(f"  [ERROR] {e}")
        return {
            'success': False,
            'error': str(e),
            'match': f"{home_team} vs {away_team}"
        }


def run_auto_predictions(hours_ahead: int = 48) -> Dict:
    """
    Exécute la génération automatique de prédictions

    Args:
        hours_ahead: Nombre d'heures dans le futur

    Returns:
        Rapport de génération
    """
    print("=" * 70)
    print("GENERATION AUTOMATIQUE DES PREDICTIONS")
    print("=" * 70)

    start_time = datetime.now()

    # Initialiser les services
    predictor = DynamicPredictor()
    db = SQLiteDatabaseService()

    # Tenter aussi Supabase (optionnel)
    try:
        db_supabase = SupabaseClient()
        db_supabase.connect()
    except:
        db_supabase = None

    # Récupérer les matchs à venir
    print(f"\n[1] Recherche des matchs dans les prochaines {hours_ahead}h...")
    upcoming_matches = get_upcoming_matches(hours_ahead)

    print(f"  [INFO] {len(upcoming_matches)} match(s) trouvé(s)")

    if not upcoming_matches:
        duration = (datetime.now() - start_time).total_seconds()
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'total_matches': 0,
            'predictions_generated': 0,
            'predictions_failed': 0,
            'results': []
        }

    # Générer les prédictions
    print(f"\n[2] Génération des prédictions...")
    results = []
    success_count = 0
    failed_count = 0

    for i, match in enumerate(upcoming_matches, 1):
        print(f"\n--- Match {i}/{len(upcoming_matches)} ---")
        result = generate_prediction_for_match(match, predictor, db)
        results.append(result)

        if result['success']:
            success_count += 1
        else:
            failed_count += 1

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Résumé
    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)
    print(f"Durée: {duration:.2f}s")
    print(f"Total matchs: {len(upcoming_matches)}")
    print(f"Prédictions générées: {success_count}")
    print(f"Échecs: {failed_count}")

    return {
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': duration,
        'total_matches': len(upcoming_matches),
        'predictions_generated': success_count,
        'predictions_failed': failed_count,
        'results': results
    }


if __name__ == '__main__':
    # Récupérer le nombre d'heures depuis les arguments
    hours = 48
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            pass

    print(f"Génération des prédictions pour les {hours} prochaines heures\n")

    # Exécuter
    report = run_auto_predictions(hours)

    print("\n" + "=" * 70)
    print("TERMINE")
    print("=" * 70)
