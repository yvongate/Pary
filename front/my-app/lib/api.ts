/**
 * API Client - Football Predictions
 * Client pour communiquer avec le backend FastAPI
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Prediction {
  match_id: string;
  home_team: string;
  away_team: string;
  league_code: string;
  match_date: string;
  shots: {
    min: number;
    max: number;
    confidence: number;
    home_team_message?: string;
    away_team_message?: string;
    message_min: string;
    message_max: string;
  };
  corners: {
    min: number;
    max: number;
    confidence: number;
    home_team_message?: string;
    away_team_message?: string;
    message_min: string;
    message_max: string;
  };
  ai_reasoning_shots?: string;
  ai_reasoning_corners?: string;
  formations?: {
    home: string;
    away: string;
  };
  created_at?: string;
}

export interface PredictionDetail extends Prediction {
  shots_analysis?: any;
  corners_analysis?: any;
  weather?: any;
  rankings_used?: any;
}

export interface League {
  code: string;
  name: string;
  country: string;
}

export interface Fixture {
  id: string;
  league_code: string;
  league: string;
  date?: string;
  time?: string;
  home_team: string;
  away_team: string;
  status: string;
  home_score?: number;
  away_score?: number;
}

export interface MatchDay {
  date: string;
  matches: Fixture[];
}

export interface Player {
  name: string;
  shirt_number?: number;
  position?: string;
  substitute: boolean;
}

export interface TeamLineup {
  formation?: string;
  players: Player[];
}

export interface LineupsResponse {
  home_team: string;
  away_team: string;
  home_formation?: string;
  away_formation?: string;
  home_lineup?: TeamLineup;
  away_lineup?: TeamLineup;
}

/**
 * Récupère les prédictions à venir
 */
export async function getUpcomingPredictions(
  league?: string,
  limit: number = 20
): Promise<{ predictions: Prediction[]; count: number; league_name: string }> {
  const params = new URLSearchParams();
  if (league) params.append('league', league);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE_URL}/predictions/upcoming?${params}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch predictions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Récupère le détail d'une prédiction
 */
export async function getPredictionDetail(matchId: string): Promise<PredictionDetail> {
  const response = await fetch(`${API_BASE_URL}/predictions/match/${matchId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch prediction detail: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Récupère la liste des championnats
 */
export async function getLeagues(): Promise<League[]> {
  const response = await fetch(`${API_BASE_URL}/leagues`);
  if (!response.ok) {
    throw new Error(`Failed to fetch leagues: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Récupère les fixtures à venir
 */
export async function getFixtures(league?: string, days: number = 14) {
  const params = new URLSearchParams();
  if (league) params.append('league', league);
  params.append('days', days.toString());

  const response = await fetch(`${API_BASE_URL}/fixtures?${params}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch fixtures: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Récupère les fixtures groupés par date
 * Compatible avec l'ancien format: getFixturesByDate(pastDays, futureDays, league)
 */
export async function getFixturesByDate(
  pastDaysOrLeague?: number | string,
  futureDaysOrDays?: number,
  legacyLeague?: string
): Promise<MatchDay[]> {
  // Déterminer les vrais paramètres (support ancien et nouveau format)
  let league: string | undefined;
  let days: number;

  if (typeof pastDaysOrLeague === 'string') {
    // Nouveau format: getFixturesByDate(league?, days?)
    league = pastDaysOrLeague;
    days = futureDaysOrDays || 14;
  } else {
    // Ancien format: getFixturesByDate(pastDays, futureDays, league)
    // On prend futureDays comme le nombre de jours
    days = futureDaysOrDays || (pastDaysOrLeague || 14);
    league = legacyLeague;
  }

  const data = await getFixtures(league, days);
  const fixtures: Fixture[] = data.matches || [];

  // Grouper par date
  const groupedByDate: { [key: string]: Fixture[] } = {};

  fixtures.forEach((fixture) => {
    const date = fixture.date || 'unknown';
    if (!groupedByDate[date]) {
      groupedByDate[date] = [];
    }
    groupedByDate[date].push(fixture);
  });

  // Convertir en array de MatchDay
  const matchDays: MatchDay[] = Object.entries(groupedByDate)
    .map(([date, matches]) => ({
      date,
      matches: matches.sort((a, b) => {
        const timeA = a.time || '00:00';
        const timeB = b.time || '00:00';
        return timeA.localeCompare(timeB);
      })
    }))
    .sort((a, b) => a.date.localeCompare(b.date));

  return matchDays;
}

/**
 * Récupère les compositions (lineups) d'un match
 */
export async function getLineups(
  homeTeam: string,
  awayTeam: string,
  date?: string
): Promise<LineupsResponse> {
  const params = new URLSearchParams();
  params.append('home_team', homeTeam);
  params.append('away_team', awayTeam);
  if (date) params.append('date', date);

  try {
    const response = await fetch(`${API_BASE_URL}/lineups?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch lineups: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    // Si l'endpoint n'existe pas encore, retourner une réponse vide
    console.warn('Lineups endpoint not available yet:', error);
    return {
      home_team: homeTeam,
      away_team: awayTeam,
      home_formation: undefined,
      away_formation: undefined,
      home_lineup: undefined,
      away_lineup: undefined
    };
  }
}
