'use client';

import { useState, useEffect } from 'react';
import { MatchDay, Fixture, getFixturesByDate, League, getLeagues } from '@/lib/api';
import LineupModal from './LineupModal';

const LEAGUE_COLORS: { [key: string]: string } = {
  'Premier League': 'bg-purple-500',
  'Championship': 'bg-purple-400',
  'La Liga': 'bg-orange-500',
  'Serie A': 'bg-cyan-500',
  'Bundesliga': 'bg-red-500',
  'Ligue 1': 'bg-blue-500',
  'Ligue 2': 'bg-blue-400',
  'Primeira Liga': 'bg-green-500',
  // Fallbacks pour les codes de ligue
  'PL': 'bg-purple-500',
  'ELC': 'bg-purple-400',
  'PD': 'bg-orange-500',
  'SA': 'bg-cyan-500',
  'BL1': 'bg-red-500',
  'FL1': 'bg-blue-500',
  'FL2': 'bg-blue-400',
  'PPL': 'bg-green-500',
};

const LEAGUE_EMOJIS: { [key: string]: string } = {
  'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'Spain': '🇪🇸',
  'Italy': '🇮🇹',
  'Germany': '🇩🇪',
  'France': '🇫🇷',
  'Portugal': '🇵🇹',
};

export default function MatchCalendar() {
  const [matchDays, setMatchDays] = useState<MatchDay[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<Fixture | null>(null);

  useEffect(() => {
    loadLeagues();
  }, []);

  useEffect(() => {
    loadFixtures();
  }, [selectedLeague]);

  const loadLeagues = async () => {
    try {
      const data = await getLeagues();
      setLeagues(data);
    } catch (err) {
      console.error('Error loading leagues:', err);
    }
  };

  const loadFixtures = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching fixtures from API...');
      // 7 jours passés + aujourd'hui + 7 jours futurs
      const data = await getFixturesByDate(7, 7, selectedLeague || undefined);
      console.log(`Fetched ${data.length} days with fixtures:`, data);
      if (data.length === 0) {
        setError('Aucun match trouvé pour cette période');
      }
      setMatchDays(data);
      if (data.length > 0 && !selectedDate) {
        // Sélectionne aujourd'hui par défaut s'il existe, sinon le premier jour
        const today = new Date().toISOString().split('T')[0];
        const todayMatchDay = data.find(md => md.date === today);
        setSelectedDate(todayMatchDay ? todayMatchDay.date : data[0].date);
      }
    } catch (err) {
      setError('Erreur lors du chargement des matchs - Vérifie que le backend tourne sur http://localhost:8000');
      console.error('Error loading fixtures:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectedMatches = matchDays.find(md => md.date === selectedDate)?.matches || [];

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    });
  };

  const isToday = (dateStr: string) => {
    const today = new Date().toISOString().split('T')[0];
    return dateStr === today;
  };

  const isPast = (dateStr: string) => {
    const today = new Date().toISOString().split('T')[0];
    return dateStr < today;
  };

  const formatTime = (dateStr?: string, timeStr?: string) => {
    if (timeStr) return timeStr;
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleMatchClick = (match: Fixture) => {
    if (match.status === 'FINISHED') {
      setSelectedMatch(match);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-center">
        <p className="text-red-400">{error}</p>
        <button
          onClick={loadFixtures}
          className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header avec filtres */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Calendrier des Matchs</h2>
          <p className="text-gray-400 text-sm mt-1">
            {selectedLeague
              ? leagues.find(l => l.code === selectedLeague)?.name
              : 'Tous les championnats'}
          </p>
        </div>

        <div className="flex gap-2">
          {/* Filtre par championnat */}
          <select
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            className="px-3 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 text-sm"
          >
            <option value="">Tous les championnats</option>
            {leagues.map((league) => (
              <option key={league.code} value={league.code}>
                {LEAGUE_EMOJIS[league.country] || '⚽'} {league.name}
              </option>
            ))}
          </select>

          <button
            onClick={loadFixtures}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition text-sm"
          >
            Rafraîchir
          </button>
        </div>
      </div>

      {/* Date Selector */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {matchDays.map((matchDay) => {
          const past = isPast(matchDay.date);
          const today = isToday(matchDay.date);

          return (
            <button
              key={matchDay.date}
              onClick={() => setSelectedDate(matchDay.date)}
              className={`flex-shrink-0 px-4 py-3 rounded-lg transition-all relative ${
                selectedDate === matchDay.date
                  ? 'bg-blue-500 text-white'
                  : today
                  ? 'bg-green-600/30 text-green-400 border border-green-500/50 hover:bg-green-600/50'
                  : past
                  ? 'bg-gray-800/50 text-gray-500 hover:bg-gray-800'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {today && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full"></div>
              )}
              <div className="text-xs uppercase tracking-wider">{formatDate(matchDay.date)}</div>
              <div className={`text-lg font-bold ${past ? 'text-gray-500' : ''}`}>
                {matchDay.matches.length} matchs
              </div>
              {today && <div className="text-[10px] text-green-400">AUJOURD'HUI</div>}
              {past && !today && <div className="text-[10px] text-gray-600">PASSÉ</div>}
            </button>
          );
        })}
      </div>

      {/* Matches List */}
      <div className="bg-gray-900 rounded-xl overflow-hidden">
        <div className="p-4 bg-gray-800 border-b border-gray-700">
          <h3 className="font-semibold text-lg">
            Matchs du {selectedDate ? formatDate(selectedDate) : ''}
          </h3>
        </div>

        {selectedMatches.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            Aucun match programmé ce jour
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {selectedMatches.map((match: Fixture) => (
              <div
                key={match.id}
                onClick={() => handleMatchClick(match)}
                className={`p-4 hover:bg-gray-800/50 transition flex items-center justify-between ${
                  match.status === 'FINISHED' ? 'cursor-pointer' : ''
                }`}
              >
                <div className="flex items-center gap-4 flex-1">
                  {/* League Badge */}
                  <div className={`${LEAGUE_COLORS[match.league] || 'bg-gray-500'} text-white text-xs px-2 py-1 rounded font-medium min-w-[100px] text-center`}>
                    {match.league}
                  </div>

                  {/* Teams */}
                  <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                    <div className="flex items-center gap-2 flex-1">
                      <span className="font-medium">{match.home_team}</span>
                    </div>

                    <div className="text-center px-4">
                      {match.status === 'FINISHED' && match.home_score !== null && match.away_score !== null ? (
                        <span className="text-xl font-bold">
                          {match.home_score} - {match.away_score}
                        </span>
                      ) : (
                        <span className="text-gray-500">vs</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-1 justify-start sm:justify-end">
                      <span className="font-medium">{match.away_team}</span>
                    </div>
                  </div>
                </div>

                {/* Time / Status */}
                <div className="text-gray-400 text-sm ml-4 text-right">
                  {match.status === 'FINISHED' ? (
                    <span className="text-green-400 text-xs">Terminé</span>
                  ) : (
                    <div>
                      <div>{formatTime(match.date, match.time)}</div>
                      {match.time && <div className="text-xs text-gray-500">{match.time}</div>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        {Object.entries(LEAGUE_COLORS).map(([league, color]) => (
          <div key={league} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded ${color}`}></div>
            <span className="text-gray-400">{league}</span>
          </div>
        ))}
      </div>

      {/* Lineup Modal */}
      {selectedMatch && (
        <LineupModal
          match={selectedMatch}
          onClose={() => setSelectedMatch(null)}
        />
      )}
    </div>
  );
}
