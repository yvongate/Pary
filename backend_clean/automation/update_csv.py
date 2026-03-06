"""
Script d'automatisation - Mise à jour des CSV historiques
Source: football-data.co.uk + FlashScore (fixtures du jour)
"""

import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

# URLs des CSV par championnat (saison 2025-2026)
CSV_URLS = {
    'E0': 'https://www.football-data.co.uk/mmz4281/2526/E0.csv',
    'E1': 'https://www.football-data.co.uk/mmz4281/2526/E1.csv',
    'SP1': 'https://www.football-data.co.uk/mmz4281/2526/SP1.csv',
    'I1': 'https://www.football-data.co.uk/mmz4281/2526/I1.csv',
    'F1': 'https://www.football-data.co.uk/mmz4281/2526/F1.csv',
    'F2': 'https://www.football-data.co.uk/mmz4281/2526/F2.csv',
    'D1': 'https://www.football-data.co.uk/mmz4281/2526/D1.csv',
    'P1': 'https://www.football-data.co.uk/mmz4281/2526/P1.csv',
    # Championnats supplémentaires
    'E2': 'https://www.football-data.co.uk/mmz4281/2526/E2.csv',
    'E3': 'https://www.football-data.co.uk/mmz4281/2526/E3.csv',
    'BL': 'https://www.football-data.co.uk/mmz4281/2526/BL.csv',
    'ED': 'https://www.football-data.co.uk/mmz4281/2526/ED.csv',
    'L1': 'https://www.football-data.co.uk/mmz4281/2526/L1.csv',
    'LL': 'https://www.football-data.co.uk/mmz4281/2526/LL.csv',
    'PL': 'https://www.football-data.co.uk/mmz4281/2526/PL.csv',
    'SA': 'https://www.football-data.co.uk/mmz4281/2526/SA.csv',
}

# URL fixtures
FIXTURES_URL = 'https://www.football-data.co.uk/fixtures.csv'


def download_csv(url: str, output_path: str) -> Dict:
    """
    Télécharge un fichier CSV depuis une URL

    Args:
        url: URL du fichier CSV
        output_path: Chemin de destination

    Returns:
        Dict avec status et infos
    """
    try:
        print(f"[DOWNLOAD] {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Sauvegarder le fichier
        with open(output_path, 'wb') as f:
            f.write(response.content)

        file_size = len(response.content)
        print(f"  [OK] {file_size} bytes saved to {output_path}")

        return {
            'success': True,
            'url': url,
            'path': output_path,
            'size': file_size,
            'timestamp': datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] {e}")
        return {
            'success': False,
            'url': url,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def update_all_historical_data(data_dir: str = './data') -> Dict:
    """
    Met à jour tous les fichiers CSV historiques

    Args:
        data_dir: Dossier de destination

    Returns:
        Rapport de mise à jour
    """
    print("=" * 70)
    print("MISE A JOUR DES DONNEES HISTORIQUES")
    print("=" * 70)

    results = {
        'timestamp': datetime.now().isoformat(),
        'total': len(CSV_URLS),
        'success': 0,
        'failed': 0,
        'files': []
    }

    # Créer le dossier si nécessaire
    os.makedirs(data_dir, exist_ok=True)

    # Télécharger chaque CSV
    for league_code, url in CSV_URLS.items():
        filename = f"{league_code}_2526.csv"
        output_path = os.path.join(data_dir, filename)

        result = download_csv(url, output_path)
        results['files'].append(result)

        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1

    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")

    return results


def get_flashscore_daily_fixtures() -> List[Dict]:
    """
    Récupère les matchs du jour/lendemain depuis FlashScore

    Returns:
        Liste de matchs FlashScore (3 prochains jours)
    """
    try:
        import sys
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        sys.path.insert(0, parent_dir)

        from scrapers.flashscore_fixtures_scraper import get_flashscore_fixtures_scraper

        scraper = get_flashscore_fixtures_scraper()
        all_matches = []

        # Scraper les 5 ligues pour les 3 prochains jours
        for league_code in ['E0', 'SP1', 'I1', 'F1', 'D1']:
            matches = scraper.scrape_fixtures(league_code, days_ahead=3)
            all_matches.extend(matches)
            print(f"  [FlashScore] {league_code}: {len(matches)} matchs")

        scraper.close()
        return all_matches

    except Exception as e:
        print(f"  [WARNING] FlashScore scraping échoué: {e}")
        return []


def merge_fixtures_with_flashscore(csv_path: str, flashscore_matches: List[Dict]) -> int:
    """
    Fusionne les fixtures CSV avec FlashScore et sauvegarde

    Args:
        csv_path: Chemin du fichier CSV
        flashscore_matches: Matchs depuis FlashScore

    Returns:
        Nombre de matchs ajoutés depuis FlashScore
    """
    try:
        # Lire le CSV existant
        df_csv = pd.read_csv(csv_path)
        print(f"  [CSV] {len(df_csv)} matchs dans le fichier")

        # Convertir FlashScore en format CSV
        new_rows = []
        added_count = 0

        for match in flashscore_matches:
            # Vérifier si le match existe déjà dans le CSV
            home_team = match['home_team']
            away_team = match['away_team']
            league_code = match['league_code']

            # Chercher match identique dans CSV
            existing = df_csv[
                (df_csv['Div'] == league_code) &
                (df_csv['HomeTeam'].str.lower() == home_team.lower()) &
                (df_csv['AwayTeam'].str.lower() == away_team.lower())
            ]

            if existing.empty:
                # Convertir date FlashScore "14/03" en "14/03/2026"
                date_str = match.get('date', '')
                if date_str and '/' in date_str:
                    day_month = date_str  # "14/03"
                    current_year = datetime.now().year
                    date_str = f"{day_month}/{current_year}"  # "14/03/2026"
                else:
                    date_str = ''

                # Créer nouvelle ligne CSV
                new_row = {
                    'Div': league_code,
                    'Date': date_str,
                    'Time': match.get('time', ''),
                    'HomeTeam': home_team,
                    'AwayTeam': away_team,
                    'Referee': '',
                    # Toutes les autres colonnes vides
                }

                new_rows.append(new_row)
                added_count += 1
                print(f"  [+] Ajouté: {home_team} vs {away_team} ({league_code})")

        if new_rows:
            # Ajouter les nouvelles lignes au DataFrame
            df_new = pd.DataFrame(new_rows)

            # Combiner avec le CSV existant
            df_merged = pd.concat([df_csv, df_new], ignore_index=True)

            # Sauvegarder
            df_merged.to_csv(csv_path, index=False)
            print(f"  [OK] {added_count} matchs FlashScore ajoutés au CSV")
        else:
            print(f"  [OK] Tous les matchs FlashScore déjà présents dans le CSV")

        return added_count

    except Exception as e:
        print(f"  [ERROR] Fusion FlashScore/CSV échouée: {e}")
        return 0


def update_fixtures(data_dir: str = './data') -> Dict:
    """
    Met à jour le fichier fixtures.csv
    Fusionne football-data.co.uk + FlashScore (matchs du jour)

    Args:
        data_dir: Dossier de destination

    Returns:
        Résultat de la mise à jour
    """
    print("\n" + "=" * 70)
    print("MISE A JOUR DES FIXTURES (CSV + FlashScore)")
    print("=" * 70)

    output_path = os.path.join(data_dir, 'fixtures.csv')

    # ÉTAPE 1: Télécharger CSV football-data.co.uk
    print("\n[ÉTAPE 1] Téléchargement CSV football-data.co.uk...")
    result = download_csv(FIXTURES_URL, output_path)

    if not result['success']:
        return result

    # ÉTAPE 2: Scraper FlashScore pour les matchs du jour/lendemain
    print("\n[ÉTAPE 2] Scraping FlashScore (3 prochains jours)...")
    flashscore_matches = get_flashscore_daily_fixtures()

    # ÉTAPE 3: Fusionner les deux sources
    if flashscore_matches:
        print(f"\n[ÉTAPE 3] Fusion: {len(flashscore_matches)} matchs FlashScore...")
        added = merge_fixtures_with_flashscore(output_path, flashscore_matches)
        result['flashscore_added'] = added
    else:
        print("\n[ÉTAPE 3] Aucun match FlashScore à ajouter")
        result['flashscore_added'] = 0

    return result


def run_full_update(data_dir: str = './data') -> Dict:
    """
    Exécute une mise à jour complète (historiques + fixtures)

    Args:
        data_dir: Dossier de destination

    Returns:
        Rapport complet
    """
    start_time = datetime.now()

    # 1. Mettre à jour les CSV historiques
    historical_results = update_all_historical_data(data_dir)

    # 2. Mettre à jour les fixtures
    fixtures_result = update_fixtures(data_dir)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': duration,
        'historical': historical_results,
        'fixtures': fixtures_result
    }


if __name__ == '__main__':
    # Exécuter la mise à jour complète
    import sys

    # Récupérer le dossier data
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        # Par défaut, utiliser ../data depuis automation/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), 'data')

    print(f"Data directory: {data_dir}")

    # Exécuter
    report = run_full_update(data_dir)

    # Afficher le résumé
    print("\n" + "=" * 70)
    print("RAPPORT FINAL")
    print("=" * 70)
    print(f"Durée: {report['duration_seconds']:.2f}s")
    print(f"Historiques: {report['historical']['success']}/{report['historical']['total']} OK")
    print(f"Fixtures: {'OK' if report['fixtures']['success'] else 'FAILED'}")
