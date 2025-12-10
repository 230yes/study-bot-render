#!/usr/bin/env python3
"""
📚 УЧЕБНЫЙ БОТ - ВЕРСИЯ ДЛЯ RENDER
С выбором устройства и расширенным функционалом
"""

import os
import asyncio
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import threading
import json

# ============ 1. НАСТРОЙКА И FLASK APP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app для Render (обязательно!)
app = Flask(__name__)

# Получаем токен из переменных окружения Render
TOKEN = os.environ.get('BOT_TOKEN', '')
if not TOKEN:
    logger.error("❌ Токен не найден! Добавьте BOT_TOKEN в Environment Variables Render")
    exit()

logger.info(f"✅ Токен получен: {TOKEN[:10]}...")

# База данных пользователей (временная)
user_devices = {}

# ============ 2. ИМПОРТ AIOGRAM ============
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.enums import ParseMode
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    logger.info("✅ Библиотеки aiogram загружены")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    logger.info("📦 Установите: pip install aiogram")
    exit()

# ============ 3. ИНИЦИАЛИЗАЦИЯ БОТА ============
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ============ 4. FLASK РОУТЫ ДЛЯ RENDER ============
@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎓 Учебный Бот</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                max-width: 600px;
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .status {
                color: #4ade80;
                font-size: 1.5em;
                margin: 20px 0;
                padding: 10px;
                background: rgba(74, 222, 128, 0.1);
                border-radius: 10px;
                border: 2px solid #4ade80;
            }
            .btn {
                display: inline-block;
                margin-top: 20px;
                padding: 15px 30px;
                background: #0088cc;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-size: 1.2em;
                transition: all 0.3s;
            }
            .btn:hover {
                background: #006699;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Учебный Бот</h1>
            <div class="status">✅ Активен на Render 24/7</div>
            <p>Telegram бот работает в фоновом режиме</p>
            <a href="https://t.me/Konspekt_help_bot" class="btn" target="_blank">
                📱 Открыть в Telegram
            </a>
            <p style="margin-top: 30px; opacity: 0.8;">
                Платформа: Render.com | Режим: Web Service
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check для Render"""
    return jsonify({"status": "ok", "service": "study-bot"}), 200

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook_handler():
    """Вебхук от Telegram"""
    try:
        update_data = request.json
        update = types.Update(**update_data)
        await dp.feed_update(bot, update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({"status": "error"}), 500

# ============ 5. ФУНКЦИИ ДЛЯ РАЗНЫХ УСТРОЙСТВ ============
def format_for_device(device_type: str, content: str, topic: str) -> str:
    """Форматирование контента под конкретное устройство"""
    if device_type == "phone":
        return f"""📱 <b>Версия для телефона:</b>

{content}

📝 <i>Совет для телефона:</i>
• Используйте режим чтения
• Сохраняйте в заметки
• Делитесь с одногруппниками"""
    
    elif device_type == "pc":
        return f"""💻 <b>Версия для компьютера:</b>

{content}

📝 <i>Совет для ПК:</i>
• Распечатайте материал
• Сохраните в PDF
• Используйте для презентаций"""
    
    elif device_type == "watch":
        return f"""⌚ <b>Версия для часов:</b>

📌 <b>Краткий конспект:</b> {topic}

📝 <i>Совет для часов:</i>
• Просматривайте в транспорте
• Используйте для повторения
• Ставьте напоминания"""
    
    else:  # default
        return content

def generate_content(topic: str, device_type: str = None) -> str:
    """Генерация учебного материала"""
    
    # Базовый контент
    base_content = f"""📚 <b>КОНСПЕКТ: {topic.upper()}</b>

📅 <b>Дата создания:</b> {datetime.now().strftime('%d.%m.%Y')}
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M')}

<b>Структура материала:</b>
1. <b>Введение</b> - актуальность и важность темы
2. <b>Основные понятия</b> - ключевые термины и определения
3. <b>Практическая часть</b> - примеры и применение
4. <b>Выводы</b> - основные итоги и перспективы

<b>Ключевые аспекты:</b>
• Аспект 1: Важная информация по теме
• Аспект 2: Основные принципы и законы
• Аспект 3: Практическое применение в жизни

<b>Рекомендации по изучению:</b>
1. Изучайте постепенно, по частям
2. Делайте пометки и выделяйте главное
3. Повторяйте материал через 24 часа
4. Применяйте на практике

🎯 <b>Для углубленного изучения:</b>
• Найдите дополнительную литературу
• Посмотрите видео-лекции
• Обсудите с преподавателем"""

    # Форматируем под устройство
    if device_type and device_type in ["phone", "pc", "watch"]:
        return format_for_device(device_type, base_content, topic)
    
    return base_content

# ============ 6. КОМАНДЫ БОТА ============
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """Команда /start"""
    user = message.from_user
    user_id = str(user.id)
    
    # Приветствие
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        "🎓 <b>Я — учебный бот-помощник</b>\n\n"
        "<b>📚 Что я умею:</b>\n"
        "• Создавать конспекты по любой теме\n"
        "• Форматировать под ваше устройство\n"
        "• Генерировать структуру для учёбы\n"
        "• Давать советы по эффективному обучению\n\n"
        "<b>📱 Выберите устройство:</b>\n"
        "Используйте /device чтобы настроить отображение\n\n"
        "<b>💡 Как использовать:</b>\n"
        "Просто напишите тему, например:\n"
        "<i>искусственный интеллект</i>\n"
        "<i>квантовая физика</i>\n"
        "<i>история древнего рима</i>\n\n"
        "<b>⚡ Бот работает на Render.com 24/7</b>"
    )
    
    # Предлагаем выбрать устройство
    await device_cmd(message)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """Команда /help"""
    await message.answer(
        "🆘 <b>ПОМОЩЬ ПО БОТУ</b>\n\n"
        "<b>🔧 Основные команды:</b>\n"
        "/start - начать работу с ботом\n"
        "/help - получить эту справку\n"
        "/device - выбрать устройство\n"
        "/status - проверить статус\n\n"
        "<b>🎯 Как получить конспект:</b>\n"
        "1. Выберите устройство командой /device\n"
        "2. Напишите тему для конспекта\n"
        "3. Получите отформатированный материал\n\n"
        "<b>📱 Доступные устройства:</b>\n"
        "• 📱 Телефон - оптимизировано для мобильных\n"
        "• 💻 Компьютер - полная версия для ПК\n"
        "• ⌚ Часы - краткая версия для умных часов\n\n"
        "<b>🚀 Примеры запросов:</b>\n"
        "• математический анализ\n"
        "• программирование на python\n"
        "• философия стоицизма\n"
        "• биология клетки\n\n"
        "<b>⚡ Особенности Render:</b>\n"
        "• Работает 24/7\n"
        "• Быстрые ответы\n"
        "• Автообновление"
    )

@dp.message(Command("device"))
async def device_cmd(message: types.Message):
    """Выбор устройства - инлайн клавиатура"""
    user_id = str(message.from_user.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Телефон", callback_data="device_phone"),
        InlineKeyboardButton(text="💻 Компьютер", callback_data="device_pc"),
    )
    builder.row(
        InlineKeyboardButton(text="⌚ Часы", callback_data="device_watch"),
        InlineKeyboardButton(text="❌ Без оптимизации", callback_data="device_none"),
    )
    
    current_device = user_devices.get(user_id, "не выбрано")
    
    await message.answer(
        f"📱 <b>ВЫБОР УСТРОЙСТВА</b>\n\n"
        f"Текущее устройство: <b>{current_device}</b>\n\n"
        "Выберите устройство, которое вы используете:\n\n"
        "• <b>📱 Телефон</b> - оптимизировано для мобильных экранов\n"
        "• <b>💻 Компьютер</b> - полная версия для больших экранов\n"
        "• <b>⌚ Часы</b> - краткая версия для умных часов\n"
        "• <b>❌ Без оптимизации</b> - стандартный формат\n\n"
        "Это повлияет на формат и длину ответов.",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    """Команда /status"""
    user_id = str(message.from_user.id)
    device = user_devices.get(user_id, "не выбрано")
    
    await message.answer(
        f"📊 <b>СТАТУС СИСТЕМЫ</b>\n\n"
        f"👤 <b>Пользователь:</b> {message.from_user.first_name}\n"
        f"📱 <b>Устройство:</b> {device}\n"
        f"🆔 <b>ID:</b> {user_id}\n\n"
        f"🌐 <b>Платформа:</b> Render.com\n"
        f"⚡ <b>Режим работы:</b> 24/7 Web Service\n"
        f"✅ <b>Статус бота:</b> Активен\n\n"
        f"<i>Все системы работают нормально!</i>"
    )

@dp.callback_query(F.data.startswith("device_"))
async def device_callback(callback: types.CallbackQuery):
    """Обработка выбора устройства"""
    user_id = str(callback.from_user.id)
    device_type = callback.data.replace("device_", "")
    
    device_names = {
        "phone": "📱 Телефон",
        "pc": "💻 Компьютер", 
        "watch": "⌚ Часы",
        "none": "❌ Без оптимизации"
    }
    
    device_name = device_names.get(device_type, "Неизвестно")
    user_devices[user_id] = device_name
    
    await callback.message.edit_text(
        f"✅ <b>Устройство выбрано!</b>\n\n"
        f"Теперь вы используете: <b>{device_name}</b>\n\n"
        f"Все материалы будут оптимизированы для этого устройства.\n\n"
        f"<i>Напишите тему для конспекта, чтобы увидеть изменения!</i>"
    )
    await callback.answer()

# ============ 7. ОБРАБОТКА ТЕМ ============
@dp.message(F.text)
async def handle_text(message: types.Message):
    """Обработка любой текстовой темы"""
    # Пропускаем команды
    if message.text.startswith('/'):
        return
    
    topic = message.text.strip()
    user_id = str(message.from_user.id)
    
    if len(topic) < 2:
        await message.answer("❌ <b>Слишком короткая тема.</b>\nНапишите подробнее, минимум 2 символа.")
        return
    
    # Получаем выбранное устройство
    device_display = user_devices.get(user_id, "не выбрано")
    device_type = None
    if "Телефон" in device_display:
        device_type = "phone"
    elif "Компьютер" in device_display:
        device_type = "pc"
    elif "Часы" in device_display:
        device_type = "watch"
    
    # Статус генерации
    status_msg = await message.answer(
        f"🔄 <b>Генерирую конспект...</b>\n"
        f"Тема: <i>{topic}</i>\n"
        f"Устройство: <b>{device_display}</b>\n\n"
        f"<i>Подбираю оптимальный формат...</i>"
    )
    
    # Имитация обработки
    await asyncio.sleep(1)
    
    # Генерация контента
    content = generate_content(topic, device_type)
    
    # Удаляем статус и отправляем результат
    await status_msg.delete()
    await message.answer(content)
    
    # Дополнительные советы
    if device_type == "phone":
        await message.answer(
            "📱 <b>Совет для телефона:</b>\n"
            "• Используйте режим 'картинка в картинке' для видео\n"
            "• Сохраняйте конспекты в заметках\n"
            "• Делитесь с друзьями через Telegram"
        )
    elif device_type == "pc":
        await message.answer(
            "💻 <b>Совет для компьютера:</b>\n"
            "• Распечатайте материал для удобства\n"
            "• Сохраните в PDF для архива\n"
            "• Используйте для подготовки к экзаменам"
        )
    elif device_type == "watch":
        await message.answer(
            "⌚ <b>Совет для часов:</b>\n"
            "• Просматривайте в транспорте\n"
            "• Используйте для быстрого повторения\n"
            "• Ставьте напоминания о занятиях"
        )
    
    # Предложение улучшить
    await asyncio.sleep(1)
    await message.answer(
        "💡 <b>Хотите улучшить результат?</b>\n\n"
        "Попробуйте:\n"
        "1. Уточнить тему\n"
        "2. Выбрать другое устройство /device\n"
        "3. Запросить другой формат\n\n"
        "<i>Скоро добавлю: PDF экспорт, AI-генерацию, настройки!</i>"
    )

# ============ 8. ЗАПУСК БОТА ============
async def run_bot():
    """Запуск Telegram бота"""
    logger.info("=" * 70)
    logger.info("🚀 УЧЕБНЫЙ БОТ ЗАПУСКАЕТСЯ НА RENDER")
    logger.info("=" * 70)
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"📍 Хостинг: Render.com")
    logger.info(f"🤖 Токен: {TOKEN[:10]}...")
    logger.info("=" * 70)
    logger.info("✅ Бот активен! Ожидание сообщений...")
    logger.info("💡 Напишите /start в Telegram для начала работы")
    logger.info("=" * 70)
    
    # Устанавливаем вебхук
    try:
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'study-bot.onrender.com')}/{TOKEN}"
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
    
    # Ожидаем завершения (никогда не завершится если всё ок)
    await asyncio.Event().wait()

def run_flask():
    """Запуск Flask сервера"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def main():
    """Главная функция запуска"""
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    asyncio.run(run_bot())

# ============ 9. ТОЧКА ВХОДА ============
if __name__ == "__main__":
    # Для локального тестирования можно использовать polling:
    # asyncio.run(dp.start_polling(bot))
    
    # Для Render используем Flask + вебхук
    main()
