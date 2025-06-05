import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import WorkoutHandlers
from database import DatabaseManager  


load_dotenv()


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

    
    db = DatabaseManager()
    
    
    if not db.get_all_exercises():
        logger.info("Таблиця exercises порожня. Виконується заповнення за замовчуванням.")
        db.populate_default_exercises()

    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не знайдено в змінних середовища")
        return

    
    app = Application.builder().token(bot_token).build()
    
    
    handlers = WorkoutHandlers()
    
    
    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    
    
    app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice_message))
    
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_button_press))
    
    
    logger.info("Бот запущено!")
    app.run_polling(allowed_updates=["message"])

if __name__ == '__main__':
    main()
