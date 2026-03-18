import MatchCalendar from '@/components/MatchCalendar';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="max-w-6xl mx-auto px-4 py-8">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">⚽ Football Tracker</h1>
              <p className="text-gray-400">
                7 championnats - Premier League, La Liga, Serie A, Ligue 1, Portugal, Belgique, Turquie
              </p>
            </div>
            <Link
              href="/analysis"
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition flex items-center gap-2 font-semibold"
            >
              📊 Analyse Tirs Faibles
            </Link>
          </div>
        </header>

        <MatchCalendar />
      </main>
    </div>
  );
}
