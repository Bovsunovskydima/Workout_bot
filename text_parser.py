import re
import json
import logging
from openai import OpenAI
from typing import Optional, Dict, Any, Tuple
from database import DatabaseManager

class TextParser:
    def __init__(self, db: DatabaseManager, openai_client: OpenAI, model_name="gpt-4o"):
        self.db = db
        self.client = openai_client
        self.model = model_name

    def get_available_exercises(self) -> list[str]:
        return [ex.lower() for ex in self.db.get_all_exercises()]

    def build_prompt(self, message: str) -> str:
        exercises = self.get_available_exercises()
        examples = [
            ("Я зробив 3 підходи по 10 підтягувань без ваги", 
             '{"exercise": "підтягування", "reps": 10, "weight": null, "set_number": 3}'),
            ("Жим лежачи: 12 повторів з вагою 50 кг", 
             '{"exercise": "жим лежачи", "reps": 12, "weight": 50, "set_number": null}'),
            ("10 присідань, 20 кг", 
             '{"exercise": "присідання", "reps": 10, "weight": 20, "set_number": null}')
        ]
        
        return f"""
Аналізуй повідомлення про вправу і поверни JSON. Доступні вправи: {', '.join(exercises)}
Якщо вправи немає у списку - поверни "unknown_exercise": true.
Якщо не можеш розпізнати - поверни "unrecognized": true.

Приклади:
{chr(10).join(f"- {input} → {output}" for input, output in examples)}

Повідомлення для аналізу: "{message}"
"""

    def parse_exercise_input(self, user_message: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Повертає (exercise_data, error_type)"""
        prompt = self.build_prompt(user_message)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            
            if data.get('unrecognized', False):
                return None, "unrecognized"
                
            if data.get('unknown_exercise', False) or data.get('exercise') not in self.get_available_exercises():
                return None, "unknown_exercise"
                
            if not isinstance(data.get('reps', 0), int) or data['reps'] <= 0:
                return None, "invalid_reps"
                
            return data, None
            
        except Exception as e:
            logging.error(f"Помилка парсингу: {str(e)}")
            return None, "unrecognized"
