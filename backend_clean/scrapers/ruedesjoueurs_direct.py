"""
Scraping DIRECT de Rue des Joueurs - SANS SerpAPI (gratuit)
Utilise les pages de championnat pour trouver les matchs
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re

# Mapping des codes de ligues vers les pages RDJ
RUE_DES_JOUEURS_LEAGUES = {
    'E0': 'https://www.ruedesjoueurs.com/pronostics/premier-league-900326.html',
    'E1': 'https://www.ruedesjoueurs.com/pronostics/championship-900638.html',
    'SP1': 'https://www.ruedesjoueurs.com/pronostics/liga-901074.html',
    'I1': 'https://www.ruedesjoueurs.com/pronostics/serie-a-899984.html',
    'F1': 'https://www.ruedesjoueurs.com/pronostics/ligue-1-900705.html',
    'F2': 'https://www.ruedesjoueurs.com/pronostics/ligue-2-900765.html',
    'D1': 'https://www.ruedesjoueurs.com/pronostics/bundesliga-899867.html',
    'P1': 'https://www.ruedesjoueurs.com/pronostics/primeira-liga-nos-portugal-845530.html'
}

# Mapping noms de ligues
LEAGUE_NAMES = {
    'E0': 'Premier League',
    'SP1': 'Liga',
    'I1': 'Serie A',
    'F1': 'Ligue 1',
    'D1': 'Bundesliga'
}


def normalize_team_name(name: str) -> str:
    """Normalise le nom d'une equipe pour la comparaison"""
    name = name.lower().strip()

    # Remplacements courants
    replacements = {
        # Premier League
        'man united': 'manchester united',
        'man utd': 'manchester united',
        'man city': 'manchester city',
        'newcastle': 'newcastle united',
        'tottenham': 'tottenham hotspur',
        'west ham': 'west ham united',

        # Ligue 1
        'psg': 'paris saint-germain',
        'paris sg': 'paris saint-germain',
        'om': 'marseille',
        'ol': 'lyon',
        'asse': 'saint-etienne',
        'losc': 'lille',

        # La Liga - RDJ utilise les noms francais
        'barcelona': 'barcelone',
        'fc barcelona': 'barcelone',
        'sevilla': 'seville',
        'atletico madrid': 'atletico madrid',
        'ath madrid': 'atletico madrid',
        'athletic bilbao': 'athletic bilbao',
        'ath bilbao': 'athletic bilbao',
        'real sociedad': 'real sociedad',
        'sociedad': 'real sociedad',
        'celta vigo': 'celta vigo',
        'celta': 'celta vigo',
        'rayo vallecano': 'rayo vallecano',
        'vallecano': 'rayo vallecano',
        'deportivo alaves': 'alaves',
        'espanyol': 'espanyol',
        'espanol': 'espanyol'
    }

    for old, new in replacements.items():
        if old in name:
            name = name.replace(old, new)

    return name


def find_match_url(home_team: str, away_team: str, league_code: str) -> Optional[str]:
    """
    Trouve l'URL d'un match sur Rue des Joueurs

    Args:
        home_team: Equipe domicile
        away_team: Equipe exterieur
        league_code: Code ligue (E0, SP1, I1, F1, D1...)

    Returns:
        URL du pronostic ou None
    """

    # Verifier que la ligue est supportee
    if league_code not in RUE_DES_JOUEURS_LEAGUES:
        print(f"[WARNING] Ligue {league_code} non supportee par RDJ")
        return None

    league_url = RUE_DES_JOUEURS_LEAGUES[league_code]
    league_name = LEAGUE_NAMES.get(league_code, league_code)

    print(f"[RDJ DIRECT] Recherche {home_team} vs {away_team} sur {league_name}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Scraper la page du championnat
        response = requests.get(league_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[ERREUR] Status {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Normaliser les noms d'equipes
        home_normalized = normalize_team_name(home_team)
        away_normalized = normalize_team_name(away_team)

        # Chercher tous les liens vers des pronostics
        all_links = soup.find_all('a', href=True)

        candidates = []

        for link in all_links:
            href = link.get('href', '')

            # Verifier que c'est un lien pronostic
            if '/pronostic/' not in href:
                continue

            # Texte du lien et URL
            text = link.get_text(strip=True).lower()
            href_lower = href.lower()

            # Verifier si les 2 equipes sont presentes
            home_in_text = home_normalized in text or any(word in text for word in home_normalized.split())
            away_in_text = away_normalized in text or any(word in text for word in away_normalized.split())

            home_in_href = home_normalized.replace(' ', '-') in href_lower or \
                          home_team.lower().replace(' ', '-') in href_lower
            away_in_href = away_normalized.replace(' ', '-') in href_lower or \
                          away_team.lower().replace(' ', '-') in href_lower

            # Score de confiance
            score = 0
            if home_in_text and away_in_text:
                score += 10
            if home_in_href and away_in_href:
                score += 20
            if home_in_href or away_in_href:
                score += 5

            if score > 0:
                # Construire l'URL complete
                full_url = href if href.startswith('http') else f"https://www.ruedesjoueurs.com{href}"

                candidates.append({
                    'url': full_url,
                    'text': text,
                    'score': score
                })

        if not candidates:
            print(f"[NOT FOUND] Aucun match trouve")
            return None

        # Trier par score et prendre le meilleur
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]

        print(f"[FOUND] {best['url']}")
        print(f"        Score: {best['score']}/30")

        return best['url']

    except Exception as e:
        print(f"[ERREUR] Scraping RDJ: {e}")
        return None


def get_match_analysis(url: str) -> Optional[Dict]:
    """
    Scrape une page de pronostic RDJ pour extraire l'analyse

    Args:
        url: URL du pronostic

    Returns:
        Dict avec full_text, injuries_text, etc.
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraire tout le texte de la page
        full_text = soup.get_text(separator='\n', strip=True)

        # Chercher la section joueurs absents
        injuries_text = ""
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            text = heading.get_text(strip=True).lower()
            if 'absent' in text or 'bless' in text or 'suspen' in text or 'indispon' in text:
                # Prendre le texte suivant
                next_elem = heading.find_next(['p', 'div', 'ul'])
                if next_elem:
                    injuries_text += next_elem.get_text(separator=' ', strip=True) + '\n'

        return {
            'url': url,
            'full_text': full_text,
            'injuries_text': injuries_text if injuries_text else "Aucune info joueurs absents trouvee",
            'source': 'RDJ Direct Scraping (gratuit)'
        }

    except Exception as e:
        print(f"[ERREUR] Scraping analyse: {e}")
        return None


def get_match_analysis_auto(home_team: str, away_team: str, league_code: str) -> Optional[Dict]:
    """
    Fonction complete : trouve ET scrape l'analyse

    Args:
        home_team: Equipe domicile
        away_team: Equipe exterieur
        league_code: Code ligue

    Returns:
        Dict avec analyse complete
    """

    # 1. Trouver l'URL
    url = find_match_url(home_team, away_team, league_code)

    if not url:
        return None

    # 2. Scraper l'analyse
    analysis = get_match_analysis(url)

    return analysis


# Test si execute directement
if __name__ == "__main__":
    print("Test RDJ Direct Scraping\n")

    # Test Strasbourg vs Lens
    result = get_match_analysis_auto("Strasbourg", "Lens", "F1")

    if result:
        print(f"\n[SUCCESS]")
        print(f"URL: {result['url']}")
        print(f"Texte complet: {len(result['full_text'])} caracteres")
        print(f"Joueurs absents: {result['injuries_text'][:200]}...")
    else:
        print("\n[ECHEC]")
