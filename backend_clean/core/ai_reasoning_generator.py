"""
Gnrateur de Raisonnement IA - Utilise DeepInfra pour gnrer des analyses textuelles

Gnre 2 textes spars:
- Un pour les TIRS
- Un pour les CORNERS
"""

import os
from typing import Dict
import requests
from dotenv import load_dotenv

load_dotenv()


class AIReasoningGenerator:
    """
    Gnre des analyses textuelles avec DeepInfra (gratuit)
    """

    def __init__(self):
        """Initialise le gnrateur IA"""
        self.api_key = os.getenv("DEEPINFRA_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.model = "meta-llama/Meta-Llama-3-70B-Instruct"

    def generate_shots_reasoning(self, analysis_data: Dict) -> str:
        """
        Gnre le texte d'analyse pour les TIRS

        Args:
            analysis_data: {
                'match': {...},
                'shots_analysis': {...},
                'predictions': {...},
                'metadata': {...}
            }

        Returns:
            Texte d'analyse humaine pour les tirs
        """
        match = analysis_data['match']
        shots = analysis_data['shots_analysis']
        pred = analysis_data['predictions']['shots']
        metadata = analysis_data.get('metadata', {})

        # Ajouter contexte Rue des Joueurs si disponible
        rdj_context = ""
        if metadata.get('ruedesjoueurs_used') and metadata.get('ruedesjoueurs_context'):
            rdj_info = metadata['ruedesjoueurs_context']
            injuries = rdj_info.get('injuries', '')
            if injuries and injuries != 'Aucune info':
                rdj_context = f"\n\nJOUEURS ABSENTS / BLESSS:\n{injuries}\n"

        # Construire le prompt avec TOUTES les donnes match-par-match
        prompt = f"""Tu es un analyste football expert. Analyse ce match en DTAIL pour prdire les TIRS.

MATCH: {match['home_team']} vs {match['away_team']}
{rdj_context}
ANALYSE DTAILLE DOMICILE ({match['home_team']}):
{shots['home_team_analysis']['conclusion']}

ANALYSE DTAILLE EXTRIEUR ({match['away_team']}):
{shots['away_team_analysis']['conclusion']}

PRDICTION FINALE: Entre {pred['min']} et {pred['max']} tirs au total (confiance {pred['confidence']:.0%})

CONSIGNE IMPORTANTE:
- Rdige une analyse DTAILLE de 15-20 phrases MINIMUM
- Style journalistique et professionnel
- UTILISE les comparaisons match-par-match fournies ci-dessus
- Pour CHAQUE quipe, mentionne plusieurs adversaires spcifiques et leurs rsultats
- Exemple: "Contre Arsenal ils ont fait 14 tirs, contre Liverpool 9 tirs, contre Chelsea 16 tirs..."
- Compare les performances contre diffrents types d'adversaires
- Identifie les PATTERNS et TENDANCES spcifiques
- Explique comment l'adversaire du jour se compare  ces matchs passs
- Si des joueurs cls sont absents/blesss, EXPLIQUE comment cela peut impacter les tirs
- NE te contente PAS de moyennes globales - dtaille les variations!
- Conclus avec la fourchette prdite et justification base sur les comparaisons

ANALYSE DTAILLE:"""

        return self._call_deepinfra(prompt)

    def generate_corners_reasoning(self, analysis_data: Dict) -> str:
        """
        Gnre le texte d'analyse pour les CORNERS

        Args:
            analysis_data: {
                'match': {...},
                'corners_analysis': {...},
                'predictions': {...},
                'metadata': {...}
            }

        Returns:
            Texte d'analyse humaine pour les corners
        """
        match = analysis_data['match']
        corners = analysis_data['corners_analysis']
        pred = analysis_data['predictions']['corners']
        metadata = analysis_data.get('metadata', {})

        # Ajouter contexte Rue des Joueurs si disponible
        rdj_context = ""
        if metadata.get('ruedesjoueurs_used') and metadata.get('ruedesjoueurs_context'):
            rdj_info = metadata['ruedesjoueurs_context']
            injuries = rdj_info.get('injuries', '')
            if injuries and injuries != 'Aucune info':
                rdj_context = f"\n\nJOUEURS ABSENTS / BLESSS:\n{injuries}\n"

        # Construire le prompt avec TOUTES les donnes match-par-match
        prompt = f"""Tu es un analyste football expert. Analyse ce match en DTAIL pour prdire les CORNERS.

MATCH: {match['home_team']} vs {match['away_team']}
{rdj_context}
ANALYSE DTAILLE DOMICILE ({match['home_team']}):
{corners['home_team_analysis']['conclusion']}

ANALYSE DTAILLE EXTRIEUR ({match['away_team']}):
{corners['away_team_analysis']['conclusion']}

PRDICTION FINALE: Entre {pred['min']} et {pred['max']} corners au total (confiance {pred['confidence']:.0%})

CONSIGNE IMPORTANTE:
- Rdige une analyse DTAILLE de 15-20 phrases MINIMUM
- Style journalistique et professionnel
- UTILISE les comparaisons match-par-match fournies ci-dessus
- Pour CHAQUE quipe, mentionne plusieurs adversaires spcifiques et leurs rsultats
- Exemple: "Contre Arsenal ils ont obtenu 7 corners, contre Liverpool 4 corners, contre Chelsea 9 corners..."
- Compare les performances contre diffrents types d'adversaires
- Identifie les PATTERNS et TENDANCES spcifiques
- Explique comment l'adversaire du jour se compare  ces matchs passs
- Mentionne le style de jeu observ dans ces matchs (centres, ailiers, jeu latral)
- Si des joueurs cls sont absents/blesss, EXPLIQUE comment cela peut impacter les corners
- NE te contente PAS de moyennes globales - dtaille les variations!
- Conclus avec la fourchette prdite et justification base sur les comparaisons

ANALYSE DTAILLE:"""

        return self._call_deepinfra(prompt)

    def _call_deepinfra(self, prompt: str) -> str:
        """
        Appelle l'API DeepInfra

        Args:
            prompt: Prompt  envoyer

        Returns:
            Rponse gnre
        """
        if not self.api_key:
            return "API key non configure. Veuillez dfinir DEEPINFRA_API_KEY dans .env"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Tu es un analyste football expert. Tes analyses sont TRES DETAILLEES, bases sur des comparaisons match-par-match spcifiques, et professionnelles. Tu ne te contentes JAMAIS de moyennes globales."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2500,
                "temperature": 0.7
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f" Erreur DeepInfra: {response.status_code}")
                return f"Erreur gnration IA: {response.status_code}"

        except Exception as e:
            print(f" Erreur DeepInfra: {e}")
            return f"Erreur gnration IA: {str(e)}"


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    generator = AIReasoningGenerator()

    # Donnes d'exemple
    test_data = {
        'match': {
            'home_team': 'Tottenham',
            'away_team': 'Arsenal',
            'league': 'england'
        },
        'shots_analysis': {
            'home_team_analysis': {
                'conclusion': 'Tottenham  domicile devrait tenter environ 11.3 tirs. Cette prdiction est base sur 150 matchs avec une confiance de 87%.'
            },
            'away_team_analysis': {
                'conclusion': 'Arsenal  l\'extrieur devrait tenter environ 7.8 tirs. Cette prdiction est base sur 148 matchs avec une confiance de 82%.'
            }
        },
        'corners_analysis': {
            'home_team_analysis': {
                'conclusion': 'Tottenham  domicile devrait obtenir environ 5.3 corners. Cette prdiction est base sur 150 matchs avec une confiance de 79%.'
            },
            'away_team_analysis': {
                'conclusion': 'Arsenal  l\'extrieur devrait obtenir environ 4.1 corners. Cette prdiction est base sur 148 matchs avec une confiance de 75%.'
            }
        },
        'predictions': {
            'shots': {'min': 16, 'max': 22, 'confidence': 0.85},
            'corners': {'min': 8, 'max': 11, 'confidence': 0.77}
        },
        'metadata': {}
    }

    print("=" * 70)
    print("TEST GNRATION IA")
    print("=" * 70)

    print("\n Gnration analyse TIRS...")
    shots_text = generator.generate_shots_reasoning(test_data)
    print("\nRsultat:")
    print(shots_text)

    print("\n" + "=" * 70)

    print("\n Gnration analyse CORNERS...")
    corners_text = generator.generate_corners_reasoning(test_data)
    print("\nRsultat:")
    print(corners_text)

    print("\n" + "=" * 70)
