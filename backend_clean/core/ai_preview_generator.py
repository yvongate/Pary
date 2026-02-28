#!/usr/bin/env python3
"""
Générateur d'analyses pré-match avec IA
Combine GNews + CSV stats + LLM pour créer des analyses comme FlashScore
"""

import os
from typing import Dict, Any, Optional
from gnews import GNews
import pandas as pd
from datetime import datetime, timedelta

# Configuration IA (exemple avec OpenAI)
# pip install openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI not installed. Run: pip install openai")


def get_team_recent_form(team_name: str, league_code: str, num_matches: int = 5) -> Dict[str, Any]:
    """
    Calcule la forme récente d'une équipe depuis les CSV

    Returns:
        {
            "matches": [...],  # Derniers matchs
            "wins": 3,
            "draws": 1,
            "losses": 1,
            "goals_for": 8,
            "goals_against": 5,
            "form_string": "W-W-D-W-L"
        }
    """
    season = "2526"  # TODO: calculer dynamiquement
    filepath = f"data/{league_code}_{season}.csv"

    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')

    # Filtrer les matchs de l'équipe
    team_matches = df[
        ((df['HomeTeam'].str.lower() == team_name.lower()) |
         (df['AwayTeam'].str.lower() == team_name.lower())) &
        (df['FTHG'].notna())
    ].sort_values('Date', ascending=False).head(num_matches)

    if len(team_matches) == 0:
        return None

    wins = 0
    draws = 0
    losses = 0
    goals_for = 0
    goals_against = 0
    form = []
    matches = []

    for _, match in team_matches.iterrows():
        is_home = match['HomeTeam'].lower() == team_name.lower()
        gf = int(match['FTHG']) if is_home else int(match['FTAG'])
        ga = int(match['FTAG']) if is_home else int(match['FTHG'])
        result = match['FTR']

        goals_for += gf
        goals_against += ga

        # Déterminer le résultat du point de vue de l'équipe
        if (is_home and result == 'H') or (not is_home and result == 'A'):
            wins += 1
            form.append('V')
            outcome = 'Victoire'
        elif result == 'D':
            draws += 1
            form.append('N')
            outcome = 'Nul'
        else:
            losses += 1
            form.append('D')
            outcome = 'Défaite'

        matches.append({
            "date": match['Date'].strftime('%Y-%m-%d'),
            "opponent": match['AwayTeam'] if is_home else match['HomeTeam'],
            "venue": "Domicile" if is_home else "Extérieur",
            "score": f"{gf}-{ga}",
            "result": outcome
        })

    return {
        "matches": matches,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "form_string": "-".join(form),
        "points": wins * 3 + draws
    }


def get_head_to_head(home_team: str, away_team: str, league_code: str, num_matches: int = 5) -> Dict[str, Any]:
    """
    Récupère l'historique des confrontations directes
    """
    season = "2526"
    filepath = f"data/{league_code}_{season}.csv"

    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')

    # Matchs entre les deux équipes
    h2h_matches = df[
        (((df['HomeTeam'].str.lower() == home_team.lower()) & (df['AwayTeam'].str.lower() == away_team.lower())) |
         ((df['HomeTeam'].str.lower() == away_team.lower()) & (df['AwayTeam'].str.lower() == home_team.lower()))) &
        (df['FTHG'].notna())
    ].sort_values('Date', ascending=False).head(num_matches)

    if len(h2h_matches) == 0:
        return {"matches": [], "home_wins": 0, "draws": 0, "away_wins": 0}

    home_wins = 0
    draws = 0
    away_wins = 0
    matches = []

    for _, match in h2h_matches.iterrows():
        is_same_order = match['HomeTeam'].lower() == home_team.lower()

        if match['FTR'] == 'H':
            if is_same_order:
                home_wins += 1
            else:
                away_wins += 1
        elif match['FTR'] == 'D':
            draws += 1
        else:
            if is_same_order:
                away_wins += 1
            else:
                home_wins += 1

        matches.append({
            "date": match['Date'].strftime('%Y-%m-%d'),
            "home": match['HomeTeam'],
            "away": match['AwayTeam'],
            "score": f"{int(match['FTHG'])}-{int(match['FTAG'])}"
        })

    return {
        "matches": matches,
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins
    }


def get_team_news(team_name: str, max_results: int = 5) -> list:
    """
    Récupère les actualités d'une équipe via GNews
    """
    try:
        google_news = GNews(language='fr', country='FR', max_results=max_results, period='7d')
        news = google_news.get_news(f"{team_name} football")

        articles = []
        for article in news:
            articles.append({
                "title": article.get('title'),
                "description": article.get('description'),
                "date": article.get('published date')
            })

        return articles
    except:
        return []


def generate_prematch_analysis(
    home_team: str,
    away_team: str,
    league_code: str,
    match_date: str,
    openai_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Génère une analyse pré-match complète avec IA

    Args:
        home_team: Nom équipe domicile
        away_team: Nom équipe extérieur
        league_code: Code championnat (E0, SP1, etc.)
        match_date: Date du match (YYYY-MM-DD)
        openai_api_key: Clé API OpenAI (ou None pour version sans IA)

    Returns:
        Dictionnaire avec analyse complète
    """

    print(f"[GENERATION] Analyse pré-match {home_team} vs {away_team}")

    # 1. Collecter les données
    print("  [1/4] Récupération forme récente...")
    home_form = get_team_recent_form(home_team, league_code)
    away_form = get_team_recent_form(away_team, league_code)

    print("  [2/4] Récupération H2H...")
    h2h = get_head_to_head(home_team, away_team, league_code)

    print("  [3/4] Récupération actualités...")
    home_news = get_team_news(home_team, max_results=3)
    away_news = get_team_news(away_team, max_results=3)

    # 2. Construire le contexte pour l'IA
    home_form_text = ""
    if home_form:
        home_form_text = f"""
{home_team} (5 derniers matchs):
- Bilan: {home_form['wins']}V - {home_form['draws']}N - {home_form['losses']}D
- Forme: {home_form['form_string']}
- Buts: {home_form['goals_for']} marqués, {home_form['goals_against']} encaissés
- Points: {home_form['points']}/15"""
    else:
        home_form_text = f"{home_team}: Données de forme non disponibles"

    away_form_text = ""
    if away_form:
        away_form_text = f"""
{away_team} (5 derniers matchs):
- Bilan: {away_form['wins']}V - {away_form['draws']}N - {away_form['losses']}D
- Forme: {away_form['form_string']}
- Buts: {away_form['goals_for']} marqués, {away_form['goals_against']} encaissés
- Points: {away_form['points']}/15"""
    else:
        away_form_text = f"{away_team}: Données de forme non disponibles"

    context = f"""
Vous êtes un analyste football professionnel. Générez une analyse pré-match détaillée.

MATCH: {home_team} vs {away_team}
DATE: {match_date}

=== FORME RÉCENTE ===
{home_form_text}
{away_form_text}

=== CONFRONTATIONS DIRECTES ===

{"Historique (5 derniers):" if h2h and h2h['matches'] else "Pas de confrontations directes récentes dans les données"}
{f"- Victoires {home_team}: {h2h['home_wins']}" if h2h and h2h['matches'] else ""}
{f"- Nuls: {h2h['draws']}" if h2h and h2h['matches'] else ""}
{f"- Victoires {away_team}: {h2h['away_wins']}" if h2h and h2h['matches'] else ""}

{f"Derniers matchs:{chr(10)}" + chr(10).join([f"- {m['date']}: {m['home']} {m['score']} {m['away']}" for m in h2h['matches'][:3]]) if h2h and h2h['matches'] else ""}

=== ACTUALITÉS ===

{home_team}:
{chr(10).join([f"- {a['title']}" for a in home_news[:3]])}

{away_team}:
{chr(10).join([f"- {a['title']}" for a in away_news[:3]])}

=== DEMANDE ===

Rédigez une analyse pré-match structurée avec:

1. **Les enjeux du match** (motivation, classement, contexte)
2. **Analyse de forme** (derniers résultats, tendances)
3. **Confrontations directes** (statistiques H2H)
4. **Joueurs clés et absents** (si mentionnés dans les news)
5. **Pronostic** (quel résultat probable et pourquoi)

Style: Professionnel, concis, basé sur les données. Comme FlashScore.
"""

    # 3. Générer l'analyse avec IA (si disponible)
    print("  [4/4] Génération analyse IA...")

    if openai_api_key and OPENAI_AVAILABLE:
        try:
            # Vérifier si c'est DeepInfra ou OpenAI
            is_deepinfra = len(openai_api_key) < 60  # Clé DeepInfra plus courte

            if is_deepinfra:
                # Configuration pour DeepInfra
                client = OpenAI(
                    api_key=openai_api_key,
                    base_url="https://api.deepinfra.com/v1/openai"
                )
                model = "deepseek-ai/DeepSeek-V3"  # Modèle DeepSeek-V3.2
                print("    [INFO] Utilisation de DeepInfra (DeepSeek-V3)")
            else:
                # Configuration OpenAI classique
                client = OpenAI(api_key=openai_api_key)
                model = "gpt-3.5-turbo"
                print("    [INFO] Utilisation de OpenAI (GPT-3.5)")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Vous êtes un analyste football professionnel. Rédigez des analyses pré-match détaillées et factuelles basées sur les statistiques fournies."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=1200
            )

            ai_analysis = response.choices[0].message.content
            print(f"    [SUCCESS] Analyse générée ({len(ai_analysis)} caractères)")

        except Exception as e:
            print(f"    [ERREUR IA] {e}")
            ai_analysis = f"Erreur lors de la génération: {str(e)}\n\nConsultez les données brutes ci-dessous."
    else:
        ai_analysis = "Analyse IA non configurée (ajoutez votre clé DeepInfra ou OpenAI)."

    # 4. Retourner le résultat
    return {
        "home_team": home_team,
        "away_team": away_team,
        "match_date": match_date,
        "ai_analysis": ai_analysis,
        "data": {
            "home_form": home_form,
            "away_form": away_form,
            "head_to_head": h2h,
            "home_news": home_news,
            "away_news": away_news
        },
        "prompt_context": context  # Pour debug
    }


if __name__ == "__main__":
    # TEST
    from dotenv import load_dotenv
    load_dotenv()  # Charger les variables depuis .env

    # Essayer DeepInfra en premier, puis OpenAI
    api_key = os.getenv("DEEPINFRA_API_KEY") or os.getenv("OPENAI_API_KEY")

    result = generate_prematch_analysis(
        home_team="Liverpool",
        away_team="Newcastle",
        league_code="E0",
        match_date="2026-01-31",
        openai_api_key=api_key
    )

    print("\n" + "="*70)
    print("ANALYSE GÉNÉRÉE PAR IA")
    print("="*70)
    print(result['ai_analysis'])
    print("\n" + "="*70)

    # Sauvegarder
    import json
    with open("match_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n[SAVED] match_analysis.json")
