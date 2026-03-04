'use client';

/**
 * Page Prédictions - Liste des prédictions à venir
 */
import React, { useState, useEffect } from 'react';
import { getUpcomingPredictions, getLeagues, Prediction, League } from '../../lib/api';
import PredictionCard from '../../components/PredictionCard';
import PredictionModal from '../../components/PredictionModal';

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // État du modal
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedMatchId, setSelectedMatchId] = useState<string>('');

  // Charger les championnats
  useEffect(() => {
    async function loadLeagues() {
      try {
        const data = await getLeagues();
        setLeagues(data);
      } catch (err) {
        console.error('Erreur chargement ligues:', err);
      }
    }
    loadLeagues();
  }, []);

  // Charger les prédictions
  useEffect(() => {
    async function loadPredictions() {
      setLoading(true);
      setError(null);
      try {
        const data = await getUpcomingPredictions(selectedLeague || undefined, 50);
        setPredictions(data.predictions);
      } catch (err) {
        setError('Impossible de charger les prédictions. Vérifiez que le backend est démarré.');
        console.error('Erreur:', err);
      } finally {
        setLoading(false);
      }
    }
    loadPredictions();
  }, [selectedLeague]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            ⚽ Prédictions Football
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Prédictions automatiques de tirs et corners basées sur l'IA
          </p>
        </div>
      </div>

      {/* Filtres */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center gap-4">
            <label htmlFor="league" className="text-sm font-medium text-gray-700">
              Championnat:
            </label>
            <select
              id="league"
              value={selectedLeague}
              onChange={(e) => setSelectedLeague(e.target.value)}
              className="block w-64 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">Tous les championnats</option>
              {leagues.map((league) => (
                <option key={league.code} value={league.code}>
                  {league.name} ({league.country})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Contenu */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Chargement des prédictions...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <p className="text-sm text-red-600 mt-2">
              Assurez-vous que le backend est démarré sur http://localhost:8000
            </p>
          </div>
        )}

        {!loading && !error && predictions.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 font-medium">
              Aucune prédiction disponible pour le moment
            </p>
            <p className="text-sm text-yellow-600 mt-2">
              Les prédictions sont générées automatiquement chaque jour à 10:00 pour les matchs des prochaines 48h
            </p>
          </div>
        )}

        {!loading && !error && predictions.length > 0 && (
          <div>
            <div className="mb-4 text-sm text-gray-600">
              {predictions.length} prédiction(s) trouvée(s)
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {predictions.map((prediction) => (
                <PredictionCard
                  key={prediction.match_id}
                  prediction={prediction}
                  onClick={() => {
                    setSelectedMatchId(prediction.match_id);
                    setModalOpen(true);
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modal de détail */}
      <PredictionModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        matchId={selectedMatchId}
      />
    </div>
  );
}
