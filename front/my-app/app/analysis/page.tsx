'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Prediction {
  big_team: string;
  projected_shots: number;
  confidence: string;
  historical_shots: number[];
  recommendation: string;
}

interface BottomTeam {
  name: string;
  points: number;
  total_matches: number;
  avg_shots: number;
  percentage_under_10: number;
  percentage_under_8_5: number;
  predictions: Prediction[];
  reliability: string;
}

interface BigTeam {
  name: string;
  total_matches: number;
  avg_opponent_shots: number;
  percentage_under_10: number;
  reliability: string;
}

interface LeagueAnalysis {
  name: string;
  country: string;
  emoji: string;
  stats: {
    total_matches: number;
    percentage_under_10: number;
    avg_shots: number;
  };
  big_teams: BigTeam[];
  bottom_5: BottomTeam[];
}

interface Analysis {
  last_updated: string;
  global_stats: {
    total_matches: number;
    percentage_under_10: number;
    average_shots: number;
  };
  leagues: { [key: string]: LeagueAnalysis };
}

export default function AnalysisPage() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string>('E0');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/analysis/low-shots');
      const data = await response.json();

      if (data.error) {
        setError(data.message || data.error);
      } else {
        setAnalysis(data);
      }
    } catch (err) {
      setError('Erreur lors du chargement de l\'analyse');
    } finally {
      setLoading(false);
    }
  };

  const getReliabilityBadge = (reliability: string) => {
    const badges = {
      excellent: { text: '🔥 PARFAIT', color: 'bg-green-500' },
      very_good: { text: '✅ TRÈS FIABLE', color: 'bg-green-600' },
      good: { text: '⚠️ FIABLE', color: 'bg-yellow-600' },
      average: { text: '⚠️ MOYEN', color: 'bg-orange-600' },
      risky: { text: '❌ RISQUÉ', color: 'bg-red-600' }
    };
    return badges[reliability as keyof typeof badges] || badges.risky;
  };

  const getConfidenceBadge = (confidence: string) => {
    const badges = {
      high: { text: 'Haute confiance', color: 'text-green-400' },
      medium: { text: 'Moyenne', color: 'text-yellow-400' },
      low: { text: 'Projection', color: 'text-gray-400' }
    };
    return badges[confidence as keyof typeof badges] || badges.low;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-center">
            <p className="text-red-400">{error || 'Impossible de charger l\'analyse'}</p>
            <button
              onClick={loadAnalysis}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition"
            >
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentLeague = analysis.leagues[selectedLeague];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold mb-2">📊 Analyse des Tirs Faibles</h1>
              <p className="text-gray-400">
                Identifiez les équipes qui tirent peu contre les grands clubs
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={loadAnalysis}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
              >
                🔄 Rafraîchir
              </button>
              <Link
                href="/"
                className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition"
              >
                ← Retour
              </Link>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            Dernière mise à jour: {analysis.last_updated}
          </p>
        </div>

        {/* Global Stats */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">📈 Résumé Global - 7 Championnats</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-purple-200">Total matchs analysés</p>
              <p className="text-3xl font-bold">{analysis.global_stats.total_matches}</p>
            </div>
            <div>
              <p className="text-sm text-purple-200">Faibles ≤10 tirs</p>
              <p className="text-3xl font-bold">{analysis.global_stats.percentage_under_10}%</p>
            </div>
            <div>
              <p className="text-sm text-purple-200">Moyenne tirs</p>
              <p className="text-3xl font-bold">{analysis.global_stats.average_shots}</p>
            </div>
          </div>
        </div>

        {/* League Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
          {Object.entries(analysis.leagues).map(([code, league]) => (
            <button
              key={code}
              onClick={() => setSelectedLeague(code)}
              className={`flex-shrink-0 px-4 py-2 rounded-lg transition whitespace-nowrap ${
                selectedLeague === code
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {league.emoji} {league.name}
            </button>
          ))}
        </div>

        {/* League Content */}
        {currentLeague && (
          <div className="space-y-6">
            {/* League Stats */}
            <div className="bg-gray-900 rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">
                {currentLeague.emoji} {currentLeague.name} - Statistiques
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Total matchs</p>
                  <p className="text-2xl font-bold">{currentLeague.stats.total_matches}</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Faibles ≤10 tirs</p>
                  <p className="text-2xl font-bold text-green-400">
                    {currentLeague.stats.percentage_under_10}%
                  </p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Moyenne tirs</p>
                  <p className="text-2xl font-bold">{currentLeague.stats.avg_shots}</p>
                </div>
              </div>
            </div>

            {/* Big Teams */}
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 bg-gray-800 border-b border-gray-700">
                <h3 className="text-lg font-bold">⭐ Grands Clubs Fiables</h3>
                <p className="text-sm text-gray-400">Empêchent les faibles de tirer</p>
              </div>
              <div className="p-4 space-y-3">
                {currentLeague.big_teams.map((team, idx) => {
                  const badge = getReliabilityBadge(team.reliability);
                  return (
                    <div key={idx} className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-lg">{team.name}</span>
                        <span className={`${badge.color} px-3 py-1 rounded text-xs font-bold`}>
                          {badge.text}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <p className="text-gray-400">Fiabilité</p>
                          <p className="font-bold text-green-400">{team.percentage_under_10}%</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Moy tirs adverses</p>
                          <p className="font-bold">{team.avg_opponent_shots}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Matchs</p>
                          <p className="font-bold">{team.total_matches}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Bottom 5 Teams */}
            <div className="bg-gray-900 rounded-xl overflow-hidden">
              <div className="p-4 bg-gray-800 border-b border-gray-700">
                <h3 className="text-lg font-bold">📉 Les 5 Derniers du Classement</h3>
                <p className="text-sm text-gray-400">Équipes sur lesquelles parier vs grands</p>
              </div>
              <div className="p-4 space-y-6">
                {currentLeague.bottom_5.map((team, idx) => {
                  const badge = getReliabilityBadge(team.reliability);
                  return (
                    <div key={idx} className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <span className="font-bold text-lg">{team.name}</span>
                          <span className="text-sm text-gray-400 ml-2">({team.points} pts)</span>
                        </div>
                        <span className={`${badge.color} px-3 py-1 rounded text-xs font-bold`}>
                          {badge.text}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                        <div className="bg-gray-900 rounded p-2">
                          <p className="text-gray-400">Moyenne globale</p>
                          <p className="font-bold">{team.avg_shots} tirs</p>
                        </div>
                        <div className="bg-gray-900 rounded p-2">
                          <p className="text-gray-400">≤8.5 tirs</p>
                          <p className="font-bold text-green-400">{team.percentage_under_8_5}%</p>
                        </div>
                      </div>

                      {/* Predictions */}
                      {team.predictions.length > 0 && (
                        <div className="border-t border-gray-700 pt-3">
                          <p className="text-sm font-semibold text-gray-300 mb-2">
                            🎯 Prédictions face aux grands (≤8.5 tirs uniquement):
                          </p>
                          <div className="space-y-2">
                            {team.predictions.map((pred, pidx) => {
                              const confBadge = getConfidenceBadge(pred.confidence);
                              return (
                                <div key={pidx} className="bg-gray-900 rounded p-3">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <span className="font-medium">vs {pred.big_team}</span>
                                      <span className="text-xs text-gray-400 ml-2">
                                        ({confBadge.text})
                                      </span>
                                    </div>
                                    <div className="text-right">
                                      <p className="font-bold text-blue-400">
                                        ~{pred.projected_shots} tirs
                                      </p>
                                      {pred.historical_shots.length > 0 && (
                                        <p className="text-xs text-gray-500">
                                          Historique: [{pred.historical_shots.join(', ')}]
                                        </p>
                                      )}
                                    </div>
                                  </div>
                                  {pred.recommendation === 'bet' && (
                                    <p className="text-xs text-green-400 mt-1">
                                      ✅ RECOMMANDÉ: Parier "{team.name} ≤8.5 tirs"
                                    </p>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {team.predictions.length === 0 && (
                        <p className="text-sm text-gray-500 italic">
                          Aucune prédiction favorable (équipe tire trop)
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
