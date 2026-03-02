"""
Automatisation: Récupération des lineups via SerpAPI 1h avant les matchs
Appelé par cron job toutes les 15 minutes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List
from services.sqlite_database_service import get_sqlite_db
from services.lineup_service import get_lineup_service


def fetch_lineups_for_upcoming_matches(time_window_minutes: int = 60, buffer_minutes: int = 15) -> Dict:
    """
    Récupère les lineups pour les matchs qui commencent dans environ 1 heure

    Args:
        time_window_minutes: Temps avant le match pour récupérer les lineups (défaut: 60 min)
        buffer_minutes: Marge de tolérance (défaut: 15 min)

    Returns:
        Rapport d'exécution
    """
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print(f"[FETCH LINEUPS] Démarrage - {start_time.isoformat()}")
    print(f"{'='*70}")

    db = get_sqlite_db()
    lineup_service = get_lineup_service()

    # Récupérer tous les matchs à venir sans lineup
    all_matches = db.get_matches_needing_lineups()

    print(f"[INFO] {len(all_matches)} matchs trouvés sans lineup")

    # Filtrer les matchs qui commencent dans la fenêtre de temps
    matches_to_fetch = []
    current_time = datetime.now()

    for match in all_matches:
        # Parser la date du match
        try:
            if isinstance(match['match_date'], str):
                match_time = datetime.fromisoformat(match['match_date'].replace('Z', '+00:00'))
            else:
                match_time = match['match_date']

            # Calculer le temps avant le match
            time_until_match = match_time - current_time
            time_until_match_minutes = time_until_match.total_seconds() / 60

            # Vérifier si on est dans la fenêtre de temps (60 min ± 15 min)
            min_time = time_window_minutes - buffer_minutes
            max_time = time_window_minutes + buffer_minutes

            if min_time <= time_until_match_minutes <= max_time:
                matches_to_fetch.append({
                    'match': match,
                    'time_until_match_minutes': time_until_match_minutes
                })
                print(f"[FOUND] {match['home_team']} vs {match['away_team']} - dans {time_until_match_minutes:.1f} min")

        except Exception as e:
            print(f"[ERREUR] Parse date pour {match.get('match_id')}: {e}")
            continue

    print(f"\n[INFO] {len(matches_to_fetch)} matchs dans la fenêtre de temps ({min_time}-{max_time} min)")

    # Récupérer les lineups via SerpAPI
    lineups_fetched = 0
    lineups_failed = 0
    lineup_results = []

    for item in matches_to_fetch:
        match = item['match']
        match_id = match['match_id']
        home_team = match['home_team']
        away_team = match['away_team']

        print(f"\n[SERPAPI] Récupération lineup pour {home_team} vs {away_team}...")

        try:
            # Appeler SerpAPI
            lineup_data = lineup_service.get_lineups(home_team, away_team, match['match_date'])

            if lineup_data:
                # Sauvegarder en DB
                lineup_to_save = {
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'league_code': match['league_code'],
                    'match_date': match['match_date'],
                    'home_formation': lineup_data.get('home_formation'),
                    'away_formation': lineup_data.get('away_formation'),
                    'home_lineup': lineup_data.get('home_lineup'),
                    'away_lineup': lineup_data.get('away_lineup'),
                    'source': lineup_data.get('source', 'serpapi')
                }

                db.insert_lineup(lineup_to_save)

                lineups_fetched += 1
                lineup_results.append({
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'status': 'success',
                    'formations': f"{lineup_data.get('home_formation')} vs {lineup_data.get('away_formation')}"
                })

                print(f"[OK] Lineup sauvegardée - {lineup_data.get('home_formation')} vs {lineup_data.get('away_formation')}")
            else:
                lineups_failed += 1
                lineup_results.append({
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'status': 'not_found',
                    'error': 'Lineup non trouvée dans les résultats SerpAPI'
                })

                print(f"[NOT FOUND] Lineup non trouvée")

        except Exception as e:
            lineups_failed += 1
            lineup_results.append({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'status': 'error',
                'error': str(e)
            })

            print(f"[ERREUR] {e}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    report = {
        'timestamp': end_time.isoformat(),
        'duration_seconds': duration,
        'total_matches_without_lineup': len(all_matches),
        'matches_in_time_window': len(matches_to_fetch),
        'lineups_fetched': lineups_fetched,
        'lineups_failed': lineups_failed,
        'results': lineup_results
    }

    print(f"\n{'='*70}")
    print(f"[RAPPORT FINAL]")
    print(f"  Matchs sans lineup: {len(all_matches)}")
    print(f"  Matchs dans fenêtre (45-75 min): {len(matches_to_fetch)}")
    print(f"  Lineups récupérées: {lineups_fetched}")
    print(f"  Échecs: {lineups_failed}")
    print(f"  Durée: {duration:.2f}s")
    print(f"{'='*70}\n")

    return report


if __name__ == "__main__":
    # Test direct
    report = fetch_lineups_for_upcoming_matches()
    print(f"\n[DONE] {report['lineups_fetched']} lineups récupérées")
