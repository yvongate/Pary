'use client';

/**
 * Page Historique des Prédictions
 * Affiche toutes les prédictions passées et futures
 */
import React, { useState, useEffect } from 'react';
import { getAllPredictions, getLeagues, Prediction, League } from '../../../lib/api';
import PredictionCard from '../../../components/PredictionCard';
import PredictionModal from '../../../components/PredictionModal';
import Link from 'next/link';

export default function HistoryPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [includePast, setIncludePast] = useState<boolean>(true);
  const [limit, setLimit] = useState<number>(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // État du modal de détail
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

  // Fonction pour charger les prédictions
  const loadPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllPredictions(
        selectedLeague || undefined,
        limit,
        includePast
      );
      setPredictions(data.predictions);
    } catch (err) {
      setError('Impossible de charger les prédictions. Vérifiez que le backend est démarré.');
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  // Charger les prédictions au montage et quand les filtres changent
  useEffect(() => {
    loadPredictions();
  }, [selectedLeague, limit, includePast]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                📊 Historique des Prédictions
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                Consultez toutes les prédictions générées (passées et futures)
              </p>
            </div>
            <Link
              href="/predictions"
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-semibold shadow-md"
            >
              ← Retour aux prédictions
            </Link>
          </div>
        </div>
      </div>

      {/* Filtres */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Filtre championnat */}
            <div className="flex items-center gap-4">
              <label htmlFor="league" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Championnat:
              </label>
              <select
                id="league"
                value={selectedLeague}
                onChange={(e) => setSelectedLeague(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tous les championnats</option>
                {leagues.map((league) => (
                  <option key={league.code} value={league.code}>
                    {league.name} ({league.country})
                  </option>
                ))}
              </select>
            </div>

            {/* Filtre limite */}
            <div className="flex items-center gap-4">
              <label htmlFor="limit" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                Nombre:
              </label>
              <select
                id="limit"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="20">20 dernières</option>
                <option value="50">50 dernières</option>
                <option value="100">100 dernières</option>
                <option value="200">200 dernières (max)</option>
              </select>
            </div>

            {/* Toggle prédictions passées */}
            <div className="flex items-center gap-4">
              <label htmlFor="includePast" className="text-sm font-medium text-gray-700">
                <input
                  id="includePast"
                  type="checkbox"
                  checked={includePast}
                  onChange={(e) => setIncludePast(e.target.checked)}
                  className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Inclure prédictions passées
              </label>
            </div>
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
              Assurez-vous que le backend est démarré et accessible
            </p>
          </div>
        )}

        {!loading && !error && predictions.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 font-medium">
              Aucune prédiction trouvée avec ces filtres
            </p>
            <p className="text-sm text-yellow-600 mt-2">
              Essayez de modifier vos filtres ou de générer de nouvelles prédictions
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
