"""
IA Deep Reasoning - Verification independante avec raisonnement profond
L'IA recoit TOUTES les donnees et raisonne comme un analyste expert
"""
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def generate_deep_analysis_prediction(
    match: Dict,
    home_history: List[Dict],
    away_history: List[Dict],
    current_rankings: Dict,
    rdj_context: Optional[Dict] = None,
    weather: Optional[Dict] = None,
    detailed_stats: Optional[Dict] = None
) -> Dict:
    """
    L'IA recoit TOUTES les donnees et fait un raisonnement ultra-profond

    Args:
        match: Info du match (home_team, away_team, league)
        home_history: Historique complet equipe domicile
        away_history: Historique complet equipe exterieur
        current_rankings: LES 12 TABLEAUX de soccerstats
        rdj_context: Contexte Rue des Joueurs (blessures, compositions, analyses)
        weather: Meteo (informatif uniquement, n'affecte pas les calculs)
        detailed_stats: Stats détaillées W-D-L, buts, gaps (soccerstats_working)

    Returns:
        {
            'shots_min': int,
            'shots_max': int,
            'corners_min': int,
            'corners_max': int,
            'confidence': float,
            'reasoning': str (le raisonnement complet)
        }
    """

    client = OpenAI(
        api_key=os.getenv('DEEPINFRA_API_KEY'),
        base_url="https://api.deepinfra.com/v1/openai"
    )

    home_team = match['home_team']
    away_team = match['away_team']

    # ================================================================
    # CONSTRUIRE LE PROMPT ULTRA-DETAILLE
    # ================================================================

    prompt = f"""Tu es un ANALYSTE FOOTBALL EXPERT. Tu dois predire le nombre de TIRS et CORNERS pour ce match.

IMPORTANT: Tu dois raisonner ETAPE PAR ETAPE avec des "SI/ALORS" en cherchant des PATTERNS dans l'historique.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH A ANALYSER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team} (DOMICILE) vs {away_team} (EXTERIEUR)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1: CLASSEMENTS ACTUELS (12 TABLEAUX COMPLETS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Ajouter les classements complets
    rankings_sections = [
        ('CLASSEMENT GENERAL', 'standings'),
        ('FORME (8 derniers matchs)', 'form_last_8'),
        ('DOMICILE', 'home'),
        ('EXTERIEUR', 'away'),
        ('ATTAQUE', 'offence'),
        ('DEFENSE', 'defence'),
        ('ATTAQUE DOMICILE', 'offence_home'),
        ('DEFENSE DOMICILE', 'defence_home'),
        ('ATTAQUE EXTERIEUR', 'offence_away'),
        ('DEFENSE EXTERIEUR', 'defence_away')
    ]

    for section_name, ranking_key in rankings_sections:
        if ranking_key in current_rankings and current_rankings[ranking_key]:
            prompt += f"\n[{section_name}]\n"

            # Trouver les 2 equipes dans ce classement
            home_rank = None
            away_rank = None

            for team in current_rankings[ranking_key]:
                if team['team'].lower() == home_team.lower():
                    home_rank = team
                if team['team'].lower() == away_team.lower():
                    away_rank = team

            if home_rank:
                prompt += f"  {home_team}: {home_rank['position']}e\n"
            if away_rank:
                prompt += f"  {away_team}: {away_rank['position']}e\n"

    # ================================================================
    # SECTION 2: HISTORIQUE DOMICILE COMPLET
    # ================================================================

    prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2: HISTORIQUE COMPLET {home_team} A DOMICILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: {len([m for m in home_history if m['home']])} matchs a domicile

DETAILS DE CHAQUE MATCH:
"""

    home_matches = [m for m in home_history if m['home']]
    for i, match_data in enumerate(home_matches[:20], 1):  # Top 20 matchs
        prompt += f"\n{i}. vs {match_data['opponent']}"
        if 'date' in match_data:
            prompt += f" ({match_data['date']})"
        prompt += f"""
   Tirs: {match_data['shots']} | Corners: {match_data['corners']}"""
        if match_data.get('goals_for') is not None:
            prompt += f" | Score: {match_data['goals_for']}-{match_data['goals_against']}"

    # Stats agregees
    home_shots_avg = sum(m['shots'] for m in home_matches) / len(home_matches) if home_matches else 0
    home_corners_avg = sum(m['corners'] for m in home_matches) / len(home_matches) if home_matches else 0

    prompt += f"""

STATISTIQUES AGREGEES {home_team} DOMICILE:
  - Moyenne tirs: {home_shots_avg:.1f}
  - Moyenne corners: {home_corners_avg:.1f}
"""

    # ================================================================
    # SECTION 3: HISTORIQUE EXTERIEUR COMPLET
    # ================================================================

    prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3: HISTORIQUE COMPLET {away_team} A L'EXTERIEUR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: {len([m for m in away_history if not m['home']])} matchs a l'exterieur

DETAILS DE CHAQUE MATCH:
"""

    away_matches = [m for m in away_history if not m['home']]
    for i, match_data in enumerate(away_matches[:20], 1):
        prompt += f"\n{i}. @ {match_data['opponent']}"
        if 'date' in match_data:
            prompt += f" ({match_data['date']})"
        prompt += f"""
   Tirs: {match_data['shots']} | Corners: {match_data['corners']}"""
        if match_data.get('goals_for') is not None:
            prompt += f" | Score: {match_data['goals_for']}-{match_data['goals_against']}"

    away_shots_avg = sum(m['shots'] for m in away_matches) / len(away_matches) if away_matches else 0
    away_corners_avg = sum(m['corners'] for m in away_matches) / len(away_matches) if away_matches else 0

    prompt += f"""

STATISTIQUES AGREGEES {away_team} EXTERIEUR:
  - Moyenne tirs: {away_shots_avg:.1f}
  - Moyenne corners: {away_corners_avg:.1f}
"""

    # ================================================================
    # SECTION 4: CONTEXTE RUE DES JOUEURS
    # ================================================================

    if rdj_context:
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4: CONTEXTE & JOUEURS ABSENTS (Rue des Joueurs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLESSURES/SUSPENSIONS:
{rdj_context.get('injuries_text', 'Aucune info joueurs absents')}

COMPOSITIONS PROBABLES:
{rdj_context.get('lineups_text', 'Non disponible')}

ANALYSE COMPLETE DU MATCH:
{rdj_context.get('full_text', '')[:2000]}
"""

    # ================================================================
    # SECTION 5: CONDITIONS METEOROLOGIQUES
    # ================================================================

    if weather:
        weather_sentence = _generate_weather_sentence(weather)

        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5: CONDITIONS METEOROLOGIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{weather_sentence}

NOTE: Les calculs mathématiques ne sont PAS affectés par la météo. Cette information enrichit ton analyse contextuelle.
"""

    # ================================================================
    # SECTION 6: STATISTIQUES DETAILLEES (W-D-L, Buts, Gaps)
    # ================================================================

    if detailed_stats and (detailed_stats.get('home') or detailed_stats.get('away')):
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6: STATISTIQUES DETAILLEES DE LA SAISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        if detailed_stats.get('home'):
            home_stats = detailed_stats['home']
            prompt += f"""
{home_team}:
  Position: {home_stats.get('position', 'N/A')}e
  Matchs joués: {home_stats.get('played', 'N/A')}
  Bilan: {home_stats.get('won', 0)}V - {home_stats.get('drawn', 0)}N - {home_stats.get('lost', 0)}D
  Buts: {home_stats.get('goals_for', 0)} marqués, {home_stats.get('goals_against', 0)} encaissés (diff: {home_stats.get('goal_difference', 0):+d})
  Points: {home_stats.get('points', 'N/A')}
"""
            if home_stats.get('gap_to_top') is not None:
                prompt += f"  Écart au leader: {home_stats.get('gap_to_top', 0):+d} pts\n"
            if home_stats.get('gap_to_top4') is not None:
                prompt += f"  Écart au top 4: {home_stats.get('gap_to_top4', 0):+d} pts\n"
            if home_stats.get('gap_to_relegation') is not None:
                prompt += f"  Écart à la relégation: {home_stats.get('gap_to_relegation', 0):+d} pts\n"

        if detailed_stats.get('away'):
            away_stats = detailed_stats['away']
            prompt += f"""
{away_team}:
  Position: {away_stats.get('position', 'N/A')}e
  Matchs joués: {away_stats.get('played', 'N/A')}
  Bilan: {away_stats.get('won', 0)}V - {away_stats.get('drawn', 0)}N - {away_stats.get('lost', 0)}D
  Buts: {away_stats.get('goals_for', 0)} marqués, {away_stats.get('goals_against', 0)} encaissés (diff: {away_stats.get('goal_difference', 0):+d})
  Points: {away_stats.get('points', 'N/A')}
"""
            if away_stats.get('gap_to_top') is not None:
                prompt += f"  Écart au leader: {away_stats.get('gap_to_top', 0):+d} pts\n"
            if away_stats.get('gap_to_top4') is not None:
                prompt += f"  Écart au top 4: {away_stats.get('gap_to_top4', 0):+d} pts\n"
            if away_stats.get('gap_to_relegation') is not None:
                prompt += f"  Écart à la relégation: {away_stats.get('gap_to_relegation', 0):+d} pts\n"

    # ================================================================
    # INSTRUCTIONS DE RAISONNEMENT
    # ================================================================

    prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS DE RAISONNEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tu dois raisonner ETAPE PAR ETAPE comme un analyste expert:

ETAPE 1: PROFIL DE L'ADVERSAIRE
  - Quel est le profil de {away_team}? (top equipe? moyenne? faible?)
  - Quelle est sa defense exterieur? (solide? moyenne? faible?)
  - Quelle est sa forme recente?

ETAPE 2: RECHERCHE DE PATTERNS DANS L'HISTORIQUE
  - Cherche dans l'historique de {home_team} a domicile:
    SI adversaire avec defense similaire a {away_team}, combien de tirs?
  - Exemples de raisonnement:
    * SI defense adverse TOP 5 (rang 1-5) ALORS {home_team} fait X tirs
    * SI defense adverse MOYENNE (rang 8-12) ALORS {home_team} fait Y tirs
    * SI defense adverse FAIBLE (rang 15-20) ALORS {home_team} fait Z tirs

ETAPE 3: FORME RECENTE
  - SI {home_team} en bonne forme (top 8) ALORS ajuster +X tirs
  - SI {home_team} en mauvaise forme (15e+) ALORS ajuster -Y tirs

ETAPE 4: CONTEXTE SUPPLEMENTAIRE
  - Joueurs absents impactent-ils?
  - Meteo impact?
  - Autres facteurs?

ETAPE 5: PREDICTION FINALE
  - Synthetiser tout le raisonnement
  - Donner intervalle TIRS et CORNERS
  - Indiquer niveau de confiance

FORMAT DE REPONSE OBLIGATOIRE:

RAISONNEMENT:
[Ton raisonnement detaille etape par etape avec des SI/ALORS]

PREDICTION FINALE:
TIRS_MIN: [nombre]
TIRS_MAX: [nombre]
CORNERS_MIN: [nombre]
CORNERS_MAX: [nombre]
CONFIANCE: [0-100]%
"""

    # ================================================================
    # APPEL A L'IA
    # ================================================================

    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un analyste football expert qui raisonne de maniere structuree avec des SI/ALORS pour trouver des patterns."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )

        reasoning_text = response.choices[0].message.content

        # Parser la reponse
        result = _parse_ai_prediction(reasoning_text)
        result['full_reasoning'] = reasoning_text

        return result

    except Exception as e:
        print(f"[ERREUR IA DEEP REASONING] {e}")
        return {
            'error': str(e),
            'shots_min': 0,
            'shots_max': 0,
            'corners_min': 0,
            'corners_max': 0,
            'confidence': 0,
            'reasoning': ''
        }


def _generate_weather_sentence(weather: Dict) -> str:
    """
    Génère une phrase météo analysée et contextualisée

    Args:
        weather: Dict avec temperature, wind_speed, precipitation, condition

    Returns:
        Phrase complète analysant la météo et son impact potentiel
    """
    temp = weather.get('temperature', 15)
    wind = weather.get('wind_speed', 10)
    rain = weather.get('precipitation', 0)
    condition = weather.get('condition', 'Clear')

    # Température
    if temp < 0:
        temp_desc = "temps glacial"
        temp_impact = "Le froid intense pourrait rendre les joueurs moins réactifs et le ballon plus dur."
    elif temp < 5:
        temp_desc = "temps très froid"
        temp_impact = "Le froid pourrait légèrement affecter le contrôle du ballon."
    elif temp < 10:
        temp_desc = "temps frais"
        temp_impact = "Température fraîche mais sans impact significatif sur le jeu."
    elif temp < 25:
        temp_desc = "temps agréable"
        temp_impact = "Conditions idéales qui ne devraient pas affecter le jeu."
    elif temp < 30:
        temp_desc = "temps chaud"
        temp_impact = "La chaleur pourrait légèrement fatiguer les joueurs en fin de match."
    else:
        temp_desc = "chaleur intense"
        temp_impact = "La chaleur extrême pourrait fatiguer rapidement les joueurs et réduire l'intensité du jeu."

    # Pluie
    if rain > 5:
        rain_desc = "pluie forte"
        rain_impact = "Le ballon sera glissant, favorisant les erreurs techniques et les occasions de corners."
    elif rain > 1:
        rain_desc = "pluie légère"
        rain_impact = "Légère humidité sur le terrain, le ballon pourrait être un peu plus rapide."
    else:
        rain_desc = None
        rain_impact = None

    # Vent
    if wind > 40:
        wind_desc = "vent très fort"
        wind_impact = "Le vent perturbera les trajectoires de ballon, notamment sur les centres et corners."
    elif wind > 25:
        wind_desc = "vent fort"
        wind_impact = "Le vent pourrait affecter les passes longues et les corners."
    elif wind > 15:
        wind_desc = "vent modéré"
        wind_impact = None
    else:
        wind_desc = None
        wind_impact = None

    # Construction de la phrase
    parts = []

    # Partie 1: Description
    if rain_desc:
        if wind_desc:
            parts.append(f"{rain_desc.capitalize()} avec {wind_desc} et {temp_desc} ({temp}°C)")
        else:
            parts.append(f"{rain_desc.capitalize()} avec {temp_desc} ({temp}°C)")
    elif wind_desc:
        parts.append(f"{temp_desc.capitalize()} ({temp}°C) avec {wind_desc}")
    else:
        parts.append(f"{temp_desc.capitalize()} de {temp}°C")

    # Partie 2: Impact
    impacts = [imp for imp in [temp_impact, rain_impact, wind_impact] if imp]
    if impacts:
        parts.append(". ".join(impacts))

    return ". ".join(parts) + "."


def _parse_ai_prediction(text: str) -> Dict:
    """Parse la reponse de l'IA pour extraire les predictions"""
    import re

    result = {
        'shots_min': 20,
        'shots_max': 35,
        'corners_min': 6,
        'corners_max': 12,
        'confidence': 50,
        'reasoning': text
    }

    # Extraire TIRS_MIN
    match = re.search(r'TIRS_MIN:\s*(\d+)', text)
    if match:
        result['shots_min'] = int(match.group(1))

    # Extraire TIRS_MAX
    match = re.search(r'TIRS_MAX:\s*(\d+)', text)
    if match:
        result['shots_max'] = int(match.group(1))

    # Extraire CORNERS_MIN
    match = re.search(r'CORNERS_MIN:\s*(\d+)', text)
    if match:
        result['corners_min'] = int(match.group(1))

    # Extraire CORNERS_MAX
    match = re.search(r'CORNERS_MAX:\s*(\d+)', text)
    if match:
        result['corners_max'] = int(match.group(1))

    # Extraire CONFIANCE
    match = re.search(r'CONFIANCE:\s*(\d+)', text)
    if match:
        result['confidence'] = int(match.group(1))

    return result
