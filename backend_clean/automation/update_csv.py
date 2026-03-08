"""
Script d'automatisation - Mise à jour des CSV historiques
Source: football-data.co.uk uniquement
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


def update_fixtures(data_dir: str = './data') -> Dict:
    """
    Met à jour le fichier fixtures.csv depuis football-data.co.uk

    Args:
        data_dir: Dossier de destination

    Returns:
        Résultat de la mise à jour
    """
    print("\n" + "=" * 70)
    print("MISE A JOUR DES FIXTURES (CSV uniquement)")
    print("=" * 70)

    output_path = os.path.join(data_dir, 'fixtures.csv')

    # Télécharger CSV football-data.co.uk
    print("\nTéléchargement CSV football-data.co.uk...")
    result = download_csv(FIXTURES_URL, output_path)

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
