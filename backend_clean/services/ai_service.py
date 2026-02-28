"""
Service IA - Génération de texte avec DeepInfra
Génère les analyses textuelles pour tirs et corners
"""
import requests
from typing import Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings


class AIService:
    """Service de génération de texte IA"""

    def __init__(self):
        self.api_key = settings.DEEPINFRA_API_KEY or settings.OPENAI_API_KEY
        self.base_url = settings.AI_BASE_URL
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE

    def generate_shots_reasoning(self, analysis_data: Dict) -> str:
        """
        Génère le texte d'analyse pour les TIRS

        Args:
            analysis_data: {
                'match': {...},
                'shots_analysis': {...},
                'predictions': {...}
            }

        Returns:
            Texte d'analyse humaine pour les tirs
        """
        match = analysis_data['match']
        shots = analysis_data['shots_analysis']
        pred = analysis_data['predictions']['shots']

        prompt = f"""Tu es un analyste football expert. Analyse ce match pour prédire les TIRS.

MATCH: {match['home_team']} vs {match['away_team']}

ANALYSE DOMICILE ({match['home_team']}):
{shots['home_team_analysis']['conclusion']}

ANALYSE EXTÉRIEUR ({match['away_team']}):
{shots['away_team_analysis']['conclusion']}

PRÉDICTION: Entre {pred['min']} et {pred['max']} tirs au total (confiance {pred['confidence']:.0%})

CONSIGNE:
- Rédige une analyse de 3-4 phrases MAXIMUM
- Style journalistique, professionnel
- Explique POURQUOI cette prédiction de tirs
- Mentionne les forces/faiblesses de chaque équipe
- Conclus avec la fourchette prédite

ANALYSE:"""

        return self._call_ai(prompt)

    def generate_corners_reasoning(self, analysis_data: Dict) -> str:
        """
        Génère le texte d'analyse pour les CORNERS

        Args:
            analysis_data: {
                'match': {...},
                'corners_analysis': {...},
                'predictions': {...}
            }

        Returns:
            Texte d'analyse humaine pour les corners
        """
        match = analysis_data['match']
        corners = analysis_data['corners_analysis']
        pred = analysis_data['predictions']['corners']

        prompt = f"""Tu es un analyste football expert. Analyse ce match pour prédire les CORNERS.

MATCH: {match['home_team']} vs {match['away_team']}

ANALYSE DOMICILE ({match['home_team']}):
{corners['home_team_analysis']['conclusion']}

ANALYSE EXTÉRIEUR ({match['away_team']}):
{corners['away_team_analysis']['conclusion']}

PRÉDICTION: Entre {pred['min']} et {pred['max']} corners au total (confiance {pred['confidence']:.0%})

CONSIGNE:
- Rédige une analyse de 3-4 phrases MAXIMUM
- Style journalistique, professionnel
- Explique POURQUOI cette prédiction de corners
- Mentionne le style de jeu (centres, ailiers, etc.)
- Conclus avec la fourchette prédite

ANALYSE:"""

        return self._call_ai(prompt)

    def _call_ai(self, prompt: str) -> str:
        """
        Appelle l'API DeepInfra

        Args:
            prompt: Prompt à envoyer

        Returns:
            Réponse générée
        """
        if not self.api_key:
            return "API key non configurée. Veuillez définir DEEPINFRA_API_KEY dans .env"

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
                        "content": "Tu es un analyste football expert. Tes analyses sont concises, précises et professionnelles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"[ERREUR IA] {response.status_code}")
                return f"Erreur génération IA: {response.status_code}"

        except Exception as e:
            print(f"[ERREUR IA] {e}")
            return f"Erreur génération IA: {str(e)}"


# Instance globale
_ai_instance = None

def get_ai_service() -> AIService:
    """Retourne l'instance singleton du service IA"""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIService()
    return _ai_instance
