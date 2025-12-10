import os
import logging
from flask import Flask, request, jsonify
import requests
import time

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "7807343935:AAHmMbpYDssOQaAo1z3AmNEewqER97sGVNU"
PORT = 8080
APP_URL = "study-bot.onrender.com"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== FLASK APP ==========
app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎓 Учебный Бот</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .status { color: green; font-size: 24px; margin: 20px; }
            .btn { 
                display: inline-block; 
                margin-top: 20px; 
                padding: 15px 30px; 
                background: #0088cc; 
                color: white; 
                text-decoration: none; 
                border-radius: 10px; 
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <h1>🎓 Учебный Бот</h1>
        <div class="status">✅ Активен на Render</div>
        <p>Бот работает и готов отвечать!</p>
        <a href="https://t.me/Konspekt_help_bot" class="btn" target="_blank">
            Открыть в Telegram
        </a>
        <p style="margin-top: 30px; color: #666;">
            Платформа: Render.com | Статус: Running
        </p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    try:
        data = request.json
        
        if 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '').strip()
            
            logger.info(f"💬 Сообщение от {chat_id}: {text}")
            
            if text == '/start':
                send_message(chat_id, 
                    "🎓 *УЧЕБНЫЙ БОТ НА RENDER.COM*\n\n"
                    "✅ *Работает 24/7*\n"
                    "✅ *Готов помогать с учёбой*\n\n"
                    "💡 *Напишите тему для конспекта!*\n"
                    "Пример: *искусственный интеллект*"
                )
            elif text == '/help':
                send_message(chat_id,
                    "🆘 *ПОМОЩЬ*\n\n"
                    "/start - начать\n"
                    "/help - справка\n\n"
                    "Просто напишите тему для конспекта!"
                )
            elif len(text) > 1:
                send_message(chat_id,
                    f"📚 *КОНСПЕКТ ПО ТЕМЕ: {text.upper()}*\n\n"
                    "1. *Введение*\n"
                    "2. *Основные понятия*\n"
                    "3. *Ключевые моменты*\n\n"
                    "✅ Бот работает на Render.com"
                )
            else:
                send_message(chat_id, "Напишите тему для конспекта!")
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"status": "error"}), 500

def send_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"📤 Сообщение отправлено")
        else:
            logger.error(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")

def setup_webhook():
    """Установка вебхука"""
    try:
        webhook_url = f"https://{APP_URL}/{BOT_TOKEN}"
        
        # Устанавливаем вебхук
        set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        payload = {"url": webhook_url, "drop_pending_updates": True}
        
        response = requests.post(set_url, json=payload, timeout=10)
        
        if response.json().get('ok'):
            logger.info(f"✅ Вебхук установлен: {webhook_url}")
        else:
            logger.error(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК БОТА")
    logger.info("=" * 60)
    
    # Устанавливаем вебхук
    setup_webhook()
    
    # Запускаем Flask БЕЗ reloader
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        use_reloader=False  # ← ВАЖНО! Отключаем reloader
    )
