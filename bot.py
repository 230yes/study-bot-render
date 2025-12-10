import os
import asyncio
import logging
import threading
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from flask import Flask
import requests

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Учебный Бот</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .status { color: green; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1>🎓 Учебный Бот</h1>
        <div class="status">✅ Активен на Render 24/7</div>
        <p>Бот работает в фоновом режиме и обрабатывает Telegram сообщения</p>
        <p>Напишите боту в Telegram: <a href="https://t.me/Konspekt_help_bot">@Konspekt_help_bot</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "ok", "service": "study-bot"}, 200

def run_web_server():
    """Запуск веб-сервера"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# ========== TELEGRAM БОТ ==========
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ ОШИБКА: Токен не найден!")
    exit()

logger.info(f"✅ Токен получен: {BOT_TOKEN[:10]}...")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КОМАНДА /START ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "🎓 *УЧЕБНЫЙ БОТ НА RENDER.COM*\n\n"
        "✅ *Работает 24/7*\n"
        "✅ *Быстрые ответы*\n"
        "✅ *Стабильная работа*\n\n"
        "📚 *Что умею:*\n"
        "• Создавать конспекты\n"
        "• Генерировать рефераты\n"
        "• Оптимизировать под устройства\n\n"
        "💡 *Просто напишите тему!*\n"
        "Пример: *искусственный интеллект*",
        parse_mode=ParseMode.MARKDOWN
    )

# ========== КОМАНДА /HELP ==========
@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "🆘 *ПОМОЩЬ ПО БОТУ*\n\n"
        "🔧 *Основные команды:*\n"
        "/start - начать работу\n"
        "/help - эта справка\n\n"
        "🎯 *Как использовать:*\n"
        "1. Напишите тему работы\n"
        "2. Получите структурированный материал\n"
        "3. Используйте для учёбы\n\n"
        "🚀 *Примеры тем:*\n"
        "• Квантовая физика\n"
        "• История Древнего Рима\n"
        "• Философия стоицизма",
        parse_mode=ParseMode.MARKDOWN
    )

# ========== ОБРАБОТКА ТЕМ ==========
@dp.message()
async def handle_topic(message: types.Message):
    """Обработка любой темы"""
    if message.text.startswith('/'):
        return
    
    topic = message.text.strip()
    
    if len(topic) < 2:
        await message.answer("❌ Слишком короткая тема. Напишите подробнее.")
        return
    
    status_message = await message.answer(
        f"🔄 *Генерирую конспект по теме:*\n*{topic}*...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(1)
    
    response = f"""📚 *КОНСПЕКТ: {topic.upper()}*

*Дата создания:* {datetime.now().strftime('%d.%m.%Y %H:%M')}
*Платформа:* Render.com
*Статус:* 🟢 Активен 24/7

*Структура конспекта:*
1. **Введение** - актуальность темы
2. **Основные понятия** - ключевые термины
3. **Исторический контекст** - развитие темы
4. **Современное состояние** - текущие исследования
5. **Практическое применение** - как используется
6. **Выводы** - основные итоги

*Ключевые моменты:*
• Важный аспект 1
• Важный аспект 2  
• Важный аспект 3

💡 *Для более детального конспекта уточните тему.*

🚀 *Бот работает на Render - стабильно и бесплатно!*"""
    
    await status_message.delete()
    await message.answer(response, parse_mode=ParseMode.MARKDOWN)

# ========== ЗАПУСК БОТА ==========
async def run_bot():
    """Запуск Telegram бота"""
    print("=" * 60)
    print("🚀 УЧЕБНЫЙ БОТ ЗАПУСКАЕТСЯ")
    print("=" * 60)
    print(f"⏰ Время запуска: {datetime.now().strftime('%H:%M:%S')}")
    print("📍 Хостинг: Render.com")
    print("=" * 60)
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")

def start_bot():
    """Запуск бота в асинхронном режиме"""
    asyncio.run(run_bot())

def keep_alive():
    """Функция для поддержания активности (ping себя)"""
    import time
    url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}"
    while True:
        try:
            if url and 'render.com' in url:
                requests.get(f"{url}/health", timeout=10)
        except:
            pass
        time.sleep(300)  # Пинг каждые 5 минут

# ========== ГЛАВНЫЙ ЗАПУСК ==========
if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем keep-alive
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Бесконечный цикл для поддержания работы
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Бот завершает работу...")
