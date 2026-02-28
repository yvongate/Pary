import MatchCalendar from '@/components/MatchCalendar';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="max-w-6xl mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">⚽ Football Tracker</h1>
          <p className="text-gray-400">
            8 championnats européens - Premier League, Championship, La Liga, Serie A, Bundesliga, Ligue 1, Ligue 2, Primeira Liga
          </p>
        </header>

        <MatchCalendar />
      </main>
    </div>
  );
}
