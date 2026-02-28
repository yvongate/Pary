"""
Service de base de données (Supabase/PostgreSQL OU SQLite local)
Gère toutes les opérations de base de données
"""
import psycopg2
import json
from typing import Optional, List, Dict
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import settings

# NOUVEAU : Import SQLite comme alternative
try:
    from services.sqlite_database_service import get_sqlite_db
    USE_SQLITE = True
    print("[INFO] Utilisation de SQLite (base locale)")
except:
    USE_SQLITE = False


class DatabaseService:
    """Service de gestion de la base de données"""

    def __init__(self):
        self.connection_string = settings.DATABASE_URL
        self.conn = None

    def connect(self) -> bool:
        """Établit la connexion à la base de données"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
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
            print("[ERREUR] Pas de connexion à la BDD")
            return None

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO match_predictions (
                    match_id, home_team, away_team, league_code, match_date,
                    shots_min, shots_max, shots_confidence,
                    corners_min, corners_max, corners_confidence,
                    analysis_shots, analysis_corners,
                    ai_reasoning_shots, ai_reasoning_corners,
                    home_formation, away_formation, weather, rankings_used
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (match_id) DO UPDATE SET
                    home_team = EXCLUDED.home_team,
                    away_team = EXCLUDED.away_team,
                    league_code = EXCLUDED.league_code,
                    match_date = EXCLUDED.match_date,
                    shots_min = EXCLUDED.shots_min,
                    shots_max = EXCLUDED.shots_max,
                    shots_confidence = EXCLUDED.shots_confidence,
                    corners_min = EXCLUDED.corners_min,
                    corners_max = EXCLUDED.corners_max,
                    corners_confidence = EXCLUDED.corners_confidence,
                    analysis_shots = EXCLUDED.analysis_shots,
                    analysis_corners = EXCLUDED.analysis_corners,
                    ai_reasoning_shots = EXCLUDED.ai_reasoning_shots,
                    ai_reasoning_corners = EXCLUDED.ai_reasoning_corners,
                    home_formation = EXCLUDED.home_formation,
                    away_formation = EXCLUDED.away_formation,
                    weather = EXCLUDED.weather,
                    rankings_used = EXCLUDED.rankings_used,
                    updated_at = NOW()
                RETURNING id
            """, (
                prediction['match_id'],
                prediction['home_team'],
                prediction['away_team'],
                prediction['league_code'],
                prediction['match_date'],
                prediction['shots_min'],
                prediction['shots_max'],
                prediction['shots_confidence'],
                prediction['corners_min'],
                prediction['corners_max'],
                prediction['corners_confidence'],
                json.dumps(prediction.get('analysis_shots')),
                json.dumps(prediction.get('analysis_corners')),
                prediction.get('ai_reasoning_shots'),
                prediction.get('ai_reasoning_corners'),
                prediction.get('home_formation'),
                prediction.get('away_formation'),
                json.dumps(prediction.get('weather')),
                json.dumps(prediction.get('rankings_used'))
            ))

            pred_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()

            return pred_id

        except Exception as e:
            print(f"[ERREUR] Insertion prédiction: {e}")
            self.conn.rollback()
            return None

    def get_upcoming_predictions(self, league_code: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Récupère les prédictions à venir (incluant les matchs d'aujourd'hui)

        Args:
            league_code: Code de la ligue (optionnel)
            limit: Nombre max de résultats

        Returns:
            Liste des prédictions
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()

            # Récupérer les matchs à partir d'aujourd'hui (incluant les matchs passés d'aujourd'hui)
            if league_code:
                cursor.execute("""
                    SELECT * FROM match_predictions
                    WHERE league_code = %s
                    AND match_date >= CURRENT_DATE
                    ORDER BY match_date ASC
                    LIMIT %s
                """, (league_code, limit))
            else:
                cursor.execute("""
                    SELECT * FROM match_predictions
                    WHERE match_date >= CURRENT_DATE
                    ORDER BY match_date ASC
                    LIMIT %s
                """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()

            predictions = []
            for row in rows:
                pred = dict(zip(columns, row))
                predictions.append(pred)

            return predictions

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
            return None

        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT * FROM match_predictions
                WHERE match_id = %s
            """, (match_id,))

            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            cursor.close()

            if row:
                return dict(zip(columns, row))
            return None

        except Exception as e:
            print(f"[ERREUR] Récupération prédiction {match_id}: {e}")
            return None

    def create_tables(self, sql_file: str = "database_schema.sql") -> bool:
        """
        Crée les tables depuis un fichier SQL

        Args:
            sql_file: Chemin vers le fichier SQL

        Returns:
            True si succès, False sinon
        """
        if not self.conn:
            return False

        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            cursor = self.conn.cursor()
            cursor.execute(sql_content)
            self.conn.commit()
            cursor.close()

            return True

        except Exception as e:
            print(f"[ERREUR] Création tables: {e}")
            self.conn.rollback()
            return False


# Instance globale (singleton)
_db_instance = None

def get_database():
    """
    Retourne l'instance singleton du service de base de données
    Utilise SQLite par défaut (plus simple pour développement)
    """
    global _db_instance
    if _db_instance is None:
        # Utiliser SQLite au lieu de PostgreSQL
        from services.sqlite_database_service import get_sqlite_db
        _db_instance = get_sqlite_db()
        print("[DATABASE] Utilisation de SQLite (base locale)")
    return _db_instance
