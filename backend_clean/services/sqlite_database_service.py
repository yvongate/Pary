"""
Service de base de données SQLite (local)
Alternative simple à PostgreSQL/Supabase pour le développement
"""
import sqlite3
import json
from typing import Optional, List, Dict
from datetime import datetime
import os


class SQLiteDatabaseService:
    """Service de gestion de la base de données SQLite"""

    def __init__(self, db_path: str = "predictions.db"):
        self.db_path = db_path
        self.conn = None
        self._create_tables()

    def _create_tables(self):
        """Crée les tables si elles n'existent pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT UNIQUE NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league_code TEXT NOT NULL,
                match_date TEXT NOT NULL,
                shots_min INTEGER NOT NULL,
                shots_max INTEGER NOT NULL,
                shots_confidence REAL NOT NULL,
                corners_min INTEGER NOT NULL,
                corners_max INTEGER NOT NULL,
                corners_confidence REAL NOT NULL,
                analysis_shots TEXT,
                analysis_corners TEXT,
                ai_reasoning_shots TEXT,
                ai_reasoning_corners TEXT,
                home_formation TEXT,
                away_formation TEXT,
                weather TEXT,
                rankings_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ajouter les colonnes home_shots, away_shots, home_corners, away_corners si elles n'existent pas
        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_shots REAL")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_shots REAL")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_corners REAL")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_corners REAL")
        except sqlite3.OperationalError:
            pass

        # Ajouter les fourchettes par équipe
        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_shots_min INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_shots_max INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_shots_min INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_shots_max INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_corners_min INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN home_corners_max INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_corners_min INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE match_predictions ADD COLUMN away_corners_max INTEGER")
        except sqlite3.OperationalError:
            pass

        # Table pour stocker les lineups (compositions) récupérées via SerpAPI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_lineups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT UNIQUE NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                league_code TEXT NOT NULL,
                match_date TEXT NOT NULL,
                lineup_raw_text TEXT,
                home_formation TEXT,
                away_formation TEXT,
                source TEXT,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def connect(self) -> bool:
        """Établit la connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Pour avoir des résultats en dict
            return True
        except Exception as e:
            print(f"[ERREUR DATABASE] Connexion échouée: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def insert_prediction(self, prediction: Dict) -> Optional[int]:
        """
        Insère ou met à jour une prédiction (UPSERT)

        Args:
            prediction: Données de la prédiction

        Returns:
            ID de la prédiction ou None si erreur
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            # Convertir dict en JSON string pour SQLite
            weather_str = json.dumps(prediction.get('weather')) if prediction.get('weather') else None
            rankings_str = json.dumps(prediction.get('rankings_used')) if prediction.get('rankings_used') else None
            analysis_shots_str = json.dumps(prediction.get('analysis_shots')) if prediction.get('analysis_shots') else None
            analysis_corners_str = json.dumps(prediction.get('analysis_corners')) if prediction.get('analysis_corners') else None

            cursor.execute("""
                INSERT INTO match_predictions (
                    match_id, home_team, away_team, league_code, match_date,
                    shots_min, shots_max, shots_confidence,
                    corners_min, corners_max, corners_confidence,
                    home_shots, away_shots, home_corners, away_corners,
                    home_shots_min, home_shots_max, away_shots_min, away_shots_max,
                    home_corners_min, home_corners_max, away_corners_min, away_corners_max,
                    analysis_shots, analysis_corners,
                    ai_reasoning_shots, ai_reasoning_corners,
                    home_formation, away_formation, weather, rankings_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    home_team = excluded.home_team,
                    away_team = excluded.away_team,
                    league_code = excluded.league_code,
                    match_date = excluded.match_date,
                    shots_min = excluded.shots_min,
                    shots_max = excluded.shots_max,
                    shots_confidence = excluded.shots_confidence,
                    corners_min = excluded.corners_min,
                    corners_max = excluded.corners_max,
                    corners_confidence = excluded.corners_confidence,
                    home_shots = excluded.home_shots,
                    away_shots = excluded.away_shots,
                    home_corners = excluded.home_corners,
                    away_corners = excluded.away_corners,
                    home_shots_min = excluded.home_shots_min,
                    home_shots_max = excluded.home_shots_max,
                    away_shots_min = excluded.away_shots_min,
                    away_shots_max = excluded.away_shots_max,
                    home_corners_min = excluded.home_corners_min,
                    home_corners_max = excluded.home_corners_max,
                    away_corners_min = excluded.away_corners_min,
                    away_corners_max = excluded.away_corners_max,
                    analysis_shots = excluded.analysis_shots,
                    analysis_corners = excluded.analysis_corners,
                    ai_reasoning_shots = excluded.ai_reasoning_shots,
                    ai_reasoning_corners = excluded.ai_reasoning_corners,
                    home_formation = excluded.home_formation,
                    away_formation = excluded.away_formation,
                    weather = excluded.weather,
                    rankings_used = excluded.rankings_used,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                prediction['match_id'],
                prediction['home_team'],
                prediction['away_team'],
                prediction['league_code'],
                prediction['match_date'].isoformat() if isinstance(prediction['match_date'], datetime) else prediction['match_date'],
                prediction['shots_min'],
                prediction['shots_max'],
                prediction['shots_confidence'],
                prediction['corners_min'],
                prediction['corners_max'],
                prediction['corners_confidence'],
                prediction.get('home_shots'),
                prediction.get('away_shots'),
                prediction.get('home_corners'),
                prediction.get('away_corners'),
                prediction.get('home_shots_min'),
                prediction.get('home_shots_max'),
                prediction.get('away_shots_min'),
                prediction.get('away_shots_max'),
                prediction.get('home_corners_min'),
                prediction.get('home_corners_max'),
                prediction.get('away_corners_min'),
                prediction.get('away_corners_max'),
                analysis_shots_str,
                analysis_corners_str,
                prediction.get('ai_reasoning_shots'),
                prediction.get('ai_reasoning_corners'),
                prediction.get('home_formation'),
                prediction.get('away_formation'),
                weather_str,
                rankings_str
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"[ERREUR] Insertion prédiction: {e}")
            return None

    def get_upcoming_predictions(self, league_code: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Récupère les prédictions à venir

        Args:
            league_code: Filtrer par ligue (optionnel)
            limit: Nombre max de résultats

        Returns:
            Liste de prédictions
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            if league_code:
                cursor.execute("""
                    SELECT * FROM match_predictions
                    WHERE league_code = ?
                    AND match_date >= date('now')
                    ORDER BY match_date ASC
                    LIMIT ?
                """, (league_code, limit))
            else:
                cursor.execute("""
                    SELECT * FROM match_predictions
                    WHERE match_date >= date('now')
                    ORDER BY match_date ASC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"[ERREUR] Récupération prédictions: {e}")
            return []

    def get_prediction_by_match_id(self, match_id: str) -> Optional[Dict]:
        """
        Récupère une prédiction par son match_id

        Args:
            match_id: ID du match

        Returns:
            Prédiction ou None
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM match_predictions
                WHERE match_id = ?
            """, (match_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            print(f"[ERREUR] Récupération prédiction: {e}")
            return None

    def delete_prediction(self, prediction_id: int) -> bool:
        """
        Supprime une prédiction

        Args:
            prediction_id: ID de la prédiction

        Returns:
            True si succès
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM match_predictions WHERE id = ?", (prediction_id,))
            self.conn.commit()
            return True

        except Exception as e:
            print(f"[ERREUR] Suppression prédiction: {e}")
            return False

    def get_all_predictions(self, limit: int = 100) -> List[Dict]:
        """Récupère toutes les prédictions"""
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM match_predictions
                ORDER BY match_date DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"[ERREUR] Récupération prédictions: {e}")
            return []

    # ====== METHODES POUR LINEUPS ======

    def insert_lineup(self, lineup_data: Dict) -> Optional[int]:
        """
        Insère ou met à jour les lineups d'un match (UPSERT)

        Args:
            lineup_data: {
                'match_id': str,
                'home_team': str,
                'away_team': str,
                'league_code': str,
                'match_date': str,
                'lineup_raw_text': str,  # Texte brut SerpAPI
                'home_formation': str (optionnel),
                'away_formation': str (optionnel),
                'source': str
            }

        Returns:
            ID de l'entrée ou None si erreur
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO match_lineups (
                    match_id, home_team, away_team, league_code, match_date,
                    lineup_raw_text, home_formation, away_formation, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    lineup_raw_text = excluded.lineup_raw_text,
                    home_formation = excluded.home_formation,
                    away_formation = excluded.away_formation,
                    source = excluded.source,
                    fetched_at = CURRENT_TIMESTAMP
            """, (
                lineup_data['match_id'],
                lineup_data['home_team'],
                lineup_data['away_team'],
                lineup_data['league_code'],
                lineup_data['match_date'].isoformat() if isinstance(lineup_data['match_date'], datetime) else lineup_data['match_date'],
                lineup_data.get('lineup_raw_text'),
                lineup_data.get('home_formation'),
                lineup_data.get('away_formation'),
                lineup_data.get('source', 'serpapi')
            ))

            self.conn.commit()
            print(f"[DB] Lineup sauvegardée pour {lineup_data['match_id']}")
            return cursor.lastrowid

        except Exception as e:
            print(f"[ERREUR] Insertion lineup: {e}")
            return None

    def get_lineup_by_match_id(self, match_id: str) -> Optional[Dict]:
        """
        Récupère les lineups d'un match par son match_id

        Args:
            match_id: ID du match

        Returns:
            Lineup data ou None si non trouvé
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM match_lineups
                WHERE match_id = ?
            """, (match_id,))

            row = cursor.fetchone()
            if row:
                result = dict(row)
                return result
            return None

        except Exception as e:
            print(f"[ERREUR] Récupération lineup: {e}")
            return None

    def get_matches_needing_lineups(self, time_before_match_minutes: int = 60) -> List[Dict]:
        """
        Récupère les matchs qui ont besoin de lineups
        (matchs qui commencent dans environ time_before_match_minutes)

        Args:
            time_before_match_minutes: Temps avant le match en minutes (défaut: 60)

        Returns:
            Liste de matchs qui ont besoin de lineups
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

            # Récupérer tous les matchs à venir qui n'ont pas encore de lineup
            cursor.execute("""
                SELECT mp.*
                FROM match_predictions mp
                LEFT JOIN match_lineups ml ON mp.match_id = ml.match_id
                WHERE mp.match_date >= datetime('now')
                AND ml.match_id IS NULL
                ORDER BY mp.match_date ASC
            """)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            print(f"[ERREUR] Récupération matchs sans lineups: {e}")
            return []


# Instance globale
_sqlite_db = None

def get_sqlite_db() -> SQLiteDatabaseService:
    """Retourne l'instance globale de la base SQLite"""
    global _sqlite_db
    if _sqlite_db is None:
        _sqlite_db = SQLiteDatabaseService()
        _sqlite_db.connect()
    return _sqlite_db
