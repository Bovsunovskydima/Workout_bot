import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "workout_bot.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL,
                    set_number INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workout_id) REFERENCES workouts (id),
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
                )
            ''')
            conn.commit()

        self.populate_default_exercises()
        logging.info("✅ База даних ініціалізована успішно")

    def populate_default_exercises(self):
        default_exercises = [
            "віджимання", "жим лежачи", "підтягування", "прес",
            "тяга штанги", "присідання", "випади", "станова тягу",
            "підйом гантелей", "тяга блока", "скручування",
            "бурпі", "мах ногами", "віджимання на брусах", "підйом ніг",
            "розведення рук", "жим гантелей", "згинання рук"
        ]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name in default_exercises:
                try:
                    cursor.execute("INSERT INTO exercises (name) VALUES (?)", (name.strip().lower(),))
                except sqlite3.IntegrityError:
                    continue
            conn.commit()

    def get_all_exercises(self) -> List[str]:
        """Повертає список доступних вправ"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM exercises ORDER BY name")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def add_user(self, telegram_id: int, username: str = None, first_name: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
            if user:
                return user[0]
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (telegram_id, username, first_name))
            return cursor.lastrowid

    def start_workout(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM workouts 
                WHERE user_id = ? AND status = 'active'
            ''', (user_id,))
            active = cursor.fetchone()
            if active:
                return active[0]
            cursor.execute('''
                INSERT INTO workouts (user_id, start_time, status)
                VALUES (?, ?, 'active')
            ''', (user_id, datetime.now()))
            return cursor.lastrowid

    def get_active_workout(self, user_id: int) -> Optional[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM workouts 
                WHERE user_id = ? AND status = 'active'
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_set(self, workout_id: int, exercise_name: str, reps: int, weight: float = None, set_number: int = None) -> int:
        normalized_name = exercise_name.strip().lower().rstrip(",. ")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM exercises WHERE name = ?", (normalized_name,))
            exercise = cursor.fetchone()
            if not exercise:
                raise ValueError(f"❌ Вправа '{exercise_name}' не знайдена в довіднику.")
            exercise_id = exercise[0]
            cursor.execute('''
                INSERT INTO sets (workout_id, exercise_id, reps, weight, set_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (workout_id, exercise_id, reps, weight, set_number))
            return cursor.lastrowid

    def finish_workout(self, workout_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE workouts 
                SET end_time = ?, status = 'completed'
                WHERE id = ?
            ''', (datetime.now(), workout_id))
            cursor.execute('''
                SELECT start_time, end_time FROM workouts WHERE id = ?
            ''', (workout_id,))
            workout_data = cursor.fetchone()
            cursor.execute('''
                SELECT e.name, s.reps, s.weight, s.set_number
                FROM sets s
                JOIN exercises e ON s.exercise_id = e.id
                WHERE s.workout_id = ?
                ORDER BY s.timestamp
            ''', (workout_id,))
            sets_data = cursor.fetchall()
            return {
                'start_time': workout_data[0],
                'end_time': workout_data[1],
                'sets': sets_data
            }

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM workouts 
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id,))
            total_workouts = cursor.fetchone()[0]
            if total_workouts == 0:
                return {'total_workouts': 0}
            cursor.execute('''
                SELECT COUNT(*), SUM(s.reps)
                FROM sets s
                JOIN workouts w ON s.workout_id = w.id
                WHERE w.user_id = ? AND w.status = 'completed'
            ''', (user_id,))
            total_sets, total_reps = cursor.fetchone()
            cursor.execute('''
                SELECT SUM((julianday(end_time) - julianday(start_time)) * 24 * 60)
                FROM workouts 
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id,))
            total_time = cursor.fetchone()[0] or 0
            total_time = int(total_time)
            cursor.execute('''
                SELECT e.name, COUNT(*) as cnt
                FROM sets s
                JOIN exercises e ON s.exercise_id = e.id
                JOIN workouts w ON s.workout_id = w.id
                WHERE w.user_id = ? AND w.status = 'completed'
                GROUP BY e.name
                ORDER BY cnt DESC
                LIMIT 3
            ''', (user_id,))
            top_exercises = cursor.fetchall()
            return {
                'total_workouts': total_workouts,
                'total_sets': total_sets or 0,
                'total_reps': total_reps or 0,
                'total_time': total_time,
                'top_exercises': top_exercises
            }
    