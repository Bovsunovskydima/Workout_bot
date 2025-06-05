import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database import DatabaseManager
from text_parser import TextParser
from speech_recognition import SpeechRecognizer
from report_generator import ReportGenerator

class WorkoutHandlers:
    def __init__(self):
        self.db = DatabaseManager()
        self.parser = TextParser()
        self.speech_recognizer = SpeechRecognizer()
        self.report_generator = ReportGenerator()

        self.keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("🏁 Старт тренування"), KeyboardButton("⏹️ Стоп тренування")],
            [KeyboardButton("📊 Статистика"), KeyboardButton("❓ Допомога")]
        ], resize_keyboard=True)

    def get_formatted_exercises_list(self):
        exercises = self.db.get_all_exercises()
        formatted_list = '\n• ' + '\n• '.join(ex.capitalize() for ex in exercises)
        return f"📋 Список доступних вправ:{formatted_list}"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db.add_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

        welcome_text = (
            "🏋️‍♂️ Привіт! Я твій персональний щоденник тренувань!\n\n"
            "Що я вмію:\n"
            "• Записувати твої тренування\n"
            "• Розпізнавати голосові повідомлення українською\n"
            "• Створювати детальні звіти\n\n"
            "Щоб почати тренування, натисни кнопку '🏁 Старт тренування'"
        )
        await update.message.reply_text(welcome_text, reply_markup=self.keyboard)

    async def start_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self.db.add_user(telegram_id=user.id)

        if self.db.get_active_workout(user_id):
            await update.message.reply_text(
                "⚡ У вас вже є активне тренування!\n"
                "Говоріть або пишіть вправи, або натисніть '⏹️ Стоп тренування' для завершення."
            )
            return

        workout_id = self.db.start_workout(user_id)
        context.user_data['workout_id'] = workout_id

        
        exercises_list = self.get_formatted_exercises_list()
        
        await update.message.reply_text(
            "🏁 Тренування розпочато!\n\n"
            "Тепер можете додавати вправи:\n"
            "Приклади вводу:\n"
            "'Віджимання, 15 разів, 1 підхід'\n"
            "'Віджимання 15 разів, перший підхід'\n\n"
            f"{exercises_list}\n\n"
            "Для завершення натисніть '⏹️ Стоп тренування'"
        )

    async def stop_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self.db.add_user(telegram_id=user.id)

        workout_id = self.db.get_active_workout(user_id)
        if not workout_id:
            await update.message.reply_text("❌ У вас немає активного тренування.\nСпочатку натисніть '🏁 Старт тренування'")
            return

        workout_data = self.db.finish_workout(workout_id)
        context.user_data.pop('workout_id', None)

        report = self.report_generator.generate_workout_report(workout_data)
        await update.message.reply_text(report)

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self.db.add_user(telegram_id=user.id)

        workout_id = self.db.get_active_workout(user_id)
        if not workout_id:
            await update.message.reply_text("⚠️ Спочатку розпочніть тренування, натиснувши '🏁 Старт тренування'")
            return

        exercise_data = self.parser.parse_exercise_input(update.message.text)
        if not exercise_data:
            await update.message.reply_text(
                "❌ Не можу розпізнати вправу.\n\n"
                "Спробуйте формат:\n"
                "'Виконав(-ла) віджимання, 15 разів, 1 підхід'\n"
                "'Жим лежачи, 12 разів, другий підхід, 80 кг'"
            )
            return

        try:
            self.db.add_set(
                workout_id=workout_id,
                exercise_name=exercise_data['exercise'],
                reps=exercise_data['reps'],
                weight=exercise_data.get('weight'),
                set_number=exercise_data.get('set_number')
            )
            confirmation = self.report_generator.format_exercise_confirmation(exercise_data)
            await update.message.reply_text(confirmation)

        except ValueError as e:
            exercises_list = self.get_formatted_exercises_list()
            await update.message.reply_text(f"{str(e)}\n\n{exercises_list}")

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self.db.add_user(telegram_id=user.id)

        workout_id = self.db.get_active_workout(user_id)
        if not workout_id:
            await update.message.reply_text("⚠️ Спочатку розпочніть тренування, натиснувши '🏁 Старт тренування'")
            return

        processing_msg = await update.message.reply_text("🎤 Обробляю голосове повідомлення...")

        try:
            voice_file = await update.message.voice.get_file()
            ogg_bytes = await voice_file.download_as_bytearray()

            text = self.speech_recognizer.transcribe_audio_sync(ogg_bytes)
            await processing_msg.delete()

            if not text:
                await update.message.reply_text("❌ Не вдалося розпізнати голосове повідомлення. Спробуйте говорити чіткіше.")
                return

            await update.message.reply_text(f"👂 Я почув: \"{text}\"")

            exercise_data = self.parser.parse_exercise_input(text)
            if not exercise_data:
                await update.message.reply_text(
                    "❌ Не можу розпізнати вправу з голосового повідомлення.\n\n"
                    "Спробуйте сказати так:\n"
                    "• 'Зробив(-ла) віджимання 15 разів, перший підхід'\n"
                    "• 'Жим лежачи 12 разів, другий підхід, 80 кілограм'"
                )
                return

            try:
                self.db.add_set(
                    workout_id=workout_id,
                    exercise_name=exercise_data['exercise'],
                    reps=exercise_data['reps'],
                    weight=exercise_data.get('weight'),
                    set_number=exercise_data.get('set_number')
                )

                confirmation = self.report_generator.format_exercise_confirmation(exercise_data)
                await update.message.reply_text(confirmation)

            except ValueError as e:
                exercises_list = self.get_formatted_exercises_list()
                await update.message.reply_text(f"{str(e)}\n\n{exercises_list}")

        except Exception as e:
            logging.error(f"Помилка обробки голосу: {e}", exc_info=True)
            try:
                await processing_msg.delete()
            except:
                pass
            await update.message.reply_text("❌ Виникла помилка при обробці голосового повідомлення. Спробуйте ще раз.")


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        exercises_list = self.get_formatted_exercises_list()
        
        help_text = (
            "🏋️‍♂️ **Як користуватися ботом:**\n\n"
            "1️⃣ Натисніть '🏁 Старт тренування'\n"
            "2️⃣ Додавайте вправи текстом або голосом:\n\n"
            "📝 **Текстові приклади:**\n"
            "• Віджимання, 15 разів, 1 підхід\n"
            "• Виконав жим лежачи, 12 разів, другий підхід, 80 кг\n"
            "• Присідання, 20 разів, третій підхід\n\n"
            "🎤 **Голосові приклади:**\n"
            "• 'Зробив(-ла) віджимання 15 разів, перший підхід'\n"
            "• 'Жим лежачи 12 разів, другий підхід, 80 кілограм'\n\n"
            "3️⃣ Натисніть '⏹️ Стоп тренування' для завершення\n"
            "4️⃣ Отримайте детальний звіт!\n\n"
            f"{exercises_list}\n\n"
            "💡 **Поради:**\n"
            "• Говоріть чітко\n"
            "• Вага не обов'язкова\n"
            "• Можна не вказувати підхід — бот порахує сам"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self.db.add_user(telegram_id=user.id)

        stats = self.db.get_user_statistics(user_id)
        if not stats or stats['total_workouts'] == 0:
            await update.message.reply_text("📊 У вас поки немає завершених тренувань.\nРозпочніть перше тренування! 💪")
            return

        stats_text = (
            f"📊 **Ваша статистика:**\n\n"
            f"🏋️‍♂️ Всього тренувань: {stats['total_workouts']}\n"
            f"💪 Всього підходів: {stats['total_sets']}\n"
            f"🔥 Всього повторень: {stats['total_reps']}\n"
            f"⏱️ Загальний час: {stats['total_time']} хв\n\n"
            f"🏆 **Топ-3 вправи по підходам:**\n"
        )

        for i, (exercise, count) in enumerate(stats['top_exercises'], 1):
            stats_text += f"{i}. {exercise.capitalize()}: {count}\n"

        await update.message.reply_text(stats_text)

    async def handle_button_press(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "🏁 Старт тренування":
            await self.start_workout(update, context)
        elif text == "⏹️ Стоп тренування":
            await self.stop_workout(update, context)
        elif text == "❓ Допомога":
            await self.help_command(update, context)
        elif text == "📊 Статистика":
            await self.show_statistics(update, context)
        else:
            await self.handle_text_message(update, context)