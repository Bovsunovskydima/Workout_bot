import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import WorkoutHandlers
from database import DatabaseManager
import openai


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('workout_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    
    try:
        bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
        openai.api_key = os.environ["OPENAI_API_KEY"] 
    except KeyError as e:
        logger.error(f"❌ Змінна середовища {e} не задана")
        return

   
    db = DatabaseManager()
    if not db.get_all_exercises():
        logger.info("📋 Таблиця exercises порожня. Заповнюємо типовими вправами.")
        db.populate_default_exercises()

    
    app = Application.builder().token(bot_token).build()
    handlers = WorkoutHandlers()

    
    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_button_press))

    logger.info("✅ Бот запущено й слухає повідомлення...")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
