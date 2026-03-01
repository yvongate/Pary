"""
Module de connexion  Supabase (PostgreSQL)
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class SupabaseClient:
    """Client pour interagir avec la base de donnes Supabase"""

    def __init__(self):
        """Initialise la connexion  Supabase"""
        import os
        # Utiliser les variables d'environnement
        supabase_url = os.getenv("SUPABASE_URL", "https://qibilvupnrqyxsoxpbze.supabase.co")
        supabase_key = os.getenv("SUPABASE_KEY", "")

        # Extraire le project ref (ex: qibilvupnrqyxsoxpbze)
        if "supabase.co" in supabase_url:
            project_ref = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
        else:
            project_ref = "qibilvupnrqyxsoxpbze"

        # Le mot de passe est la clé service_role ou le mot de passe configuré
        password = os.getenv("SUPABASE_PASSWORD") or supabase_key or "voicilemotdepassedepary"

        # Connection avec pooler IPv4 (session mode)
        # Utiliser aws-0-eu-west-1 pour la région Europe West
        self.connection_string = (
            f"postgresql://postgres.{project_ref}:{password}"
            f"@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
        )
        self.conn = None

    def connect(self):
        """tablit la connexion  la base de donnes"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            return True
        except Exception as e:
            print(f" Erreur connexion Supabase: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """
        Excute une requte SELECT

        Args:
            query: Requte SQL
            params: Paramtres de la requte

        Returns:
            Liste de rsultats (dict)
        """
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            print(f" Erreur excution query: {e}")
            return None

    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """
        Excute une requte INSERT

        Args:
            query: Requte SQL
            params: Paramtres de la requte

        Returns:
            ID de l'enregistrement insr
        """
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()

                # Rcuprer l'ID insr
                cursor.execute("SELECT lastval()")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f" Erreur insertion: {e}")
            self.conn.rollback()
            return None

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """
        Excute une requte UPDATE

        Args:
            query: Requte SQL
            params: Paramtres de la requte

        Returns:
            True si succs
        """
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return True
        except Exception as e:
            print(f" Erreur update: {e}")
            self.conn.rollback()
            return False

    # === MTHODES SPCIFIQUES POUR LES PRDICTIONS ===

    def insert_prediction(self, prediction_data: Dict) -> Optional[int]:
        """
        Insre une nouvelle prdiction

        Args:
            prediction_data: {
                match_id, home_team, away_team, league_code, match_date,
                shots_min, shots_max, shots_confidence,
                corners_min, corners_max, corners_confidence,
                analysis_shots, analysis_corners,
                ai_reasoning_shots, ai_reasoning_corners,
                home_formation, away_formation, weather, rankings_used
            }

        Returns:
            ID de la prdiction insre
        """
        query = """
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
        """

        params = (
            prediction_data['match_id'],
            prediction_data['home_team'],
            prediction_data['away_team'],
            prediction_data['league_code'],
            prediction_data['match_date'],
            prediction_data['shots_min'],
            prediction_data['shots_max'],
            prediction_data['shots_confidence'],
            prediction_data['corners_min'],
            prediction_data['corners_max'],
            prediction_data['corners_confidence'],
            Json(prediction_data.get('analysis_shots', {})),
            Json(prediction_data.get('analysis_corners', {})),
            prediction_data.get('ai_reasoning_shots'),
            prediction_data.get('ai_reasoning_corners'),
            prediction_data.get('home_formation'),
            prediction_data.get('away_formation'),
            Json(prediction_data.get('weather', {})),
            Json(prediction_data.get('rankings_used', {}))
        )

        return self.execute_insert(query, params)

    def get_upcoming_predictions(self, league_code: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Rcupre les prdictions  venir

        Args:
            league_code: Code du championnat (optionnel)
            limit: Nombre max de rsultats

        Returns:
            Liste des prdictions
        """
        if league_code:
            query = """
                SELECT * FROM upcoming_predictions
                WHERE league_code = %s
                LIMIT %s
            """
            params = (league_code, limit)
        else:
            query = """
                SELECT * FROM upcoming_predictions
                LIMIT %s
            """
            params = (limit,)

        return self.execute_query(query, params) or []

    def get_prediction_by_match_id(self, match_id: str) -> Optional[Dict]:
        """
        Rcupre une prdiction par match_id

        Args:
            match_id: ID du match

        Returns:
            Prdiction complte
        """
        query = """
            SELECT * FROM match_predictions
            WHERE match_id = %s
        """
        results = self.execute_query(query, (match_id,))
        return results[0] if results else None

    def invalidate_prediction(self, match_id: str) -> bool:
        """
        Invalide une prdiction (si compos ont chang)

        Args:
            match_id: ID du match

        Returns:
            True si succs
        """
        query = """
            UPDATE match_predictions
            SET is_valid = FALSE
            WHERE match_id = %s
        """
        return self.execute_update(query, (match_id,))

    def log_analysis_step(self, match_id: str, step_number: int,
                         step_name: str, step_result: str,
                         execution_time_ms: int) -> bool:
        """
        Enregistre une tape d'analyse

        Args:
            match_id: ID du match
            step_number: Numro de l'tape
            step_name: Nom de l'tape
            step_result: Rsultat
            execution_time_ms: Temps d'excution

        Returns:
            True si succs
        """
        query = """
            INSERT INTO analysis_logs (
                match_id, step_number, step_name, step_result, execution_time_ms
            ) VALUES (%s, %s, %s, %s, %s)
        """
        params = (match_id, step_number, step_name, step_result, execution_time_ms)
        return self.execute_insert(query, params) is not None


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    # Test connexion
    client = SupabaseClient()

    print("=" * 60)
    print("TEST CONNEXION SUPABASE")
    print("=" * 60)

    if client.connect():
        print(" Connexion russie!")

        # Test insertion
        test_prediction = {
            'match_id': 'test_001',
            'home_team': 'Tottenham',
            'away_team': 'Arsenal',
            'league_code': 'E0',
            'match_date': datetime(2026, 2, 25, 20, 0),
            'shots_min': 10,
            'shots_max': 14,
            'shots_confidence': 0.87,
            'corners_min': 6,
            'corners_max': 9,
            'corners_confidence': 0.82,
            'analysis_shots': {'test': 'data'},
            'analysis_corners': {'test': 'data'},
            'ai_reasoning_shots': 'Test reasoning',
            'ai_reasoning_corners': 'Test reasoning',
            'home_formation': '4-3-3',
            'away_formation': '5-4-1',
            'weather': {'temp': 12},
            'rankings_used': {'home': 4, 'away': 2}
        }

        pred_id = client.insert_prediction(test_prediction)
        if pred_id:
            print(f" Prdiction insre: ID {pred_id}")

        # Test rcupration
        predictions = client.get_upcoming_predictions()
        print(f" Prdictions  venir: {len(predictions)}")

        client.disconnect()
    else:
        print(" chec connexion")
