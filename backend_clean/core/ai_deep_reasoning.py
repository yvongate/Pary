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
    detailed_stats: Optional[Dict] = None,
    lineups: Optional[Dict] = None
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
        lineups: Compositions confirmées récupérées via SerpAPI

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
    # SECTION 6: COMPOSITIONS CONFIRMEES (LINEUPS)
    # ================================================================

    if lineups and lineups.get('lineup_raw_text'):
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6: COMPOSITIONS CONFIRMEES (LINEUPS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ COMPOSITIONS OFFICIELLES (récupérées 1h avant le match via SerpAPI)

TEXTE BRUT DES RESULTATS DE RECHERCHE:
{lineups.get('lineup_raw_text')[:2000]}

INSTRUCTIONS IMPORTANTES:
1. Parse ce texte pour identifier les formations exactes des deux équipes
2. Identifie les joueurs clés titulaires et remplaçants
3. Analyse l'impact tactique:
   - Formations défensives (5-4-1, 4-5-1, 4-4-2) = moins de tirs attendus
   - Formations offensives (4-3-3, 3-4-3, 4-2-4) = plus de tirs attendus
   - Formations équilibrées (4-2-3-1, 3-5-2) = tirs modérés
4. Croiser avec les absences mentionnées dans RDJ pour valider cohérence
5. Utilise ces infos CONFIRMEES pour affiner tes prédictions de tirs/corners

Note: Si le texte ne contient pas d'infos claires, utilise ton analyse des autres sections.
"""

    # ================================================================
    # SECTION 7: STATISTIQUES DETAILLEES (W-D-L, Buts, Gaps)
    # ================================================================

    if detailed_stats and (detailed_stats.get('home') or detailed_stats.get('away')):
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7: STATISTIQUES DETAILLEES DE LA SAISON
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

Tu dois raisonner ETAPE PAR ETAPE comme un analyste expert et prédire LES DEUX ÉQUIPES:

PARTIE A: ANALYSE {home_team} (DOMICILE)
──────────────────────────────────────

ETAPE 1: Profil de {home_team}
  - Position, forme, force offensive et défensive à domicile?

ETAPE 2: Analyse de la défense adverse ({away_team})
  - Quelle est la qualité de la défense extérieur de {away_team}?
  - Cherche dans l'historique de {home_team} à domicile:
    SI adversaire avec défense similaire à {away_team}, combien de tirs?

ETAPE 3: Contexte {home_team}
  - Blessures/suspensions impactantes?
  - Forme récente?

ETAPE 4: Prédiction {home_team}
  - Combien de tirs et corners pour {home_team}?


PARTIE B: ANALYSE {away_team} (EXTERIEUR)
──────────────────────────────────────

ETAPE 5: Profil de {away_team}
  - Position, forme, force offensive et défensive à l'extérieur?

ETAPE 6: Analyse de la défense adverse ({home_team})
  - Quelle est la qualité de la défense domicile de {home_team}?
  - Cherche dans l'historique de {away_team} à l'extérieur:
    SI adversaire avec défense similaire à {home_team}, combien de tirs?

ETAPE 7: Contexte {away_team}
  - Blessures/suspensions impactantes?
  - Forme récente?

ETAPE 8: Prédiction {away_team}
  - Combien de tirs et corners pour {away_team}?


PARTIE C: SYNTHESE FINALE
──────────────────────────

ETAPE 9: Vérification cohérence
  - Le total est-il réaliste? (≈28 tirs, ≈11 corners total)
  - Ajustements nécessaires?

FORMAT DE REPONSE OBLIGATOIRE:

RAISONNEMENT:
[Ton raisonnement détaillé des 9 étapes ci-dessus]

PREDICTION FINALE:

EQUIPE DOMICILE ({home_team}):
HOME_TIRS_MIN: [nombre]
HOME_TIRS_MAX: [nombre]
HOME_CORNERS_MIN: [nombre]
HOME_CORNERS_MAX: [nombre]

EQUIPE EXTERIEUR ({away_team}):
AWAY_TIRS_MIN: [nombre]
AWAY_TIRS_MAX: [nombre]
AWAY_CORNERS_MIN: [nombre]
AWAY_CORNERS_MAX: [nombre]

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
    """Parse la reponse de l'IA pour extraire les predictions des DEUX équipes"""
    import re

    result = {
        'home_shots_min': 10,
        'home_shots_max': 18,
        'home_corners_min': 3,
        'home_corners_max': 7,
        'away_shots_min': 8,
        'away_shots_max': 16,
        'away_corners_min': 2,
        'away_corners_max': 6,
        'confidence': 50,
        'reasoning': text
    }

    # Extraire HOME_TIRS_MIN
    match = re.search(r'HOME_TIRS_MIN:\s*(\d+)', text)
    if match:
        result['home_shots_min'] = int(match.group(1))

    # Extraire HOME_TIRS_MAX
    match = re.search(r'HOME_TIRS_MAX:\s*(\d+)', text)
    if match:
        result['home_shots_max'] = int(match.group(1))

    # Extraire HOME_CORNERS_MIN
    match = re.search(r'HOME_CORNERS_MIN:\s*(\d+)', text)
    if match:
        result['home_corners_min'] = int(match.group(1))

    # Extraire HOME_CORNERS_MAX
    match = re.search(r'HOME_CORNERS_MAX:\s*(\d+)', text)
    if match:
        result['home_corners_max'] = int(match.group(1))

    # Extraire AWAY_TIRS_MIN
    match = re.search(r'AWAY_TIRS_MIN:\s*(\d+)', text)
    if match:
        result['away_shots_min'] = int(match.group(1))

    # Extraire AWAY_TIRS_MAX
    match = re.search(r'AWAY_TIRS_MAX:\s*(\d+)', text)
    if match:
        result['away_shots_max'] = int(match.group(1))

    # Extraire AWAY_CORNERS_MIN
    match = re.search(r'AWAY_CORNERS_MIN:\s*(\d+)', text)
    if match:
        result['away_corners_min'] = int(match.group(1))

    # Extraire AWAY_CORNERS_MAX
    match = re.search(r'AWAY_CORNERS_MAX:\s*(\d+)', text)
    if match:
        result['away_corners_max'] = int(match.group(1))

    # Extraire CONFIANCE
    match = re.search(r'CONFIANCE:\s*(\d+)', text)
    if match:
        result['confidence'] = int(match.group(1))

    return result
