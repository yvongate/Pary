/**
 * GeneratePredictionModal - Formulaire de génération manuelle de prédictions
 */
'use client';

import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface GeneratePredictionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (predictionId: number, homeTeam: string, awayTeam: string) => void;
  initialHomeTeam?: string;
  initialAwayTeam?: string;
}

export default function GeneratePredictionModal({
  isOpen,
  onClose,
  onSuccess,
  initialHomeTeam,
  initialAwayTeam
}: GeneratePredictionModalProps) {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [homeFormation, setHomeFormation] = useState('');
  const [awayFormation, setAwayFormation] = useState('');
  const [homePlayers, setHomePlayers] = useState('');
  const [awayPlayers, setAwayPlayers] = useState('');
  const [bookmakerProps, setBookmakerProps] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pré-remplir les équipes quand le modal s'ouvre avec des valeurs initiales
  useEffect(() => {
    if (isOpen) {
      // Debug : vérifier les valeurs reçues
      console.log('Modal ouvert avec:', { initialHomeTeam, initialAwayTeam });

      // Pré-remplir avec les valeurs initiales (ou vide si pas de valeurs)
      setHomeTeam(initialHomeTeam || '');
      setAwayTeam(initialAwayTeam || '');
      // Réinitialiser les autres champs
      setHomeFormation('');
      setAwayFormation('');
      setHomePlayers('');
      setAwayPlayers('');
      setBookmakerProps('');
      setError(null);
    }
  }, [isOpen, initialHomeTeam, initialAwayTeam]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validation
      if (!homeTeam || !awayTeam) {
        throw new Error('Les noms des équipes sont obligatoires');
      }

      if (!homeFormation || !awayFormation) {
        throw new Error('Les formations sont obligatoires');
      }

      // Valider format formations (regex)
      const formationPattern = /^\d(-\d){1,3}$/;
      if (!formationPattern.test(homeFormation)) {
        throw new Error(`Formation domicile invalide. Format attendu: 4-3-3 ou 4-2-3-1`);
      }
      if (!formationPattern.test(awayFormation)) {
        throw new Error(`Formation extérieur invalide. Format attendu: 4-3-3 ou 4-2-3-1`);
      }

      // Lancer la génération
      const response = await fetch(`${API_BASE_URL}/api/generate-prediction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          home_team: homeTeam.trim(),
          away_team: awayTeam.trim(),
          home_formation: homeFormation.trim(),
          away_formation: awayFormation.trim(),
          home_players: homePlayers.trim() || null,
          away_players: awayPlayers.trim() || null,
          bookmaker_props_text: bookmakerProps.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la génération');
      }

      const data = await response.json();

      // Succès - Fermer le modal et notifier (passer les noms d'équipes)
      onSuccess(data.prediction_id, homeTeam.trim(), awayTeam.trim());

      // Réinitialiser le formulaire
      setHomeTeam('');
      setAwayTeam('');
      setHomeFormation('');
      setAwayFormation('');
      setHomePlayers('');
      setAwayPlayers('');
      setBookmakerProps('');

    } catch (err: any) {
      setError(err.message || 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 rounded-t-lg">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">📊 Générer une prédiction</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl font-bold"
              disabled={loading}
            >
              ×
            </button>
          </div>
          <p className="text-sm mt-2 text-blue-100">
            Renseignez les formations pour générer une prédiction IA
          </p>
        </div>

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="p-6">
          {/* Erreur */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Équipe Domicile */}
          <div className="mb-6 bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">
            <h3 className="font-bold text-blue-900 mb-4 flex items-center">
              🏠 ÉQUIPE DOMICILE
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de l'équipe *
                </label>
                <input
                  type="text"
                  value={homeTeam}
                  onChange={(e) => setHomeTeam(e.target.value)}
                  placeholder="Ex: Villarreal"
                  required
                  disabled={loading}
                  readOnly={!!initialHomeTeam}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 ${initialHomeTeam ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Formation *
                  <span className="text-xs text-gray-500 ml-2">(Format: X-X-X ou X-X-X-X)</span>
                </label>
                <input
                  type="text"
                  value={homeFormation}
                  onChange={(e) => setHomeFormation(e.target.value)}
                  placeholder="Ex: 4-3-3"
                  pattern="\d(-\d){1,3}"
                  title="Format: 4-3-3 ou 4-2-3-1"
                  required
                  disabled={loading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Joueurs (optionnel)
                  <span className="text-xs text-gray-500 ml-2">(Séparés par des virgules)</span>
                </label>
                <input
                  type="text"
                  value={homePlayers}
                  onChange={(e) => setHomePlayers(e.target.value)}
                  placeholder="Ex: Navas, Foyth, Albiol, Pedraza, Parejo, Capoue..."
                  disabled={loading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                />
              </div>
            </div>
          </div>

          {/* Équipe Extérieur */}
          <div className="mb-6 bg-red-50 rounded-lg p-4 border-l-4 border-red-500">
            <h3 className="font-bold text-red-900 mb-4 flex items-center">
              ✈️ ÉQUIPE EXTÉRIEUR
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de l'équipe *
                </label>
                <input
                  type="text"
                  value={awayTeam}
                  onChange={(e) => setAwayTeam(e.target.value)}
                  placeholder="Ex: Elche"
                  required
                  disabled={loading}
                  readOnly={!!initialAwayTeam}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500 text-gray-900 ${initialAwayTeam ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Formation *
                  <span className="text-xs text-gray-500 ml-2">(Format: X-X-X ou X-X-X-X)</span>
                </label>
                <input
                  type="text"
                  value={awayFormation}
                  onChange={(e) => setAwayFormation(e.target.value)}
                  placeholder="Ex: 4-2-3-1"
                  pattern="\d(-\d){1,3}"
                  title="Format: 4-3-3 ou 4-2-3-1"
                  required
                  disabled={loading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500 text-gray-900 bg-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Joueurs (optionnel)
                  <span className="text-xs text-gray-500 ml-2">(Séparés par des virgules)</span>
                </label>
                <input
                  type="text"
                  value={awayPlayers}
                  onChange={(e) => setAwayPlayers(e.target.value)}
                  placeholder="Ex: Edgar, Bigas, Gonzalez, Lirola, Guti..."
                  disabled={loading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500 text-gray-900 bg-white"
                />
              </div>
            </div>
          </div>

          {/* Propositions Bookmaker */}
          <div className="mb-6 bg-purple-50 rounded-lg p-4 border-l-4 border-purple-500">
            <h3 className="font-bold text-purple-900 mb-2 flex items-center">
              🎯 PROPOSITIONS BOOKMAKER (optionnel)
            </h3>
            <p className="text-xs text-gray-600 mb-3">
              L'IA analysera les cotes pour détecter les meilleures opportunités de value betting
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lignes et cotes
                <span className="text-xs text-gray-500 ml-2">(Format libre)</span>
              </label>
              <textarea
                value={bookmakerProps}
                onChange={(e) => setBookmakerProps(e.target.value)}
                placeholder={`Exemples de propositions bookmaker:

TOTAL TIRS/CORNERS:
+24.5 tirs cote 1.85
-24.5 tirs cote 2.10
+10.5 corners cote 1.95
-10.5 corners cote 1.90

HANDICAPS TIRS:
PSG handicap tirs -5.5 cote 1.90
Nantes handicap tirs +5.5 cote 1.95

HANDICAPS CORNERS:
Liverpool handicap corners -2.5 cote 2.00
Everton handicap corners +2.5 cote 1.85

Format court: +24.5t 1.85 ou PSG -5.5t @ 1.90`}
                disabled={loading}
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 font-mono text-sm text-gray-900 bg-white"
              />
              <p className="mt-1 text-xs text-gray-500">
                💡 Total: "+24.5 tirs @ 1.85" | Handicap: "PSG handicap tirs -5.5 @ 1.90"
              </p>
            </div>
          </div>

          {/* Boutons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Génération en cours...
                </>
              ) : (
                <>
                  🚀 Générer la prédiction
                </>
              )}
            </button>
          </div>

          <p className="mt-4 text-xs text-gray-500 text-center">
            * Champs obligatoires
          </p>
        </form>
      </div>
    </div>
  );
}
