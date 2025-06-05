from datetime import datetime
import logging
from typing import Dict, Any
from collections import defaultdict

class ReportGenerator:
    def __init__(self):
        pass

    def generate_workout_report(self, workout_data: Dict[str, Any]) -> str:
        try:
            start_time = datetime.fromisoformat(workout_data['start_time'])
            end_time = datetime.fromisoformat(workout_data['end_time'])

            duration = end_time - start_time
            duration_minutes = int(duration.total_seconds() / 60)

            exercises_data = defaultdict(list)
            for exercise_name, reps, weight, set_number in workout_data['sets']:
                exercises_data[exercise_name].append({
                    'reps': reps,
                    'weight': weight if weight is not None else 0,
                    'set_number': set_number
                })

            report = "🏁 Тренування завершено!\n\n"
            report += f"⏱️ Час тренування: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} ({duration_minutes} хв)\n\n"

            if not workout_data['sets']:
                report += "😔 Жодних вправ не зроблено."
                return report

            report += "💪 Ви зробили такі вправи:\n"

            total_sets = 0
            total_reps = 0

            for exercise_name, sets_list in exercises_data.items():
                sets_count = len(sets_list)
                total_sets += sets_count

                exercise_total_reps = sum(s['reps'] for s in sets_list)
                total_reps += exercise_total_reps

                weights = [s['weight'] for s in sets_list]
                avg_weight = sum(weights) / sets_count if sets_count > 0 else 0

                exercise_line = f"- {exercise_name.capitalize()}: підходів - {sets_count}, повторень - {exercise_total_reps}"
                if avg_weight > 0:
                    exercise_line += f" (сер. вага {avg_weight:.1f} кг)"
                exercise_line += "\n"

                report += exercise_line

            report += f"\n🔥 Загалом: підходів - {total_sets}, повторень - {total_reps}"
            return report

        except Exception as e:
            logging.error(f"Помилка генерації звіту: {e}")
            return "❌ Помилка при створенні звіту тренування"


    def format_exercise_confirmation(self, exercise_data: Dict[str, Any]) -> str:
        """Форматує підтвердження додавання вправи"""
        text = f"✅ Додано: {exercise_data['exercise'].capitalize()}"
        text += f", повторень - {exercise_data['reps']}"

        if exercise_data.get('set_number'):
            text += f", номер підхіду - {exercise_data['set_number']}"

        if exercise_data.get('weight'):
            text += f", {exercise_data['weight']} кг"

        return text
