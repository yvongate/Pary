"""
IA Deep Reasoning - Verification independante avec raisonnement profond
L'IA recoit TOUTES les donnees et raisonne comme un analyste expert

Format de raisonnement restaure du commit bf4507ae (sans corners):
- 9 etapes structurees (PARTIE A: 1-4, PARTIE B: 5-8, PARTIE C: 9)
- Comparaisons naturelles face aux differents types d'equipes du championnat
- Predictions precises + intervalles (min/max)
- Focus uniquement sur les TIRS
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
                'home_stats': {'avg_shots': float},
                'away_stats': {'avg_shots': float},
                'league': str,
                'match_date': str,
                'bookmaker_propositions': str (optionnel, texte brut)
            }

        Returns:
            {
                'shots_range': {'min': int, 'max': int},
                'reasoning': str,
                'best_value_bet': str (optionnel, si propositions fournies),
                'best_balanced_bet': str (optionnel, si propositions fournies)
            }
        """
        home_team = context['home_team']
        away_team = context['away_team']
        home_formation = context['home_formation']
        away_formation = context['away_formation']
        home_stats = context.get('home_stats', {})
        away_stats = context.get('away_stats', {})
        bookmaker_props = context.get('bookmaker_propositions', '')

        # Extraire les classements et stats détaillées
        rankings = context.get('rankings', {})
        detailed_stats = context.get('detailed_stats', {})
        match_history = context.get('match_history', {})

        home_detailed = detailed_stats.get('home', {}) or {}
        away_detailed = detailed_stats.get('away', {}) or {}

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1: CLASSEMENTS ACTUELS (données live)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team}:
  - Classement général: {rankings.get('home_standings_rank', home_detailed.get('position', '?'))}e sur 20
  - Points: {home_detailed.get('points', 'Non fourni')} ({home_detailed.get('won', '?')}V-{home_detailed.get('drawn', '?')}N-{home_detailed.get('lost', '?')}D)
  - Buts: {home_detailed.get('goals_for', '?')} marqués / {home_detailed.get('goals_against', '?')} encaissés
  - Rang attaque domicile: {rankings.get('home_attack_rank', 'Non fourni')}e
  - Rang défense domicile: {rankings.get('home_defence_rank', 'Non fourni')}e
  - Rang forme (8 derniers matchs): {rankings.get('home_form_rank', 'Non fourni')}e

{away_team}:
  - Classement général: {rankings.get('away_standings_rank', away_detailed.get('position', '?'))}e sur 20
  - Points: {away_detailed.get('points', 'Non fourni')} ({away_detailed.get('won', '?')}V-{away_detailed.get('drawn', '?')}N-{away_detailed.get('lost', '?')}D)
  - Buts: {away_detailed.get('goals_for', '?')} marqués / {away_detailed.get('goals_against', '?')} encaissés
  - Rang attaque extérieur: {rankings.get('away_attack_rank', 'Non fourni')}e
  - Rang défense extérieur: {rankings.get('away_defence_rank', 'Non fourni')}e
  - Rang forme (8 derniers matchs): {rankings.get('away_form_rank', 'Non fourni')}e

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2: STATISTIQUES HISTORIQUES (BASELINE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{home_team}:
  - Moyenne tirs: {home_stats.get('avg_shots', 0):.1f} tirs/match
  - Moyenne tirs cadrés: {home_stats.get('avg_shots_on_target', home_stats.get('avg_shots', 0) * 0.45):.1f} tirs/match

{away_team}:
  - Moyenne tirs: {away_stats.get('avg_shots', 0):.1f} tirs/match
  - Moyenne tirs cadrés: {away_stats.get('avg_shots_on_target', away_stats.get('avg_shots', 0) * 0.45):.1f} tirs/match

"""

        # Ajouter l'historique des matchs si disponible
        home_history = match_history.get('home', [])
        away_history = match_history.get('away', [])

        if home_history or away_history:
            prompt += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3: HISTORIQUE DES MATCHS (pour analyse par type d'adversaire)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            if home_history:
                prompt += f"\n{home_team} à DOMICILE (derniers matchs):\n"
                for match in home_history[:10]:  # 10 derniers matchs
                    opponent = match.get('opponent', 'Unknown')
                    shots = match.get('shots', '?')  # Champ correct: 'shots' pas 'team_shots'
                    date = match.get('date', '?')
                    prompt += f"  - vs {opponent}: {shots} tirs ({date})\n"

            if away_history:
                prompt += f"\n{away_team} à l'EXTÉRIEUR (derniers matchs):\n"
                for match in away_history[:10]:
                    opponent = match.get('opponent', 'Unknown')
                    shots = match.get('shots', '?')  # Champ correct: 'shots' pas 'team_shots'
                    date = match.get('date', '?')
                    prompt += f"  - vs {opponent}: {shots} tirs ({date})\n"

            prompt += "\n"

        # SECTION 4: Météo (si disponible)
        weather = context.get('weather', {})
        if weather:
            prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4: MÉTÉO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Conditions: {weather.get('condition', 'Non fourni')}
Température: {weather.get('temperature', '?')}°C
Vent: {weather.get('wind_speed', '?')} km/h
Impact potentiel: {weather.get('impact_description', 'Non évalué')}

"""

        # SECTION 5: Blessures et contexte RDJ (si disponible)
        rdj_context = context.get('rdj_context', {})
        if rdj_context:
            injuries = rdj_context.get('injuries_text', '')
            if injuries:
                prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5: BLESSURES ET SUSPENSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{injuries[:800]}

"""

        # SECTION 6: Stats formations Understat (si disponible)
        formation_stats = context.get('formation_stats', {})
        home_form_stats = formation_stats.get('home', {})
        away_form_stats = formation_stats.get('away', {})
        if home_form_stats or away_form_stats:
            prompt += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6: STATS FORMATIONS (Understat)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            if home_form_stats:
                prompt += f"""{home_team} en {home_form_stats.get('formation', home_formation)}:
  - Tirs/90: {home_form_stats.get('shots_per_90', '?')}
  - xG/90: {home_form_stats.get('xg_per_90', '?')}
  - Tirs concédés/90: {home_form_stats.get('shots_against_per_90', '?')}

"""
            if away_form_stats:
                prompt += f"""{away_team} en {away_form_stats.get('formation', away_formation)}:
  - Tirs/90: {away_form_stats.get('shots_per_90', '?')}
  - xG/90: {away_form_stats.get('xg_per_90', '?')}
  - Tirs concédés/90: {away_form_stats.get('shots_against_per_90', '?')}

"""

        # Derby indicator
        is_derby = context.get('is_derby', False)
        if is_derby:
            prompt += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ DERBY - Match à enjeu émotionnel fort
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ce match est identifié comme un DERBY local.
Les derbies ont tendance à être plus disputés avec:
- Plus d'engagement physique
- Potentiellement plus de fautes et tensions
- Atmosphère électrique qui peut affecter le jeu

"""

        # Raisonnement tactique déjà calculé (si disponible)
        tactical_reasoning = context.get('tactical_reasoning', '')
        if tactical_reasoning:
            prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSE TACTIQUE (pré-calculée)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{tactical_reasoning}

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
1. MEILLEUR VALUE BET (rentabilité long terme, EV maximal)
2. BEST BALANCED BET (haute probabilité + bonne cote = sweet spot)

Ces 2 paris sont souvent DIFFÉRENTS!

Le "Balanced Bet" est le COMPROMIS OPTIMAL:
- Probabilité élevée pour sécurité (>70%)
- Cote décente pour rentabilité (>1.60)
- Ni trop risqué, ni cote trop faible

EXEMPLE CONCRET (PSG vs Nantes):

=== TIRS ===

TOTAUX TIRS:
Proposition A: "+27.5 tirs @ 2.50"
→ EV: +30%, Probabilité: 65%, Cote: 2.50
→ Type: VALUE BET candidat

Proposition B: "+25.5 tirs @ 1.85"
→ EV: +15%, Probabilité: 78%, Cote: 1.85
→ Type: BALANCED BET candidat ✅

Proposition C: "+23.5 tirs @ 1.35"
→ EV: -8%, Probabilité: 92%, Cote: 1.35
→ Type: REJETE (cote trop faible <1.60) ❌

HANDICAPS TIRS:
Proposition D: "PSG handicap tirs -7.5 @ 2.80"
→ EV: +35%, Probabilité: 62%, Cote: 2.80
→ Type: MEILLEUR VALUE BET (EV maximal) 🔥

Proposition E: "PSG handicap tirs -5.5 @ 1.90"
→ EV: +18%, Probabilité: 72%, Cote: 1.90
→ Type: Autre BALANCED BET candidat

RECOMMANDATIONS FINALES TIRS:
🔥 Value Bet: Handicap "PSG tirs -7.5 @ 2.80" (EV +35%)
⚖️ Balanced Bet: Total "+25.5 tirs @ 1.85" (prob 78%, cote décente)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TYPES DE PROPOSITIONS A ANALYSER:

   A) TOTAUX TIRS (Over/Under):
      - "+24.5 tirs @ 1.85" = Plus de 24.5 tirs TOTAL match

   B) HANDICAPS TIRS:
      - "PSG handicap tirs -5.5 @ 1.90" = PSG doit faire 6 tirs DE PLUS que adversaire

      CALCUL HANDICAP TIRS:
      - Handicap tirs PSG -5.5: PSG_tirs - Adversaire_tirs >= 6
      - Exemple: PSG 18 tirs, Nantes 7 tirs → Ecart +11 ✅ Gagne handicap -5.5
      - Exemple: PSG 15 tirs, Nantes 10 tirs → Ecart +5 ❌ Perd handicap -5.5

2. Pour CHAQUE proposition, calcule:

   A) PROBABILITÉ RÉELLE (ta prédiction):
      - Basée sur ton analyse tactique + stats + formations

      POUR TOTAUX TIRS:
      - Exemple: "+24.5 tirs" → ta prédiction = 28 tirs total → probabilité 80%

      POUR HANDICAPS TIRS:
      - Exemple: "PSG -5.5 tirs" → ta prédiction = PSG 20 tirs, Nantes 8 tirs
        → Écart prévu = +12 tirs → Dépasse largement -5.5 → probabilité 75%
      - Exemple: "PSG -9.5 tirs" → ta prédiction = PSG 20 tirs, Nantes 8 tirs
        → Écart prévu = +12 tirs → Dépasse -9.5 de peu → probabilité 55%

   B) PROBABILITÉ IMPLICITE (marché):
      - Probabilite implicite = 1 / cote
      - Exemple: cote 1.85 = 1/1.85 = 54%

   C) EXPECTED VALUE (EV):
      - EV = (ta_probabilite / proba_implicite) - 1
      - EV > 25%: FORTE VALUE
      - EV 10-25%: VALUE MODEREE
      - EV < 10%: PAS DE VALUE

3. Identifie les 2 MEILLEURS PARIS pour les TIRS:

   ⚠️ IMPORTANT: Tu dois analyser et recommander des paris pour:
   - TIRS (totaux + handicaps)

   Pour TIRS, identifie 2 paris:
   1. MEILLEUR VALUE BET (EV maximal)
   2. BEST BALANCED BET (sweet spot)

   Tes recommandations pour TIRS peuvent être:
   - 2 totaux tirs différents
   - 1 total tirs + 1 handicap tirs
   - 2 handicaps tirs différents

   Choisis le MEILLEUR pari de chaque type!

   A) MEILLEUR VALUE BET pour TIRS:
      - Cherche le plus grand EV positif (parmi totaux ET handicaps)
      - Focus: Rentabilité long terme
      - Accepte probabilité moyenne (60-70%) si excellente cote
      - Exemples TIRS:
        * Total: "+27.5 tirs @ 2.50" (EV +30%, proba 65%)
        * Handicap: "PSG tirs -6.5 @ 2.20" (EV +28%, proba 68%)
      → Choisis celui avec le MEILLEUR EV pour TIRS!

   B) BEST BALANCED BET (Sweet Spot) pour TIRS:
      - Cherche le MEILLEUR COMPROMIS (parmi totaux ET handicaps)
      - Critères OBLIGATOIRES:
        * Probabilité > 70% (bonne sécurité)
        * Cote > 1.60 (rentabilité décente)
        * EV > 5% (au moins un peu de value)
      - Focus: Balance entre sécurité et rentabilité
      - Exemples TIRS:
        * Total: "+25.5 tirs @ 1.85" (EV +15%, proba 78%)
        * Handicap: "PSG tirs -4.5 @ 1.75" (EV +12%, proba 76%)
      → Choisis celui avec le MEILLEUR compromis pour TIRS!

      NOTE IMPORTANTE: NE PAS recommander de cotes trop faibles (<1.60)!
      Si toutes les propositions probables ont cotes <1.60, indique:
      "AUCUN PARI EQUILIBRE - Toutes les cotes probables sont trop faibles"

4. Justifie CHAQUE recommandation avec analyse tactique

IMPORTANT:
- Analyse TOUTES les propositions (total + handicaps)
- Recommande LA meilleure (plus grand EV)
- Calcule aussi les HANDICAPS OPTIMAUX meme si non fournis par bookmaker
"""

        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS DE RAISONNEMENT (OBLIGATOIRES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Tu dois raisonner ETAPE PAR ETAPE en cherchant des PATTERNS.
Tu DOIS analyser les performances SELON LE TYPE D'ADVERSAIRE (top 5, milieu, bas de tableau).
Tu DOIS citer les CLASSEMENTS et POSITIONS exactes des équipes.

PARTIE A: ANALYSE {home_team} (DOMICILE)
──────────────────────────────────────

ETAPE 1: Profil de {home_team} avec CLASSEMENTS (OBLIGATOIRE - cite les chiffres!)
  - Classement général: Xe sur 20
  - Classement domicile: Xe
  - Classement attaque: Xe / Classement défense: Xe
  - TYPE D'EQUIPE: top 5 (1er-5e) / milieu (6e-14e) / bas (15e-20e)

ETAPE 2: Baseline historique PAR TYPE D'ADVERSAIRE (OBLIGATOIRE)
  Analyse les stats de {home_team} à domicile:
  - Moyenne générale: {home_stats.get('avg_shots', 0):.1f} tirs/match
  - Contre équipes du TOP 5: environ X tirs (moins car adversaire fort)
  - Contre équipes du MILIEU: environ Y tirs
  - Contre équipes du BAS: environ Z tirs (plus car adversaire faible)

  {away_team} est une équipe du [TOP 5 / MILIEU / BAS].
  Donc {home_team} devrait faire environ [X/Y/Z] tirs.

  Formation {home_team} en {home_formation}: ajustement si formation offensive/défensive

ETAPE 3: Contexte et ajustements {home_team}
  - Blessures/suspensions impactantes? (+/- X tirs)
  - Forme récente? (+/- X tirs)
  - Motivation du match? (+/- X tirs)

ETAPE 4: Prédiction {home_team}
  - Baseline (étape 2): X tirs (basé sur type adversaire)
  - Ajustements (étape 3): +/- X tirs
  - Prédiction finale {home_team}: X tirs (fourchette X-Y)


PARTIE B: ANALYSE {away_team} (EXTERIEUR)
──────────────────────────────────────

ETAPE 5: Profil de {away_team} avec CLASSEMENTS (OBLIGATOIRE - cite les chiffres!)
  - Classement général: Xe sur 20
  - Classement extérieur: Xe
  - Classement attaque: Xe / Classement défense: Xe
  - TYPE D'EQUIPE: top 5 (1er-5e) / milieu (6e-14e) / bas (15e-20e)

ETAPE 6: Baseline historique PAR TYPE D'ADVERSAIRE (OBLIGATOIRE)
  Analyse les stats de {away_team} à l'extérieur:
  - Moyenne générale: {away_stats.get('avg_shots', 0):.1f} tirs/match
  - A l'extérieur vs TOP 5: environ X tirs (moins car adversaire fort)
  - A l'extérieur vs MILIEU: environ Y tirs
  - A l'extérieur vs BAS: environ Z tirs (plus car adversaire faible)

  {home_team} est une équipe du [TOP 5 / MILIEU / BAS].
  Donc {away_team} devrait faire environ [X/Y/Z] tirs.

  Formation {away_team} en {away_formation}: ajustement si formation offensive/défensive

ETAPE 7: Contexte et ajustements {away_team}
  - Blessures/suspensions impactantes? (+/- X tirs)
  - Forme récente? (+/- X tirs)
  - Motivation du match? (+/- X tirs)

ETAPE 8: Prédiction {away_team}
  - Baseline (étape 6): X tirs (basé sur type adversaire)
  - Ajustements (étape 7): +/- X tirs
  - Prédiction finale {away_team}: X tirs (fourchette X-Y)


PARTIE C: SYNTHESE FINALE
──────────────────────────

ETAPE 9: Vérification cohérence
  - Total prédit: X tirs ({home_team}) + Y tirs ({away_team}) = Z tirs total
  - Cohérence avec les classements? (équipe forte vs faible = écart important)
  - Ajustements finaux si nécessaire

"""

        # Si propositions bookmaker, ajouter analyse value
        if bookmaker_props and bookmaker_props.strip():
            prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE SUPPLEMENTAIRE: DETECTION DE VALUE (Compare TA prédiction avec le marché)

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

Exemples concrets:

TIRS:
Proposition: "+24.5 tirs @ 1.85"
- Proba implicite marché: 1/1.85 = 54%
- TA prédiction (étape 2): 28 tirs total
- TA proba réelle "+24.5": 75% (28 > 24.5 très probable)
- EV: (75/54) - 1 = +39% 🔥 FORTE VALUE!

JUSTIFICATION DE L'ÉCART TIRS:
Pourquoi le marché se trompe?
→ "Le bookmaker n'a pas vu que PSG joue en 4-3-3 ultra-offensif
   avec Mbappé-Neymar-Dembélé contre un bloc bas 5-4-1.
   Les compositions confirment une domination PSG massive."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE 3.5: VALIDATION STATIQUE (CRITIQUE - OBLIGATOIRE!)

⚠️ AVANT de recommander quoi que ce soit, tu DOIS valider la cohérence mathématique!

Cette étape empêche les erreurs, incohérences et fausses alertes.

═══════════════════════════════════════════════════════
RÈGLE 1: VÉRIFIER LES SEUILS D'EXPECTED VALUE (EV)
═══════════════════════════════════════════════════════

Pour CHAQUE proposition analysée:

A) Si EV < 10%:
   Décision: ❌ REJETER
   Raison: Le marché est mieux calibré que ma prédiction
   Message: "Marché trop proche, pas d'avantage détectable"
   Action: NE PAS recommander ce pari

B) Si 10% ≤ EV < 25%:
   Décision: ✅ VALUE MODÉRÉE (normal)
   Raison: Écart normal qu'un bon modèle peut détecter
   Message: "Bonne value, cohérente avec mon avantage analytique"
   Action: Recommander le pari

C) Si 25% ≤ EV < 50%:
   Décision: ⚠️ VALUE ÉLEVÉE (vigilance)
   Raison: Écart important, vérifier avant de valider
   Message: "Value intéressante mais inhabituelle"
   Action: Recommander MAIS ajouter avertissement:
   "⚠️ EV élevé (+X%). Vérifiez manuellement les compositions et contexte."

D) Si EV ≥ 50%:
   Décision: 🚨 RED FLAG (probable erreur)
   Raison: Trop beau pour être vrai
   Message: "Écart anormalement élevé (+X%).
   Soit opportunité exceptionnelle rare, soit j'ai raté une info importante.
   VÉRIFICATION MANUELLE OBLIGATOIRE avant de parier!"
   Action: Recommander avec ALERTE MAXIMUM

═══════════════════════════════════════════════════════
RÈGLE 2: VÉRIFIER LA COHÉRENCE INTERNE
═══════════════════════════════════════════════════════

Vérification A - Total des tirs:

Si tu prévois: {home_team} [X] tirs, {away_team} [Z] tirs
Alors total = [X + Z] tirs

Vérifie CHAQUE proposition "+ligne" ou "-ligne":
- Si "+27.5 tirs" et ton total = 30 → ✅ Cohérent
- Si "+35.5 tirs" et ton total = 30 → ❌ INCOHÉRENT (rejette!)

Vérification B - Probabilités extrêmes (suspect):

- Si probabilité > 90% → Suspect (sauf cas très rare comme PSG vs amateur)
- Si probabilité < 10% mais EV positif → Incohérent (rejette!)

Vérification C - Logique des handicaps:

Si tu prévois écart de +8 tirs pour {home_team}:
- Handicap {home_team} -5.5 → ✅ Cohérent (8 > 5.5)
- Handicap {home_team} -10.5 → ❌ Incohérent (8 < 10.5, rejette!)

═══════════════════════════════════════════════════════
RÈGLE 3: DÉTECTER LES BIAIS DES DEUX CÔTÉS (CRITIQUE!)
═══════════════════════════════════════════════════════

🚨 RÈGLE MATHÉMATIQUE FONDAMENTALE:

Deux paris OPPOSÉS ne peuvent PAS avoir de value simultanément!

Exemple d'INCOHÉRENCE à détecter:
- {home_team} handicap -4.5 @ 2.37 → EV: +17%
- {away_team} handicap +4.5 @ 2.37 → EV: +12%

🚨 IMPOSSIBLE! Ce sont des paris opposés:
- Si {home_team} -4.5 gagne → {away_team} +4.5 perd
- Si {away_team} +4.5 gagne → {home_team} -4.5 perd

ACTION OBLIGATOIRE:
Si tu détectes value des DEUX côtés d'un même pari:
→ REJETTE LES DEUX
→ Indique: "Incohérence mathématique détectée. Mes calculs sont erronés."

Exception acceptable:
Si TOUS les EV positifs sont du MÊME côté → ✅ Normal
Exemple: Tous les bons paris sur {home_team} (si dominance claire)

═══════════════════════════════════════════════════════
RÈGLE 4: CONCLUSION DE VALIDATION
═══════════════════════════════════════════════════════

Pour CHAQUE pari candidat, vérifie:

✅ CAS 1 - VALIDATION RÉUSSIE:
- EV entre 10-25%
- Cohérence interne OK (totaux corrects, probas normales)
- Pas de biais des deux côtés
→ PARI VALIDÉ, procède à la recommandation

⚠️ CAS 2 - VALIDATION AVEC VIGILANCE:
- EV entre 25-50%
- OU probabilité > 85% (vérifier pourquoi)
→ PARI VALIDÉ avec avertissement vigilance

🚨 CAS 3 - VALIDATION AVEC ALERTE MAX:
- EV ≥ 50%
→ PARI VALIDÉ mais ALERTE MAXIMUM (vérification manuelle obligatoire)

❌ CAS 4 - REJET:
- EV < 10%
- OU incohérence interne (totaux, probas)
- OU biais des deux côtés
- OU probabilité > 95% (sauf contexte exceptionnel)
→ PARI REJETÉ, ne pas recommander

⚠️ SI AUCUN PARI NE PASSE LA VALIDATION:
Indique clairement:
"Aucune proposition ne passe les critères de validation.
Le marché est bien calibré ou mes prédictions manquent de confiance.
Recommandation: NE PAS PARIER sur ce match."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ETAPE 4: Recommandations finales (TIRS)

⚠️ CRITIQUE: Tu dois analyser et recommander pour:
1. TIRS (totaux + handicaps)

Identifie 2 TYPES de paris distincts:

A) MEILLEUR VALUE BET:
   - Cherche le plus grand EV positif (> 10%) dans cette catégorie
   - Si EV > 25%: FORTE VALUE
   - Si EV 10-25%: VALUE MODEREE
   - Si EV < 10%: PAS DE VALUE
   - Focus: Rentabilité à long terme (EV maximal)
   - Accepte probabilité moyenne (60-65%) si excellente cote (>2.00)
   - Peut être un total OU un handicap de cette catégorie

B) BEST BALANCED BET (Sweet Spot):
   - Cherche le MEILLEUR COMPROMIS de cette catégorie
   - Critères OBLIGATOIRES:
     * Probabilité > 70% (bonne sécurité)
     * Cote > 1.60 (rentabilité décente)
     * EV > 5% (au moins un peu de value)
   - Focus: Ni trop risqué, ni cote trop faible
   - Peut être un total OU un handicap de cette catégorie

   ⚠️ IMPORTANT: Rejette les cotes <1.60 même si probabilité 95%!
   Si aucune proposition ne respecte les 3 critères, indique:
   "AUCUN PARI EQUILIBRE TROUVE - Cotes trop faibles ou probabilités insuffisantes"

EXEMPLES DE RECOMMANDATIONS VALIDES:

TIRS:
- Value: Total "+27.5 tirs @ 2.50", Balanced: Total "+25.5 tirs @ 1.85"
- Value: Handicap "PSG tirs -7.5 @ 2.80", Balanced: Total "+25.5 tirs @ 1.85"
- Value: Handicap "PSG tirs -7.5 @ 2.80", Balanced: Handicap "PSG tirs -5.5 @ 1.90"

IMPORTANT: Ces 2 paris sont souvent DIFFÉRENTS!
- Value bet = EV maximal (peut être risqué, total OU handicap)
- Balanced bet = Sweet spot sécurité/rentabilité (total OU handicap)

FORMAT DE REPONSE OBLIGATOIRE (si propositions):

==================================================
MA PREDICTION INDEPENDANTE (étape 2 - AVANT analyse cotes)

{home_team}: [X] tirs
{away_team}: [Z] tirs

TOTAL: [X+Z] tirs
ÉCART: {home_team} +[X-Z] tirs

Base de calcul: Formations {home_formation} vs {away_formation}
+ Stats historiques + Analyse tactique

==================================================
🔥 MEILLEUR VALUE BET (EV Maximal - Rentabilité long terme)

[Type: TOTAL ou HANDICAP] [Proposition] @ [cote]

Exemples:
- TOTAL: "+27.5 tirs @ 2.50"
- HANDICAP: "PSG handicap tirs -7.5 @ 2.80"

- Expected Value: +X%
- MA probabilité réelle: X%
- Probabilité implicite marché: X% (1/cote)
- ÉCART: +Y points de %
- Type: FORTE VALUE / VALUE MODEREE / PAS DE VALUE

POURQUOI LE MARCHE SE TROMPE:
[Explique pourquoi TA analyse détecte quelque chose que le bookmaker n'a pas vu]
Exemple pour total: "Le bookmaker n'a pas pris en compte les compositions
confirmées qui montrent un PSG ultra-offensif contre un bloc bas..."
Exemple pour handicap: "Avec PSG qui fait 20 tirs à domicile et Nantes
seulement 8, l'écart de +12 tirs dépassera largement le handicap -7.5..."

JUSTIFICATION TACTIQUE:
[Analyse détaillée formations, joueurs, style de jeu]

==================================================
⚖️ BEST BALANCED BET (Sweet Spot - Compromis optimal)

[Type: TOTAL ou HANDICAP] [Proposition] @ [cote] OU "AUCUN PARI EQUILIBRE TROUVE"

Exemples:
- TOTAL: "+25.5 tirs @ 1.85"
- HANDICAP: "PSG handicap tirs -5.5 @ 1.90"

Si trouvé:
- MA probabilité de réussite: X% (doit être >70%)
- Cote: X.XX (doit être >1.60)
- Expected Value: +X% (doit être >5%)
- Balance: EXCELLENTE / BONNE

POURQUOI C'EST LE MEILLEUR COMPROMIS:
[Explique le balance entre sécurité (haute probabilité) et rentabilité (bonne cote)]
Exemple pour total: "Probabilité 76% garantit bonne sécurité, tout en gardant
une cote 1.82 qui offre rentabilité décente (+18% EV). Ni trop risqué, ni cote trop faible."
Exemple pour handicap: "Avec écart prévu de +8 tirs pour PSG, le handicap -5.5
a 74% de chances de réussite, tout en offrant cote 1.90 décente."

JUSTIFICATION TACTIQUE:
[Analyse détaillée basée sur historique et contexte]

Si aucun trouvé:
"AUCUN PARI EQUILIBRE TROUVE
Raison: [Toutes les cotes probables sont <1.60 / Aucune proposition >70% de probabilité / Etc.]"

NOTE: Si le balanced bet = le value bet, indique:
"LE MEILLEUR VALUE BET EST AUSSI LE MEILLEUR PARI EQUILIBRE (JACKPOT!)"

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

NOTE: Ces handicaps sont calcules avec 70% de confiance.
      Si bookmaker propose handicap proche, FORTE VALUE potentielle!
==================================================
"""
        else:
            prompt += f"""

ETAPE 3: Prediction finale

Donne une fourchette realiste:
- Tirs min/max
"""

        prompt += f"""

FORMAT DE REPONSE FINAL:

PREDICTION BASELINE:
Total tirs: [nombre_precis] ([min]-[max])

SHOTS: [nombre_precis] (prediction centrale)
SHOTS_RANGE_MIN: [nombre]
SHOTS_RANGE_MAX: [nombre]
"""

        # Appel à l'IA
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
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

            # Parser la réponse
            result = self._parse_response(reasoning_text)
            result['reasoning'] = reasoning_text

            return result

        except Exception as e:
            print(f"[ERREUR IA DEEP REASONING] {e}")
            # Fallback
            total_shots = home_stats.get('avg_shots', 15) + away_stats.get('avg_shots', 10)

            return {
                'shots_range': {'min': int(total_shots - 5), 'max': int(total_shots + 5)},
                'reasoning': f'Erreur IA: {e}. Utilisation baseline historique.'
            }

    def _parse_response(self, text: str) -> Dict:
        """Parse la réponse de l'IA"""
        import re

        result = {
            'shots': 25,
            'shots_range': {'min': 20, 'max': 30}
        }

        # Extraire SHOTS (nombre précis)
        match = re.search(r'SHOTS:\s*(\d+)', text)
        if match:
            result['shots'] = int(match.group(1))

        # Extraire SHOTS_RANGE_MIN
        match = re.search(r'SHOTS_RANGE_MIN:\s*(\d+)', text)
        if match:
            result['shots_range']['min'] = int(match.group(1))

        # Extraire SHOTS_RANGE_MAX
        match = re.search(r'SHOTS_RANGE_MAX:\s*(\d+)', text)
        if match:
            result['shots_range']['max'] = int(match.group(1))

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

    prompt = f"""Tu es un ANALYSTE FOOTBALL EXPERT. Tu dois predire DEUX METRIQUES pour ce match:
1. Le nombre de TIRS (tirs totaux)
2. Le nombre de TIRS CADRES (shots on target)

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
   Tirs: {match_data['shots']}"""
        if match_data.get('goals_for') is not None:
            prompt += f" | Score: {match_data['goals_for']}-{match_data['goals_against']}"

    # Stats agregees
    home_shots_avg = sum(m['shots'] for m in home_matches) / len(home_matches) if home_matches else 0

    prompt += f"""

STATISTIQUES AGREGEES {home_team} DOMICILE:
  - Moyenne tirs: {home_shots_avg:.1f}
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
   Tirs: {match_data['shots']}"""
        if match_data.get('goals_for') is not None:
            prompt += f" | Score: {match_data['goals_for']}-{match_data['goals_against']}"

    away_shots_avg = sum(m['shots'] for m in away_matches) / len(away_matches) if away_matches else 0

    prompt += f"""

STATISTIQUES AGREGEES {away_team} EXTERIEUR:
  - Moyenne tirs: {away_shots_avg:.1f}
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
5. Utilise ces infos CONFIRMEES pour affiner tes prédictions de tirs

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
INSTRUCTIONS DE RAISONNEMENT (OBLIGATOIRES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Tu dois raisonner ETAPE PAR ETAPE en cherchant des PATTERNS dans l'historique.
Tu DOIS utiliser les CLASSEMENTS de la SECTION 1 et l'HISTORIQUE des SECTIONS 2-3.
Tu DOIS analyser les performances SELON LE TYPE D'ADVERSAIRE (top 5, milieu, bas).

PARTIE A: ANALYSE {home_team} (DOMICILE)
──────────────────────────────────────

ETAPE 1: Profil de {home_team} avec CLASSEMENTS (OBLIGATOIRE - cite les chiffres!)
  - Classement général: Xe sur 20 (cite le chiffre de SECTION 1)
  - Classement domicile: Xe
  - Classement attaque: Xe / Classement défense: Xe
  - Forme (8 derniers matchs): Xe
  - TYPE D'EQUIPE: top 5 (1er-5e) / milieu (6e-14e) / bas (15e-20e)

ETAPE 2: Baseline historique PAR TYPE D'ADVERSAIRE (OBLIGATOIRE - analyse SECTION 2)
  Analyse les matchs de {home_team} à domicile et REGROUPE par position adversaire:
  - Moyenne générale: X tirs/match (tous matchs confondus)
  - Contre équipes du TOP 5 (1er-5e): X tirs en moyenne (cite les adversaires)
  - Contre équipes du MILIEU (6e-14e): Y tirs en moyenne
  - Contre équipes du BAS (15e-20e): Z tirs en moyenne

  {away_team} est actuellement Xe au classement général.
  Donc {home_team} devrait faire environ [X/Y/Z] tirs (selon le groupe de {away_team}).

  SI formations disponibles:
  - {home_team} en {home_formation_stats['formation'] if home_formation_stats else 'N/A'}: {home_formation_stats['shots_per_90'] if home_formation_stats else 'N/A'} tirs/90
  - Valider avec les stats formations

ETAPE 3: Contexte et ajustements {home_team}
  - Blessures/suspensions impactantes? (+/- X tirs)
  - Forme récente? (+/- X tirs)
  - Motivation du match? (+/- X tirs)

ETAPE 4: Prédiction {home_team}
  - Baseline (étape 2): X tirs (basé sur historique vs type adversaire)
  - Ajustements (étape 3): +/- X tirs
  - Prédiction finale {home_team}: X tirs (fourchette X-Y)


PARTIE B: ANALYSE {away_team} (EXTERIEUR)
──────────────────────────────────────

ETAPE 5: Profil de {away_team} avec CLASSEMENTS (OBLIGATOIRE - cite les chiffres!)
  - Classement général: Xe sur 20 (cite le chiffre de SECTION 1)
  - Classement extérieur: Xe
  - Classement attaque: Xe / Classement défense: Xe
  - Forme (8 derniers matchs): Xe
  - TYPE D'EQUIPE: top 5 (1er-5e) / milieu (6e-14e) / bas (15e-20e)

ETAPE 6: Baseline historique PAR TYPE D'ADVERSAIRE (OBLIGATOIRE - analyse SECTION 3)
  Analyse les matchs de {away_team} à l'extérieur et REGROUPE par position adversaire:
  - Moyenne générale: X tirs/match (tous matchs confondus)
  - A l'extérieur vs TOP 5 (1er-5e): X tirs en moyenne
  - A l'extérieur vs MILIEU (6e-14e): Y tirs en moyenne
  - A l'extérieur vs BAS (15e-20e): Z tirs en moyenne

  {home_team} est actuellement Xe au classement général.
  Donc {away_team} devrait faire environ [X/Y/Z] tirs (selon le groupe de {home_team}).

  SI formations disponibles:
  - {away_team} en {away_formation_stats['formation'] if away_formation_stats else 'N/A'}: {away_formation_stats['shots_per_90'] if away_formation_stats else 'N/A'} tirs/90
  - Valider avec les stats formations

ETAPE 7: Contexte et ajustements {away_team}
  - Blessures/suspensions impactantes? (+/- X tirs)
  - Forme récente? (+/- X tirs)
  - Motivation du match? (+/- X tirs)

ETAPE 8: Prédiction {away_team}
  - Baseline (étape 6): X tirs (basé sur historique vs type adversaire)
  - Ajustements (étape 7): +/- X tirs
  - Prédiction finale {away_team}: X tirs (fourchette X-Y)


PARTIE C: SYNTHESE FINALE
──────────────────────────

ETAPE 9: Vérification cohérence
  - Total prédit: X tirs ({home_team}) + Y tirs ({away_team}) = Z tirs total
  - Cohérence avec les classements? (équipe forte vs faible = écart important)
  - Ajustements finaux si nécessaire

FORMAT DE REPONSE OBLIGATOIRE - TEXTE SIMPLE SANS MARKDOWN:

EXEMPLE DE BON FORMATAGE:
==================================================
RAISONNEMENT DETAILLE - Arsenal vs Chelsea
==================================================

PARTIE A: ANALYSE ARSENAL (DOMICILE)

ETAPE 1: Profil d'Arsenal avec CLASSEMENTS
  - Classement general: 1er sur 20 (67 points)
  - Classement domicile: 2e
  - Classement attaque: 1er / Classement defense: 3e
  - Forme (8 derniers matchs): 2e
  - TYPE D'EQUIPE: TOP 5

ETAPE 2: Baseline historique PAR TYPE D'ADVERSAIRE
En analysant les 14 derniers matchs a domicile:
  - Moyenne generale: 15.6 tirs
  - Contre equipes du TOP 5 (Man City, Liverpool, Chelsea, Tottenham): 12 tirs en moyenne
  - Contre equipes du MILIEU (6e-14e): 15 tirs en moyenne
  - Contre equipes du BAS (15e-20e): 18 tirs en moyenne

Chelsea est actuellement 6e au classement (equipe du MILIEU).
Donc Arsenal devrait faire environ 15 tirs (moyenne vs milieu de tableau).

ETAPE 3: Contexte et ajustements
  - Blessures: Aucune absence majeure (+0 tir)
  - Forme: 3 victoires sur 4 derniers a domicile (+1 tir)
  - Motivation: Match important pour le titre (+0 tir)

ETAPE 4: Prediction Arsenal
  - Baseline (etape 2): 15 tirs (vs equipe du milieu)
  - Ajustements: +1 tir (bonne forme)
  - Prediction finale Arsenal: 16 tirs (fourchette 15-17)


PARTIE B: ANALYSE CHELSEA (EXTERIEUR)

ETAPE 5: Profil de Chelsea avec CLASSEMENTS
  - Classement general: 6e sur 20
  - Classement exterieur: 8e
  - Classement attaque: 5e / Classement defense: 7e
  - Forme (8 derniers matchs): 10e
  - TYPE D'EQUIPE: MILIEU

ETAPE 6: Baseline historique PAR TYPE D'ADVERSAIRE
En analysant les 12 derniers matchs a l'exterieur:
  - Moyenne generale: 12.3 tirs
  - A l'exterieur vs TOP 5 (Arsenal, Man City, Liverpool): 10 tirs en moyenne
  - A l'exterieur vs MILIEU (6e-14e): 12 tirs en moyenne
  - A l'exterieur vs BAS (15e-20e): 15 tirs en moyenne

Arsenal est actuellement 1er au classement (equipe du TOP 5).
Donc Chelsea devrait faire environ 10 tirs (moyenne vs top 5 a l'exterieur).

ETAPE 7: Contexte et ajustements
  - Blessures: Attaquant principal absent (-1 tir)
  - Forme: Moyenne recemment (+0 tir)
  - Motivation: Qualif Europe en jeu (+1 tir)

ETAPE 8: Prediction Chelsea
  - Baseline (etape 6): 10 tirs (vs equipe du top 5)
  - Ajustements: -1 +1 = +0 tirs
  - Prediction finale Chelsea: 10 tirs (fourchette 9-12)


PARTIE C: SYNTHESE FINALE

ETAPE 9: Verification coherence
  - Total predit: 16 (Arsenal) + 10 (Chelsea) = 26 tirs
  - Coherence: OUI (Arsenal 1er vs Chelsea 6e = domination logique)
  - Ecart: Arsenal +6 tirs (coherent avec classements)

==================================================
PREDICTION FINALE:

EQUIPE DOMICILE ({home_team}):

TIRS TOTAUX:
HOME_TIRS: 16 tirs (prediction centrale)
HOME_TIRS_MIN: 15
HOME_TIRS_MAX: 17

TIRS CADRES:
HOME_TIRS_CADRES: 7 tirs cadrés (prediction centrale)
HOME_TIRS_CADRES_MIN: 6
HOME_TIRS_CADRES_MAX: 8

EQUIPE EXTERIEUR ({away_team}):

TIRS TOTAUX:
AWAY_TIRS: 10 tirs (prediction centrale)
AWAY_TIRS_MIN: 9
AWAY_TIRS_MAX: 12

TIRS CADRES:
AWAY_TIRS_CADRES: 4 tirs cadrés (prediction centrale)
AWAY_TIRS_CADRES_MIN: 3
AWAY_TIRS_CADRES_MAX: 5

TOTAUX:
TOTAL_TIRS: 26 tirs au total (somme des predictions centrales)
TOTAL_TIRS_CADRES: 11 tirs cadrés au total

CONFIANCE: 82%
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
        rain_impact = "Le ballon sera glissant, favorisant les erreurs techniques."
    elif rain > 1:
        rain_desc = "pluie légère"
        rain_impact = "Légère humidité sur le terrain, le ballon pourrait être un peu plus rapide."
    else:
        rain_desc = None
        rain_impact = None

    # Vent
    if wind > 40:
        wind_desc = "vent très fort"
        wind_impact = "Le vent perturbera les trajectoires de ballon, notamment sur les centres."
    elif wind > 25:
        wind_desc = "vent fort"
        wind_impact = "Le vent pourrait affecter les passes longues."
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
    """Parse la reponse de l'IA pour extraire les predictions des DEUX équipes (tirs)"""
    import re

    result = {
        'home_shots': 14,
        'home_shots_min': 10,
        'home_shots_max': 18,
        'home_shots_on_target': 6,
        'home_shots_on_target_min': 5,
        'home_shots_on_target_max': 8,
        'away_shots': 10,
        'away_shots_min': 8,
        'away_shots_max': 16,
        'away_shots_on_target': 4,
        'away_shots_on_target_min': 3,
        'away_shots_on_target_max': 6,
        'total_shots': 24,
        'total_shots_on_target': 10,
        'confidence': 50,
        'reasoning': text
    }

    # ===== TIRS TOTAUX =====
    # Extraire HOME_TIRS (nombre précis)
    match = re.search(r'HOME_TIRS:\s*(\d+)', text)
    if match:
        result['home_shots'] = int(match.group(1))

    # Extraire HOME_TIRS_MIN
    match = re.search(r'HOME_TIRS_MIN:\s*(\d+)', text)
    if match:
        result['home_shots_min'] = int(match.group(1))

    # Extraire HOME_TIRS_MAX
    match = re.search(r'HOME_TIRS_MAX:\s*(\d+)', text)
    if match:
        result['home_shots_max'] = int(match.group(1))

    # Extraire AWAY_TIRS (nombre précis)
    match = re.search(r'AWAY_TIRS:\s*(\d+)', text)
    if match:
        result['away_shots'] = int(match.group(1))

    # Extraire AWAY_TIRS_MIN
    match = re.search(r'AWAY_TIRS_MIN:\s*(\d+)', text)
    if match:
        result['away_shots_min'] = int(match.group(1))

    # Extraire AWAY_TIRS_MAX
    match = re.search(r'AWAY_TIRS_MAX:\s*(\d+)', text)
    if match:
        result['away_shots_max'] = int(match.group(1))

    # Extraire TOTAL_TIRS (nombre précis)
    match = re.search(r'TOTAL_TIRS:\s*(\d+)', text)
    if match:
        result['total_shots'] = int(match.group(1))

    # ===== TIRS CADRES =====
    # Extraire HOME_TIRS_CADRES
    match = re.search(r'HOME_TIRS_CADRES:\s*(\d+)', text)
    if match:
        result['home_shots_on_target'] = int(match.group(1))

    # Extraire HOME_TIRS_CADRES_MIN
    match = re.search(r'HOME_TIRS_CADRES_MIN:\s*(\d+)', text)
    if match:
        result['home_shots_on_target_min'] = int(match.group(1))

    # Extraire HOME_TIRS_CADRES_MAX
    match = re.search(r'HOME_TIRS_CADRES_MAX:\s*(\d+)', text)
    if match:
        result['home_shots_on_target_max'] = int(match.group(1))

    # Extraire AWAY_TIRS_CADRES
    match = re.search(r'AWAY_TIRS_CADRES:\s*(\d+)', text)
    if match:
        result['away_shots_on_target'] = int(match.group(1))

    # Extraire AWAY_TIRS_CADRES_MIN
    match = re.search(r'AWAY_TIRS_CADRES_MIN:\s*(\d+)', text)
    if match:
        result['away_shots_on_target_min'] = int(match.group(1))

    # Extraire AWAY_TIRS_CADRES_MAX
    match = re.search(r'AWAY_TIRS_CADRES_MAX:\s*(\d+)', text)
    if match:
        result['away_shots_on_target_max'] = int(match.group(1))

    # Extraire TOTAL_TIRS_CADRES
    match = re.search(r'TOTAL_TIRS_CADRES:\s*(\d+)', text)
    if match:
        result['total_shots_on_target'] = int(match.group(1))

    # Extraire CONFIANCE
    match = re.search(r'CONFIANCE:\s*(\d+)', text)
    if match:
        result['confidence'] = int(match.group(1))

    return result
