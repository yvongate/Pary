"""
IA Deep Reasoning - Verification independante avec raisonnement profond
L'IA recoit TOUTES les donnees et raisonne comme un analyste expert
"""
import os
from typing import Dict, List, Optional
import anthropic
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class DeepReasoningAnalyzer:
    """
    Classe pour analyser les matchs avec génération manuelle (sans historique complet)
    Utilisée pour les prédictions manuelles où l'utilisateur fournit compositions + propositions bookmaker
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            timeout=120.0
        )

    def analyze_match(self, context: Dict) -> Dict:
        """
        Analyse simplifiée pour génération manuelle

        Args:
            context: {
                'home_team': str,
                'away_team': str,
                'home_formation': str,
                'away_formation': str,
                'home_players': List[str],
                'away_players': List[str],
                'home_stats': {'avg_shots': float, 'avg_corners': float},
                'away_stats': {'avg_shots': float, 'avg_corners': float},
                'league': str,
                'match_date': str,
                'bookmaker_propositions': str (optionnel, texte brut)
            }

        Returns:
            {
                'shots_range': {'min': int, 'max': int},
                'corners_range': {'min': int, 'max': int},
                'reasoning': str,
                'best_value_bet': str (optionnel, si propositions fournies)
            }
        """
        home_team = context['home_team']
        away_team = context['away_team']
        home_formation = context['home_formation']
        away_formation = context['away_formation']
        home_stats = context.get('home_stats', {})
        away_stats = context.get('away_stats', {})
        bookmaker_props = context.get('bookmaker_propositions', '')

        # Construire le prompt
        prompt = f"""Tu es un ANALYSTE FOOTBALL EXPERT specialise dans le VALUE BETTING.

MATCH A ANALYSER:
{home_team} (DOMICILE) vs {away_team} (EXTERIEUR)
Championnat: {context.get('league', 'Unknown')}
Date: {context.get('match_date', '')}

COMPOSITIONS CONFIRMEES:

{home_team} ({home_formation}):
Joueurs: {', '.join(context.get('home_players', [])) if context.get('home_players') else 'Non fournis'}

{away_team} ({away_formation}):
Joueurs: {', '.join(context.get('away_players', [])) if context.get('away_players') else 'Non fournis'}

STATISTIQUES HISTORIQUES (BASELINE):

{home_team}:
  - Moyenne tirs: {home_stats.get('avg_shots', 0):.1f} tirs/match
  - Moyenne corners: {home_stats.get('avg_corners', 0):.1f} corners/match

{away_team}:
  - Moyenne tirs: {away_stats.get('avg_shots', 0):.1f} tirs/match
  - Moyenne corners: {away_stats.get('avg_corners', 0):.1f} corners/match

"""

        # Ajouter les propositions bookmaker si fournies
        if bookmaker_props and bookmaker_props.strip():
            prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 PROPOSITIONS BOOKMAKER (MARCHE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{bookmaker_props}

MISSION IMPORTANTE - DOUBLE ANALYSE:

TU DOIS IDENTIFIER 2 TYPES DE PARIS:
1. MEILLEUR VALUE BET (rentabilité long terme, bon EV)
2. PARI LE PLUS PROBABLE (maximiser chances de gagner CE pari)

Ces 2 paris sont souvent DIFFÉRENTS!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TYPES DE PROPOSITIONS A ANALYSER:

   A) TOTAL (Over/Under):
      - "+24.5 tirs @ 1.85" = Plus de 24.5 tirs TOTAL match
      - "-10.5 corners @ 1.90" = Moins de 10.5 corners TOTAL match

   B) HANDICAPS TIRS/CORNERS:
      - "PSG handicap tirs -5.5 @ 1.90" = PSG doit faire 6 tirs DE PLUS que adversaire
      - "Nantes handicap corners +2.5 @ 2.00" = Nantes peut avoir 3 corners DE MOINS

      CALCUL HANDICAP:
      - Handicap tirs PSG -5.5: PSG_tirs - Adversaire_tirs >= 6
      - Exemple: PSG 18 tirs, Nantes 7 tirs → Ecart +11 ✅ Gagne handicap -5.5
      - Exemple: PSG 15 tirs, Nantes 10 tirs → Ecart +5 ❌ Perd handicap -5.5

2. Pour CHAQUE proposition, calcule:

   A) PROBABILITÉ RÉELLE (ta prédiction):
      - Basée sur ton analyse tactique + stats + formations
      - Exemple: "+24.5 tirs" → ta prédiction = 28 tirs total → probabilité 80%

   B) PROBABILITÉ IMPLICITE (marché):
      - Probabilite implicite = 1 / cote
      - Exemple: cote 1.85 = 1/1.85 = 54%

   C) EXPECTED VALUE (EV):
      - EV = (ta_probabilite / proba_implicite) - 1
      - EV > 25%: FORTE VALUE
      - EV 10-25%: VALUE MODEREE
      - EV < 10%: PAS DE VALUE

3. Identifie les 2 MEILLEURS PARIS:

   A) MEILLEUR VALUE BET:
      - Cherche le plus grand EV positif
      - Focus: Rentabilité long terme
      - Accepte probabilité moyenne (60-70%) si excellente cote

   B) PARI LE PLUS PROBABLE:
      - Cherche la plus haute probabilité de réussite (> 75%)
      - Focus: Maximiser chances de gagner
      - Peu importe si EV négatif ou cote faible
      - Exemple: Probabilité 85% même avec cote 1.15

4. Justifie CHAQUE recommandation avec analyse tactique

IMPORTANT:
- Analyse TOUTES les propositions (total + handicaps)
- Recommande LA meilleure (plus grand EV)
- Calcule aussi les HANDICAPS OPTIMAUX meme si non fournis par bookmaker
"""

        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS DE RAISONNEMENT (ORDRE CRUCIAL !)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ IMPORTANT CRITIQUE:
TU DOIS FAIRE TA PROPRE ANALYSE EN PREMIER, **AVANT** DE REGARDER LES COTES.
NE LAISSE PAS LES COTES INFLUENCER TON ANALYSE TACTIQUE.

Les bookmakers ont des modèles sophistiqués MAIS:
- Ils n'ont pas les COMPOSITIONS confirmées en temps réel
- Ils ne font pas d'analyse TACTIQUE approfondie formations
- Les cotes intègrent la masse des parieurs (pas forcément rationnel)

TON AVANTAGE: Analyse tactique + compositions confirmées

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE 1: ANALYSE TACTIQUE INDEPENDANTE (SANS regarder les cotes!)

Analyse les formations:
- {home_formation}: Formation offensive, equilibree ou defensive?
- {away_formation}: Formation offensive, equilibree ou defensive?

Style de jeu probable:
- {home_team} avec {home_formation}: Plutot possession? Contre-attaque? Direct?
- {away_team} avec {away_formation}: Plutot possession? Contre-attaque? Direct?

Matchup tactique:
- Qui dominera la possession?
- Qui sera plus agressif offensivement?
- Style de jeu: Ouvert (beaucoup tirs) ou Fermé (bloc bas)?

Impact sur les tirs et corners:
- Formations offensives (4-3-3, 3-4-3) = plus de tirs attendus
- Formations defensives (5-4-1, 4-5-1) = moins de tirs attendus
- Bloc bas = plus de corners concedes
- Possession élevée = plus de tirs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE 2: PREDICTION COMPLETE (TA propre analyse, INDEPENDANTE du marché!)

Basé sur:
1. Stats historiques: {home_team} {home_stats.get('avg_shots', 0):.1f} tirs, {away_team} {away_stats.get('avg_shots', 0):.1f} tirs
2. Analyse tactique formations (étape 1)
3. Contexte du match

CALCULE (sans regarder les cotes bookmaker):

{home_team} prévu:
- Tirs: [X] (justifie avec formation + stats)
- Corners: [Y] (justifie avec style de jeu)

{away_team} prévu:
- Tirs: [Z] (justifie avec formation + stats)
- Corners: [W] (justifie avec style de jeu)

TOTAL MATCH prévu:
- Tirs total: [X + Z]
- Corners total: [Y + W]
- Écart tirs: {home_team} vs {away_team} = [X - Z]
- Écart corners: {home_team} vs {away_team} = [Y - W]

⚠️ CHECKPOINT: As-tu fait TA propre prédiction AVANT de regarder les cotes? OUI/NON
Si NON, recommence l'étape 2!

"""

        # Si propositions bookmaker, ajouter analyse value
        if bookmaker_props and bookmaker_props.strip():
            prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE 3: DETECTION DE VALUE (Compare TA prédiction avec le marché)

MAINTENANT (et seulement maintenant), compare TA prédiction (étape 2) avec les cotes bookmaker.

PROCESSUS DE DETECTION:

Pour CHAQUE proposition bookmaker:

A) Convertis la cote → probabilite implicite
   Formule: Proba implicite = 1 / cote

B) Calcule TA probabilite (basée sur TON analyse étape 2, PAS sur les cotes!)
   - Si proposition "+24.5 tirs" et ta prédiction est 28 tirs total
   - Ta probabilité réelle = Très élevée (ex: 75%)

C) Compare les 2 probabilités:
   - Proba implicite marché: 54% (1/1.85)
   - TA proba réelle: 75% (basée sur ton analyse)
   - ÉCART DÉTECTÉ: +21 points de %

D) Calcule Expected Value (EV):
   EV = (ta_proba / proba_implicite) - 1
   EV = (75 / 54) - 1 = +39% 🔥 FORTE VALUE!

E) Interprète le résultat:
   - EV > 25%: FORTE VALUE → Le marché sous-estime massivement
   - EV 10-25%: VALUE MODÉRÉE → Opportunité intéressante
   - EV < 10%: PAS DE VALUE → Marché bien calibré

Exemple concret:
Proposition: "+24.5 tirs @ 1.85"
- Proba implicite marché: 1/1.85 = 54%
- TA prédiction (étape 2): 28 tirs total
- TA proba réelle "+24.5": 75% (28 > 24.5 très probable)
- EV: (75/54) - 1 = +39% 🔥 FORTE VALUE!

JUSTIFICATION DE L'ÉCART:
Pourquoi le marché se trompe?
→ "Le bookmaker n'a pas vu que PSG joue en 4-3-3 ultra-offensif
   avec Mbappé-Neymar-Dembélé contre un bloc bas 5-4-1.
   Les compositions confirment une domination PSG massive."

ETAPE 4: Double Recommandation finale

Tu dois identifier 2 TYPES de paris distincts:

A) MEILLEUR VALUE BET:
   - Cherche le plus grand EV positif (> 10%)
   - Si EV > 25%: FORTE VALUE
   - Si EV 10-25%: VALUE MODEREE
   - Si EV < 10%: PAS DE VALUE
   - Focus: Rentabilité à long terme (bon rapport cote/probabilité)

B) PARI LE PLUS PROBABLE:
   - Cherche la proposition avec la PLUS HAUTE probabilité de réussite
   - Peu importe si la cote est faible (EV peut être négatif)
   - Focus: Maximiser les chances de gagner CE pari
   - Exemple: "+24.5 tirs" avec 85% de probabilité même si cote = 1.20 (EV négatif)

IMPORTANT: Ces 2 paris peuvent être DIFFÉRENTS!
- Value bet = Bon rapport risque/récompense
- Pari probable = Maximiser chances de gagner

FORMAT DE REPONSE OBLIGATOIRE (si propositions):

==================================================
MA PREDICTION INDEPENDANTE (étape 2 - AVANT analyse cotes)

{home_team}: [X] tirs, [Y] corners
{away_team}: [Z] tirs, [W] corners

TOTAL: [X+Z] tirs, [Y+W] corners
ÉCART: {home_team} +[X-Z] tirs, +[Y-W] corners

Base de calcul: Formations {home_formation} vs {away_formation}
+ Stats historiques + Analyse tactique

==================================================
🔥 MEILLEUR VALUE BET (Rentabilité long terme)

[Proposition] @ [cote]

- Expected Value: +X%
- MA probabilité réelle: X% (basée sur MA prédiction)
- Probabilité implicite marché: X% (1/cote)
- ÉCART: +Y points de %
- Type: FORTE VALUE / VALUE MODEREE / PAS DE VALUE

POURQUOI LE MARCHE SE TROMPE:
[Explique pourquoi TA analyse détecte quelque chose que le bookmaker n'a pas vu]
Exemple: "Le bookmaker n'a pas pris en compte les compositions
confirmées qui montrent un PSG ultra-offensif contre un bloc bas..."

JUSTIFICATION TACTIQUE:
[Analyse détaillée formations, joueurs, style de jeu]

==================================================
✅ PARI LE PLUS PROBABLE (Maximiser chances de gagner)

[Proposition] @ [cote]

- MA probabilité de réussite: X%
- Expected Value: +/-X% (peut être négatif)
- Probabilité implicite marché: X% (1/cote)
- Confiance: TRÈS HAUTE / HAUTE / MOYENNE

POURQUOI CE PARI EST SÛR:
[Explique pourquoi ce pari a les plus grandes chances de rentrer]
Exemple: "Avec PSG qui fait en moyenne 20 tirs à domicile et Nantes
qui concède 15 tirs, le total dépassera facilement 24.5 tirs."

JUSTIFICATION TACTIQUE:
[Analyse détaillée basée sur historique et contexte]

NOTE: Si le pari le plus probable = le meilleur value bet, indique:
"LE PARI LE PLUS PROBABLE EST AUSSI LE MEILLEUR VALUE BET"

==================================================
AUTRES PROPOSITIONS ANALYSEES

[Pour chaque autre proposition:]
- Probabilité réelle: X%
- EV: +/-X%
- Verdict: VALUE / PAS DE VALUE / EVITER

==================================================
HANDICAPS RECOMMANDES (calculés automatiquement)

HANDICAPS TIRS OPTIMAUX:
- {home_team} handicap tirs [valeur] @ [cote estimée]
  Ecart prevu: {home_team} [X] tirs - {away_team} [Y] tirs = +[Z] tirs

- {away_team} handicap tirs [valeur] @ [cote estimée]
  Ecart prevu: [calcul inverse]

HANDICAPS CORNERS OPTIMAUX:
- {home_team} handicap corners [valeur] @ [cote estimée]
  Ecart prevu: {home_team} [X] corners - {away_team} [Y] corners = +[Z] corners

- {away_team} handicap corners [valeur] @ [cote estimée]
  Ecart prevu: [calcul inverse]

NOTE: Ces handicaps sont calcules avec 70% de confiance.
      Si bookmaker propose handicap proche, FORTE VALUE potentielle!
==================================================
"""
        else:
            prompt += f"""
ETAPE 3: Prediction finale

Donne une fourchette realiste:
- Tirs min/max
- Corners min/max
"""

        prompt += f"""

FORMAT DE REPONSE FINAL:

PREDICTION BASELINE:
Total tirs: [min-max]
Total corners: [min-max]

SHOTS_RANGE_MIN: [nombre]
SHOTS_RANGE_MAX: [nombre]
CORNERS_RANGE_MIN: [nombre]
CORNERS_RANGE_MAX: [nombre]
"""

        # Appel à l'IA
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                temperature=0.3,
                system="Tu es un analyste football expert specialise dans le value betting et l'analyse tactique.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            reasoning_text = message.content[0].text

            # Parser la réponse
            result = self._parse_response(reasoning_text)
            result['reasoning'] = reasoning_text

            return result

        except Exception as e:
            print(f"[ERREUR IA DEEP REASONING] {e}")
            # Fallback
            total_shots = home_stats.get('avg_shots', 15) + away_stats.get('avg_shots', 10)
            total_corners = home_stats.get('avg_corners', 6) + away_stats.get('avg_corners', 4)

            return {
                'shots_range': {'min': int(total_shots - 5), 'max': int(total_shots + 5)},
                'corners_range': {'min': int(total_corners - 3), 'max': int(total_corners + 3)},
                'reasoning': f'Erreur IA: {e}. Utilisation baseline historique.'
            }

    def _parse_response(self, text: str) -> Dict:
        """Parse la réponse de l'IA"""
        import re

        result = {
            'shots_range': {'min': 20, 'max': 30},
            'corners_range': {'min': 8, 'max': 12}
        }

        # Extraire SHOTS_RANGE_MIN
        match = re.search(r'SHOTS_RANGE_MIN:\s*(\d+)', text)
        if match:
            result['shots_range']['min'] = int(match.group(1))

        # Extraire SHOTS_RANGE_MAX
        match = re.search(r'SHOTS_RANGE_MAX:\s*(\d+)', text)
        if match:
            result['shots_range']['max'] = int(match.group(1))

        # Extraire CORNERS_RANGE_MIN
        match = re.search(r'CORNERS_RANGE_MIN:\s*(\d+)', text)
        if match:
            result['corners_range']['min'] = int(match.group(1))

        # Extraire CORNERS_RANGE_MAX
        match = re.search(r'CORNERS_RANGE_MAX:\s*(\d+)', text)
        if match:
            result['corners_range']['max'] = int(match.group(1))

        return result


def generate_deep_analysis_prediction(
    match: Dict,
    home_history: List[Dict],
    away_history: List[Dict],
    current_rankings: Dict,
    rdj_context: Optional[Dict] = None,
    weather: Optional[Dict] = None,
    detailed_stats: Optional[Dict] = None,
    lineups: Optional[Dict] = None,
    home_formation_stats: Optional[Dict] = None,
    away_formation_stats: Optional[Dict] = None
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
        home_formation_stats: Stats Understat formation équipe domicile
        away_formation_stats: Stats Understat formation équipe extérieur

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

    client = anthropic.Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        timeout=120.0  # 2 minutes timeout (au lieu du défaut)
    )

    home_team = match['home_team']
    away_team = match['away_team']

    # ================================================================
    # CONSTRUIRE LE PROMPT ULTRA-DETAILLE
    # ================================================================

    prompt = f"""Tu es un ANALYSTE FOOTBALL EXPERT. Tu dois predire le nombre de TIRS et CORNERS pour ce match.

IMPORTANT: Tu dois raisonner ETAPE PAR ETAPE avec des "SI/ALORS" en cherchant des PATTERNS dans l'historique.

CONSIGNES DE FORMATAGE (CRITIQUE):
- N'utilise PAS de markdown (#, **, |, ```, etc.)
- N'utilise PAS de tableaux markdown
- Utilise du TEXTE SIMPLE et LISIBLE
- Utilise des tirets (-) pour les listes
- Utilise des MAJUSCULES pour les titres
- Utilise des espaces/indentations pour structurer
- Evite les symboles speciaux (→, ✅, ❌, etc.)
- Ecris comme si c'etait dans un email ou SMS

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
    # SECTION 6B: STATISTIQUES HISTORIQUES DES FORMATIONS (UNDERSTAT)
    # ================================================================

    if home_formation_stats and away_formation_stats:
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6B: PERFORMANCES HISTORIQUES DES FORMATIONS (Understat)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚽ {home_team} avec formation confirmée {home_formation_stats['formation']}:

  STATISTIQUES OFFENSIVES (quand {home_team} attaque):
    - Tirs/90: {home_formation_stats['shots_per_90']}
    - Buts/90: {home_formation_stats['goals_per_90']}
    - xG/90: {home_formation_stats['xg_per_90']}
    - Minutes jouées: {home_formation_stats['minutes']} ({home_formation_stats['percentage_used']}% du temps)
    - Caractère: {"OFFENSIVE" if home_formation_stats['xg_per_90'] > 1.5 else "ÉQUILIBRÉE" if home_formation_stats['xg_per_90'] > 1.2 else "DÉFENSIVE"}

  STATISTIQUES DÉFENSIVES (quand {home_team} défend):
    - Tirs concédés/90: {home_formation_stats['shots_against_per_90']}
    - Buts concédés/90: {home_formation_stats['goals_against_per_90']}
    - xGA/90: {home_formation_stats['xga_per_90']}
    - Solidité: {"FORTE" if home_formation_stats['xga_per_90'] < 1.2 else "MOYENNE" if home_formation_stats['xga_per_90'] < 1.5 else "FAIBLE"}

⚽ {away_team} avec formation confirmée {away_formation_stats['formation']}:

  STATISTIQUES OFFENSIVES (quand {away_team} attaque):
    - Tirs/90: {away_formation_stats['shots_per_90']}
    - Buts/90: {away_formation_stats['goals_per_90']}
    - xG/90: {away_formation_stats['xg_per_90']}
    - Minutes jouées: {away_formation_stats['minutes']} ({away_formation_stats['percentage_used']}% du temps)
    - Caractère: {"OFFENSIVE" if away_formation_stats['xg_per_90'] > 1.5 else "ÉQUILIBRÉE" if away_formation_stats['xg_per_90'] > 1.2 else "DÉFENSIVE"}

  STATISTIQUES DÉFENSIVES (quand {away_team} défend):
    - Tirs concédés/90: {away_formation_stats['shots_against_per_90']}
    - Buts concédés/90: {away_formation_stats['goals_against_per_90']}
    - xGA/90: {away_formation_stats['xga_per_90']}
    - Solidité: {"FORTE" if away_formation_stats['xga_per_90'] < 1.2 else "MOYENNE" if away_formation_stats['xga_per_90'] < 1.5 else "FAIBLE"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE TACTIQUE (APPROCHE SYMÉTRIQUE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POUR {home_team}:
  - Offensive {home_team} en {home_formation_stats['formation']}: {home_formation_stats['shots_per_90']} tirs/90
  - Défensive {away_team} en {away_formation_stats['formation']}: concède {away_formation_stats['shots_against_per_90']} tirs/90
  - Moyenne baseline: ({home_formation_stats['shots_per_90']} + {away_formation_stats['shots_against_per_90']}) / 2 = {(home_formation_stats['shots_per_90'] + away_formation_stats['shots_against_per_90']) / 2:.1f} tirs
  - Ratio xG/xGA: {home_formation_stats['xg_per_90']} / {away_formation_stats['xga_per_90']} = {home_formation_stats['xg_per_90'] / away_formation_stats['xga_per_90'] if away_formation_stats['xga_per_90'] > 0 else 'N/A':.2f} {"→ Dominance nette" if away_formation_stats['xga_per_90'] > 0 and home_formation_stats['xg_per_90'] / away_formation_stats['xga_per_90'] > 1.3 else "→ Match équilibré"}

POUR {away_team}:
  - Offensive {away_team} en {away_formation_stats['formation']}: {away_formation_stats['shots_per_90']} tirs/90
  - Défensive {home_team} en {home_formation_stats['formation']}: concède {home_formation_stats['shots_against_per_90']} tirs/90
  - Moyenne baseline: ({away_formation_stats['shots_per_90']} + {home_formation_stats['shots_against_per_90']}) / 2 = {(away_formation_stats['shots_per_90'] + home_formation_stats['shots_against_per_90']) / 2:.1f} tirs
  - Ratio xG/xGA: {away_formation_stats['xg_per_90']} / {home_formation_stats['xga_per_90']} = {away_formation_stats['xg_per_90'] / home_formation_stats['xga_per_90'] if home_formation_stats['xga_per_90'] > 0 else 'N/A':.2f} {"→ Dominance nette" if home_formation_stats['xga_per_90'] > 0 and away_formation_stats['xg_per_90'] / home_formation_stats['xga_per_90'] > 1.3 else "→ Match équilibré"}

PONDÉRATION FIABILITÉ:
  - {home_team} {home_formation_stats['formation']}: {home_formation_stats['minutes']} min = {"échantillon FORT" if home_formation_stats['minutes'] > 900 else "échantillon MOYEN" if home_formation_stats['minutes'] > 450 else "échantillon FAIBLE"}
  - {away_team} {away_formation_stats['formation']}: {away_formation_stats['minutes']} min = {"échantillon FORT" if away_formation_stats['minutes'] > 900 else "échantillon MOYEN" if away_formation_stats['minutes'] > 450 else "échantillon FAIBLE"}
"""
    else:
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6B: FORMATIONS (NON DISPONIBLES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ FORMATIONS NON DISPONIBLES

Raisons possibles:
  - Compositions non encore publiées (match dans > 1h)
  - Erreur service SerpAPI ou Understat
  - Formations jamais utilisées cette saison
  - Équipes non suivies par Understat

STRATÉGIE FALLBACK:
  - Utiliser l'historique général de {home_team} à domicile (Section 1)
  - Utiliser l'historique général de {away_team} à l'extérieur (Section 1)
  - Ajuster avec contexte (blessures, classements, météo)
  - Prioriser les classements et forme récente
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

ETAPE 2: Utiliser les formations confirmées (SYMÉTRIQUE)
  - {home_team} en {home_formation_stats['formation'] if home_formation_stats else 'N/A'} fait historiquement {home_formation_stats['shots_per_90'] if home_formation_stats else 'N/A'} tirs/90
  - {away_team} en {away_formation_stats['formation'] if away_formation_stats else 'N/A'} concède {away_formation_stats['shots_against_per_90'] if away_formation_stats else 'N/A'} tirs/90
  - Moyenne baseline formations: ({home_formation_stats['shots_per_90'] if home_formation_stats else 0} + {away_formation_stats['shots_against_per_90'] if away_formation_stats else 0}) / 2 tirs
  - Valider avec ratio xG/xGA (dominance si > 1.3)
  - Si pas de formations, utilise l'historique général de {home_team} à domicile

ETAPE 3: Contexte {home_team}
  - Blessures/suspensions impactantes?
  - Forme récente?
  - Cohérence avec classements?

ETAPE 4: Prédiction {home_team}
  - Baseline formations (étape 2) ajusté avec contexte (étape 3)
  - Combien de tirs et corners pour {home_team}?


PARTIE B: ANALYSE {away_team} (EXTERIEUR)
──────────────────────────────────────

ETAPE 5: Profil de {away_team}
  - Position, forme, force offensive et défensive à l'extérieur?

ETAPE 6: Utiliser les formations confirmées (SYMÉTRIQUE)
  - {away_team} en {away_formation_stats['formation'] if away_formation_stats else 'N/A'} fait historiquement {away_formation_stats['shots_per_90'] if away_formation_stats else 'N/A'} tirs/90
  - {home_team} en {home_formation_stats['formation'] if home_formation_stats else 'N/A'} concède {home_formation_stats['shots_against_per_90'] if home_formation_stats else 'N/A'} tirs/90
  - Moyenne baseline formations: ({away_formation_stats['shots_per_90'] if away_formation_stats else 0} + {home_formation_stats['shots_against_per_90'] if home_formation_stats else 0}) / 2 tirs
  - Valider avec ratio xG/xGA (dominance si > 1.3)
  - Si pas de formations, utilise l'historique général de {away_team} à l'extérieur

ETAPE 7: Contexte {away_team}
  - Blessures/suspensions impactantes?
  - Forme récente?
  - Cohérence avec classements?

ETAPE 8: Prédiction {away_team}
  - Baseline formations (étape 6) ajusté avec contexte (étape 7)
  - Combien de tirs et corners pour {away_team}?


PARTIE C: SYNTHESE FINALE
──────────────────────────

ETAPE 9: Vérification cohérence
  - Le total est-il réaliste? (≈28 tirs, ≈11 corners total)
  - Ajustements nécessaires?

FORMAT DE REPONSE OBLIGATOIRE - TEXTE SIMPLE SANS MARKDOWN:

EXEMPLE DE BON FORMATAGE:
==================================================
RAISONNEMENT DETAILLE - Arsenal vs Chelsea
==================================================

PARTIE A: ANALYSE ARSENAL (DOMICILE)

ETAPE 1: Profil d'Arsenal
Arsenal est actuellement 1er du championnat avec 67 points.
Leur forme recente est excellente (2e sur 8 matchs).
A domicile, ils sont classes 10e en attaque et 10e en defense.

ETAPE 2: Baseline historique
En analysant les 14 derniers matchs a domicile:
  - Moyenne: 15.6 tirs et 5.8 corners
  - Contre equipes du top 6: 12 tirs en moyenne
  - Contre equipes du bas: 18 tirs en moyenne

ETAPE 3: Contexte et ajustements
Blessures: Aucune absence majeure
Forme: 3 victoires sur les 4 derniers matchs a domicile
Motivation: Match important pour garder la 1re place

ETAPE 4: Prediction Arsenal
Baseline: 15-16 tirs, 5-6 corners
Ajustements: +1 tir (bonne forme), +0 corner
Prediction finale Arsenal: 15-17 tirs, 5-6 corners

[Meme structure pour PARTIE B avec l'equipe exterieur]

PARTIE C: SYNTHESE FINALE
Total predit: 27-33 tirs, 10-12 corners
Coherence: OUI, dans les normes d'un match de Premier League

==================================================
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
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            temperature=0.3,
            system="Tu es un analyste football expert qui raisonne de maniere structuree avec des SI/ALORS pour trouver des patterns.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        reasoning_text = message.content[0].text

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
