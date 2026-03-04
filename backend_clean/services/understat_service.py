"""
Service Understat - Recuperation des stats de formations historiques
API: https://understat.com/getTeamData/{TeamName}/{Season}
"""

import requests
from typing import Dict, Optional
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)


class UnderstatService:
    """Service pour recuperer les stats de formations depuis Understat"""

    BASE_URL = "https://understat.com/getTeamData"

    # Mapping noms d'equipes football-data.co.uk vers Understat
    TEAM_NAME_MAPPING = {
        # Premier League
        'Arsenal': 'Arsenal',
        'Aston Villa': 'Aston Villa',
        'Bournemouth': 'Bournemouth',
        'Brentford': 'Brentford',
        'Brighton': 'Brighton',
        'Burnley': 'Burnley',
        'Chelsea': 'Chelsea',
        'Crystal Palace': 'Crystal Palace',
        'Everton': 'Everton',
        'Fulham': 'Fulham',
        'Liverpool': 'Liverpool',
        'Luton': 'Luton',
        'Man City': 'Manchester City',
        'Man United': 'Manchester United',
        'Newcastle': 'Newcastle United',
        'Nott\'m Forest': 'Nottingham Forest',
        'Sheffield United': 'Sheffield United',
        'Tottenham': 'Tottenham',
        'West Ham': 'West Ham',
        'Wolves': 'Wolverhampton Wanderers',

        # La Liga
        'Alaves': 'Alaves',
        'Almeria': 'Almeria',
        'Athletic Club': 'Athletic Club',
        'Ath Madrid': 'Atletico Madrid',
        'Atletico Madrid': 'Atletico Madrid',
        'Barcelona': 'Barcelona',
        'Cadiz': 'Cadiz',
        'Celta': 'Celta Vigo',
        'Espanol': 'Espanyol',
        'Getafe': 'Getafe',
        'Girona': 'Girona',
        'Granada': 'Granada',
        'Las Palmas': 'Las Palmas',
        'Mallorca': 'Mallorca',
        'Osasuna': 'Osasuna',
        'Rayo Vallecano': 'Rayo Vallecano',
        'Real Betis': 'Real Betis',
        'Real Madrid': 'Real Madrid',
        'Real Sociedad': 'Real Sociedad',
        'Sevilla': 'Sevilla',
        'Valencia': 'Valencia',
        'Valladolid': 'Real Valladolid',
        'Villarreal': 'Villarreal',

        # Serie A
        'Atalanta': 'Atalanta',
        'Bologna': 'Bologna',
        'Cagliari': 'Cagliari',
        'Empoli': 'Empoli',
        'Fiorentina': 'Fiorentina',
        'Frosinone': 'Frosinone',
        'Genoa': 'Genoa',
        'Inter': 'Inter',
        'Juventus': 'Juventus',
        'Lazio': 'Lazio',
        'Lecce': 'Lecce',
        'AC Milan': 'Milan',
        'Monza': 'Monza',
        'Napoli': 'Napoli',
        'Roma': 'Roma',
        'Salernitana': 'Salernitana',
        'Sassuolo': 'Sassuolo',
        'Torino': 'Torino',
        'Udinese': 'Udinese',
        'Verona': 'Verona',

        # Bundesliga
        'Augsburg': 'Augsburg',
        'Dortmund': 'Borussia Dortmund',
        "M'gladbach": 'Borussia Monchengladbach',
        'Bayern Munich': 'Bayern Munich',
        'Bochum': 'Bochum',
        'Darmstadt': 'Darmstadt',
        'Ein Frankfurt': 'Eintracht Frankfurt',
        'FC Koln': 'FC Koln',
        'Freiburg': 'Freiburg',
        'Heidenheim': 'Heidenheim',
        'Hoffenheim': 'Hoffenheim',
        'Leverkusen': 'Bayer Leverkusen',
        'Mainz': 'Mainz',
        'RB Leipzig': 'RB Leipzig',
        'Schalke 04': 'Schalke 04',
        'Stuttgart': 'Stuttgart',
        'Union Berlin': 'Union Berlin',
        'Werder Bremen': 'Werder Bremen',
        'Wolfsburg': 'Wolfsburg',

        # Ligue 1
        'Ajaccio': 'Ajaccio',
        'Angers': 'Angers',
        'Auxerre': 'Auxerre',
        'Brest': 'Brest',
        'Clermont': 'Clermont',
        'Le Havre': 'Le Havre',
        'Lens': 'Lens',
        'Lille': 'Lille',
        'Lorient': 'Lorient',
        'Lyon': 'Lyon',
        'Marseille': 'Marseille',
        'Metz': 'Metz',
        'Monaco': 'Monaco',
        'Montpellier': 'Montpellier',
        'Nantes': 'Nantes',
        'Nice': 'Nice',
        'Paris SG': 'Paris Saint Germain',
        'PSG': 'Paris Saint Germain',
        'Reims': 'Reims',
        'Rennes': 'Rennes',
        'Strasbourg': 'Strasbourg',
        'Toulouse': 'Toulouse'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def _normalize_team_name(self, team_name: str) -> str:
        """Convertit le nom de l'equipe vers le format Understat"""
        return self.TEAM_NAME_MAPPING.get(team_name, team_name)

    def get_formation_stats(self, team_name: str, formation: str, season: int = 2024) -> Optional[Dict]:
        """
        Recupere les stats d'une formation specifique pour une equipe

        Args:
            team_name: Nom de l'equipe (format football-data)
            formation: Formation (ex: "4-3-3", "4-2-3-1")
            season: Saison (ex: 2024, 2025)

        Returns:
            Dict avec stats de la formation ou None si:
            - Equipe non trouvee
            - Formation non utilisee par l'equipe
            - Erreur API/reseau
            {
                'formation': '4-3-3',
                'minutes': 1200,
                'shots_per_90': 18.5,
                'shots_against_per_90': 12.3,
                'goals_per_90': 2.1,
                'goals_against_per_90': 1.1,
                'xg_per_90': 2.1,
                'xga_per_90': 1.3,
                'percentage_used': 33.5,
                'sample_size': 1200
            }
        """
        try:
            # Validation inputs
            if not team_name or not formation:
                logger.error(f"Parametres invalides: team_name={team_name}, formation={formation}")
                return None

            # Normaliser le nom
            understat_name = self._normalize_team_name(team_name)

            # Recuperer toutes les stats de l'equipe
            team_data = self._get_team_data(understat_name, season)

            if not team_data:
                logger.warning(f"[Understat] Aucune donnee pour {team_name} ({understat_name}) saison {season}")
                return None

            if 'statistics' not in team_data:
                logger.warning(f"[Understat] Pas de section 'statistics' pour {team_name}")
                return None

            statistics = team_data['statistics']

            if 'formation' not in statistics:
                logger.warning(f"[Understat] Pas de donnees formation pour {team_name}")
                return None

            formations = statistics['formation']

            if not isinstance(formations, dict):
                logger.error(f"[Understat] Format inattendu pour formations de {team_name}: {type(formations)}")
                return None

            # Chercher la formation specifique
            if formation not in formations:
                available = list(formations.keys())
                logger.info(f"[Understat] Formation {formation} non trouvee pour {team_name}. Disponibles: {available}")
                return None

            formation_data = formations[formation]

            if not isinstance(formation_data, dict):
                logger.error(f"[Understat] Format inattendu pour formation {formation}: {type(formation_data)}")
                return None

        except Exception as e:
            logger.error(f"[Understat] Erreur validation donnees {team_name}: {e}")
            return None

        try:
            # Extraire les stats
            minutes = formation_data.get('time', 0)

            # Validation echantillon minimum
            if minutes < 45:  # Moins d'un demi-match
                logger.info(f"[Understat] Echantillon trop faible pour {team_name} {formation}: {minutes} min")
                return None

            # Helper pour extraire totaux
            def get_total(data_dict):
                try:
                    if isinstance(data_dict, dict):
                        total = data_dict.get('total', 0)
                        if total:
                            return float(total)
                        # Fallback: additionner home + away
                        h = float(data_dict.get('h', 0))
                        a = float(data_dict.get('a', 0))
                        return h + a
                    return float(data_dict) if data_dict else 0
                except (ValueError, TypeError) as e:
                    logger.warning(f"[Understat] Erreur conversion donnee: {data_dict}, {e}")
                    return 0

            shots_data = formation_data.get('shots', {})
            goals_data = formation_data.get('goals', {})
            xg_data = formation_data.get('xG', {})
            against_data = formation_data.get('against', {})

            shots = get_total(shots_data)
            goals = get_total(goals_data)
            xg = get_total(xg_data)

            shots_against = 0
            goals_against = 0
            xga = 0

            if isinstance(against_data, dict):
                shots_against = get_total(against_data.get('shots', {}))
                goals_against = get_total(against_data.get('goals', {}))
                xga = get_total(against_data.get('xG', {}))

            # Calculer les moyennes par 90 minutes
            if minutes > 0:
                shots_per_90 = (shots / minutes) * 90
                shots_against_per_90 = (shots_against / minutes) * 90
                goals_per_90 = (goals / minutes) * 90
                goals_against_per_90 = (goals_against / minutes) * 90
                xg_per_90 = (xg / minutes) * 90
                xga_per_90 = (xga / minutes) * 90
            else:
                logger.warning(f"[Understat] Minutes = 0 pour {team_name} {formation}")
                return None

            # Validation coherence
            if shots_per_90 > 50 or shots_per_90 < 0:
                logger.warning(f"[Understat] Valeur aberrante shots_per_90={shots_per_90} pour {team_name} {formation}")
                return None

            # Calculer le pourcentage d'utilisation
            try:
                total_minutes = sum(f.get('time', 0) for f in formations.values() if isinstance(f, dict))
                percentage_used = (minutes / total_minutes * 100) if total_minutes > 0 else 0
            except Exception as e:
                logger.warning(f"[Understat] Erreur calcul percentage: {e}")
                percentage_used = 0

            result = {
                'formation': formation,
                'minutes': int(minutes),
                'shots_per_90': round(shots_per_90, 2),
                'shots_against_per_90': round(shots_against_per_90, 2),
                'goals_per_90': round(goals_per_90, 2),
                'goals_against_per_90': round(goals_against_per_90, 2),
                'xg_per_90': round(xg_per_90, 2),
                'xga_per_90': round(xga_per_90, 2),
                'percentage_used': round(percentage_used, 1),
                'sample_size': int(minutes)
            }

            logger.info(f"[Understat] Stats recuperees pour {team_name} {formation}: {minutes}min, {shots_per_90:.1f} tirs/90")
            return result

        except Exception as e:
            logger.error(f"[Understat] Erreur extraction stats {team_name} {formation}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_team_data(self, team_name: str, season: int) -> Optional[Dict]:
        """
        Recupere toutes les donnees d'une equipe depuis Understat

        Returns:
            Dict avec donnees equipe ou None si erreur
        """
        team_encoded = quote(team_name)
        url = f"{self.BASE_URL}/{team_encoded}/{season}"

        try:
            response = self.session.get(url, timeout=10)

            # Gestion codes erreur HTTP
            if response.status_code == 404:
                logger.warning(f"[Understat] Equipe non trouvee: {team_name} (404)")
                return None
            elif response.status_code == 403:
                logger.error(f"[Understat] Acces interdit (403) - IP bloquee?")
                return None
            elif response.status_code == 500:
                logger.error(f"[Understat] Erreur serveur (500)")
                return None
            elif response.status_code == 429:
                logger.error(f"[Understat] Trop de requetes (429) - rate limit")
                return None

            response.raise_for_status()

            # Parser JSON
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"[Understat] Reponse JSON invalide pour {team_name}: {e}")
                return None

            # Validation structure
            if not isinstance(data, dict):
                logger.error(f"[Understat] Format reponse inattendu pour {team_name}: {type(data)}")
                return None

            logger.info(f"[Understat] Donnees recuperees pour {team_name} saison {season}")
            return data

        except requests.Timeout:
            logger.error(f"[Understat] Timeout (10s) pour {team_name}")
            return None
        except requests.ConnectionError:
            logger.error(f"[Understat] Erreur connexion pour {team_name}")
            return None
        except requests.RequestException as e:
            logger.error(f"[Understat] Erreur HTTP pour {team_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Understat] Erreur inattendue pour {team_name}: {e}")
            import traceback
            traceback.print_exc()
            return None


# Singleton
_understat_service = None

def get_understat_service() -> UnderstatService:
    """Retourne l'instance singleton du service Understat"""
    global _understat_service
    if _understat_service is None:
        _understat_service = UnderstatService()
    return _understat_service
