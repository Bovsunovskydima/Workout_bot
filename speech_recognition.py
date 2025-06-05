import openai
import logging
import io
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class SpeechRecognizer:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY не знайдено в змінних середовища")
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Розпізнає українське мовлення з аудіо"""
        try:
            
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.ogg"  
            
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uk"  
            )
            
            text = transcript.text.strip()
            logging.info(f"Розпізнано текст: {text}")
            return text
            
        except openai.AuthenticationError:
            logging.error("Помилка автентифікації OpenAI - перевірте API ключ")
            return None
        except openai.RateLimitError:
            logging.error("Перевищено ліміт запитів OpenAI")
            return None
        except openai.APIError as e:
            logging.error(f"Помилка OpenAI API: {e}")
            return None
        except Exception as e:
            logging.error(f"Помилка розпізнавання мовлення: {e}")
            return None

    def transcribe_audio_sync(self, audio_data: bytes) -> Optional[str]:
        """Синхронна версія для простішого використання"""
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.ogg"
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uk"
            )
            
            text = transcript.text.strip()
            logging.info(f"Розпізнано текст: {text}")
            return text
            
        except openai.AuthenticationError:
            logging.error("Помилка автентифікації OpenAI - перевірте API ключ та баланс")
            return None
        except openai.RateLimitError:
            logging.error("Перевищено ліміт запитів OpenAI")
            return None
        except openai.APIError as e:
            logging.error(f"Помилка OpenAI API: {e}")
            return None
        except Exception as e:
            logging.error(f"Помилка розпізнавання мовлення: {e}")
            return None