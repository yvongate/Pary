"""
Service IA - Génération de texte avec Anthropic Claude
Génère les analyses textuelles pour tirs et corners
"""
import anthropic
from typing import Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings


class AIService:
    """Service de génération de texte IA avec Anthropic Claude"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE

        # Initialiser le client Anthropic
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            print("[WARNING] Clé API Anthropic non configurée")

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
        Appelle l'API Anthropic Claude

        Args:
            prompt: Prompt à envoyer

        Returns:
            Réponse générée
        """
        if not self.client:
            return "API key Anthropic non configurée. Veuillez définir ANTHROPIC_API_KEY dans .env"

        try:
            # Appel API Anthropic avec SDK officiel
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="Tu es un analyste football expert. Tes analyses sont concises, précises et professionnelles.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extraire le texte de la réponse
            return message.content[0].text.strip()

        except anthropic.APIConnectionError as e:
            print(f"[ERREUR IA] Connexion échouée: {e}")
            return "Erreur de connexion à l'API Anthropic. Vérifiez votre connexion internet."

        except anthropic.RateLimitError as e:
            print(f"[ERREUR IA] Limite de débit atteinte: {e}")
            return "Limite de débit API atteinte. Veuillez réessayer dans quelques instants."

        except anthropic.APIStatusError as e:
            print(f"[ERREUR IA] Erreur API ({e.status_code})")
            print(f"[DEBUG] Response: {e.response.text if hasattr(e.response, 'text') else e.response}")
            return f"Erreur API Anthropic: {e.status_code}"

        except Exception as e:
            print(f"[ERREUR IA] Erreur inattendue: {e}")
            return f"Erreur génération IA: {str(e)}"


# Instance globale
_ai_instance = None

def get_ai_service() -> AIService:
    """Retourne l'instance singleton du service IA"""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIService()
    return _ai_instance
