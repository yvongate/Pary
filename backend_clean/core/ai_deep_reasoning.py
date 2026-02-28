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
    formations: Optional[Dict] = None
) -> Dict:
    """
    L'IA recoit TOUTES les donnees et fait un raisonnement ultra-profond

    Args:
        match: Info du match (home_team, away_team, league)
        home_history: Historique complet equipe domicile
        away_history: Historique complet equipe exterieur
        current_rankings: LES 12 TABLEAUX de soccerstats
        rdj_context: Contexte Rue des Joueurs
        weather: Meteo
        formations: Formations si disponibles

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

{rdj_context.get('injuries_summary', 'Aucune info joueurs absents')}

ANALYSE COMPLETE:
{rdj_context.get('full_text', '')[:1000]}
"""

    # ================================================================
    # SECTION 5: METEO
    # ================================================================

    if weather:
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5: CONDITIONS METEOROLOGIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Temperature: {weather.get('temperature', 'N/A')}°C
Vent: {weather.get('wind_speed', 'N/A')} km/h
Conditions: {weather.get('condition', 'N/A')}
"""

    # ================================================================
    # SECTION 6: FORMATIONS
    # ================================================================

    if formations:
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6: FORMATIONS PREVUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team}: {formations.get('home_formation', 'Inconnue')}
{away_team}: {formations.get('away_formation', 'Inconnue')}
"""

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
