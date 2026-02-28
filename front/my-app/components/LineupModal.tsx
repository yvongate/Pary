'use client';

import { useState, useEffect } from 'react';
import { Fixture, LineupsResponse, getLineups, Player } from '@/lib/api';

interface LineupModalProps {
  match: Fixture;
  onClose: () => void;
}

export default function LineupModal({ match, onClose }: LineupModalProps) {
  const [lineups, setLineups] = useState<LineupsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLineups();
  }, [match]);

  const loadLineups = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLineups(match.home_team, match.away_team, match.date);
      setLineups(data);
    } catch (err) {
      console.error('Error loading lineups:', err);
      setError('Impossible de charger les compositions. Le match est peut-être trop récent ou les données ne sont pas disponibles.');
    } finally {
      setLoading(false);
    }
  };

  const renderPlayers = (players: Player[], isStarters: boolean) => {
    const filteredPlayers = players.filter(p => p.substitute !== isStarters);

    if (filteredPlayers.length === 0) return null;

    return (
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          {isStarters ? 'Titulaires' : 'Remplaçants'}
        </h4>
        <div className="space-y-1">
          {filteredPlayers.map((player, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-2 bg-gray-800/50 rounded hover:bg-gray-800 transition"
            >
              {player.shirt_number && (
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                  {player.shirt_number}
                </div>
              )}
              <div className="flex-1">
                <div className="font-medium">{player.name}</div>
                <div className="text-xs text-gray-400">{player.position}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-gray-900 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Compositions d'équipes</h2>
            <p className="text-sm text-gray-400 mt-1">
              {match.home_team} {match.home_score} - {match.away_score} {match.away_team}
            </p>
            <p className="text-xs text-gray-500">{match.date}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
            </div>
          ) : error ? (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-center">
              <p className="text-red-400">{error}</p>
              <button
                onClick={loadLineups}
                className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition"
              >
                Réessayer
              </button>
            </div>
          ) : lineups?.lineups ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Équipe domicile */}
              {lineups.lineups.home && (
                <div className="space-y-4">
                  <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4">
                    <h3 className="text-xl font-bold">{lineups.lineups.home.team || match.home_team}</h3>
                    {lineups.lineups.home.formation && (
                      <p className="text-sm text-gray-400 mt-1">
                        Formation: <span className="text-white font-semibold">{lineups.lineups.home.formation}</span>
                      </p>
                    )}
                  </div>

                  {lineups.lineups.home.players && renderPlayers(lineups.lineups.home.players, true)}
                  {lineups.lineups.home.players && renderPlayers(lineups.lineups.home.players, false)}
                </div>
              )}

              {/* Équipe extérieur */}
              {lineups.lineups.away && (
                <div className="space-y-4">
                  <div className="bg-orange-500/20 border border-orange-500 rounded-lg p-4">
                    <h3 className="text-xl font-bold">{lineups.lineups.away.team || match.away_team}</h3>
                    {lineups.lineups.away.formation && (
                      <p className="text-sm text-gray-400 mt-1">
                        Formation: <span className="text-white font-semibold">{lineups.lineups.away.formation}</span>
                      </p>
                    )}
                  </div>

                  {lineups.lineups.away.players && renderPlayers(lineups.lineups.away.players, true)}
                  {lineups.lineups.away.players && renderPlayers(lineups.lineups.away.players, false)}
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        {lineups?.source && (
          <div className="sticky bottom-0 bg-gray-800 p-4 border-t border-gray-700 text-center text-xs text-gray-500">
            Source: {lineups.source}
          </div>
        )}
      </div>
    </div>
  );
}
