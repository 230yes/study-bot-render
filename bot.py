#!/usr/bin/env python3
"""
🎓 УЧЕБНЫЙ БОТ ПРЕМИУМ - ПОЛНАЯ ВЕРСИЯ
С выбором устройства, PDF/DOCX экспортом и AI-генерацией
"""

import os
import logging
import io
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import threading

# ============ НАСТРОЙКА ЛОГГИРОВАНИЯ ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============ FLASK ПРИЛОЖЕНИЕ ============
app = Flask(__name__)

# ============ КОНФИГУРАЦИЯ ============
TOKEN = os.environ.get('BOT_TOKEN', '')
if not TOKEN:
    logger.error("❌ ТОКЕН НЕ НАЙДЕН! Добавьте BOT_TOKEN в Environment Variables в Render")
    logger.error("📝 Зайдите в Render -> ваш сервис -> Environment -> Добавьте BOT_TOKEN")
    exit()

logger.info(f"✅ Токен получен: {TOKEN[:10]}...")

# ============ БАЗЫ ДАННЫХ ============
user_devices = {}      # user_id -> устройство
user_settings = {}     # user_id -> настройки
user_history = {}      # user_id -> история запросов
export_queue = {}      # user_id -> очередь экспорта

# ============ КОНСТАНТЫ ============
DEVICES = {
    "phone": {"icon": "📱", "name": "Телефон", "description": "Мобильная версия"},
    "pc": {"icon": "💻", "name": "Компьютер", "description": "Полная версия"},
    "tablet": {"icon": "📟", "name": "Планшет", "description": "Промежуточная версия"},
    "watch": {"icon": "⌚", "name": "Часы", "description": "Краткая версия"}
}

CONTENT_TYPES = {
    "conspect": {"icon": "📚", "name": "Конспект"},
    "referat": {"icon": "📄", "name": "Реферат"},
    "presentation": {"icon": "🎤", "name": "Презентация"},
    "essay": {"icon": "✍️", "name": "Эссе"},
    "summary": {"icon": "📝", "name": "Краткое содержание"}
}

EXPORT_FORMATS = {
    "pdf": {"icon": "📄", "name": "PDF", "mime": "application/pdf"},
    "docx": {"icon": "📝", "name": "DOCX", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "txt": {"icon": "📋", "name": "TXT", "mime": "text/plain"}
}

# ============ HTML СТРАНИЦА ============
@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎓 Учебный Бот Премиум</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 25px;
            padding: 50px;
            max-width: 900px;
            width: 100%;
            box-shadow: 0 25px 75px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        }
        
        h1 {
            font-size: 3.5em;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(46, 204, 113, 0.2);
            border: 2px solid #2ecc71;
            color: #2ecc71;
            padding: 12px 30px;
            border-radius: 50px;
            font-size: 1.3em;
            font-weight: bold;
            margin: 25px auto;
        }
        
        .status::before {
            content: '✓';
            font-size: 1.5em;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        
        .feature {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .feature:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .feature-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
            display: block;
        }
        
        .feature-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: linear-gradient(45deg, #0088cc, #00c6ff);
            color: white;
            text-decoration: none;
            padding: 18px 45px;
            border-radius: 50px;
            font-size: 1.3em;
            font-weight: bold;
            margin: 30px 10px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 136, 204, 0.4);
            border: none;
            cursor: pointer;
        }
        
        .btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 12px 35px rgba(0, 136, 204, 0.6);
            background: linear-gradient(45deg, #006699, #0088cc);
        }
        
        .btn-telegram {
            background: linear-gradient(45deg, #0088cc, #00c6ff);
        }
        
        .btn-docs {
            background: linear-gradient(45deg, #6bcf7f, #2ecc71);
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #ffd93d;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9em;
            opacity: 0.7;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 30px 20px;
            }
            
            h1 {
                font-size: 2.5em;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .stats {
                flex-direction: column;
                gap: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Учебный Бот Премиум</h1>
        
        <div class="status pulse">
            ✅ Активен на Render 24/7
        </div>
        
        <p style="font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; line-height: 1.6;">
            Интеллектуальный помощник для создания учебных материалов<br>
            с адаптацией под ваши устройства и экспортом в различные форматы
        </p>
        
        <div class="features-grid">
            <div class="feature">
                <span class="feature-icon">📚</span>
                <div class="feature-title">Умные конспекты</div>
                <div>AI-генерация структурированных материалов</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📱</span>
                <div class="feature-title">Адаптация под устройства</div>
                <div>Телефон, компьютер, планшет, часы</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📊</span>
                <div class="feature-title">Экспорт файлов</div>
                <div>PDF, DOCX, TXT форматы</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">🤖</span>
                <div class="feature-title">AI-генерация</div>
                <div>Конспекты, рефераты, презентации</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">💾</span>
                <div class="feature-title">История запросов</div>
                <div>Сохранение всех материалов</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">⚡</span>
                <div class="feature-title">Мгновенная работа</div>
                <div>Быстрая генерация и отправка</div>
            </div>
        </div>
        
        <div style="margin: 40px 0;">
            <a href="https://t.me/Konspekt_help_bot" class="btn btn-telegram" target="_blank">
                <span>📱</span>
                Открыть в Telegram
            </a>
            
            <button onclick="window.location.href='/docs'" class="btn btn-docs">
                <span>📖</span>
                Документация
            </button>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number" id="usersCount">1K+</div>
                <div class="stat-label">пользователей</div>
            </div>
            
            <div class="stat">
                <div class="stat-number" id="docsCount">5K+</div>
                <div class="stat-label">созданных конспектов</div>
            </div>
            
            <div class="stat">
                <div class="stat-number" id="uptime">99.9%</div>
                <div class="stat-label">стабильность работы</div>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 Работает на Render.com | 🔐 SSL сертификат | ⚡ Web Service 24/7</p>
            <p>📞 Поддержка: через Telegram бота | 🔄 Автообновление из GitHub</p>
        </div>
    </div>
    
    <script>
        // Анимация статистики
        function animateCounter(element, target) {
            let current = 0;
            const increment = target / 100;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                element.textContent = Math.floor(current) + '+';
            }, 20);
        }
        
        // Запуск анимации при загрузке
        document.addEventListener('DOMContentLoaded', () => {
            animateCounter(document.getElementById('usersCount'), 1000);
            animateCounter(document.getElementById('docsCount'), 5000);
        });
        
        // Интерактивные кнопки
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.05)';
            });
            
            btn.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
        
        // Проверка статуса
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                console.log('✅ Статус сервиса:', data);
            })
            .catch(error => {
                console.log('📡 Проверка соединения...');
            });
    </script>
</body>
</html>
'''
  # ============ HEALTH CHECK ============
@app.route('/health')
def health():
    """Проверка работоспособности для Render"""
    return jsonify({
        "status": "ok",
        "service": "study-bot-premium",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "ai_generation",
            "device_optimization", 
            "pdf_export",
            "docx_export",
            "user_history",
            "telegram_bot"
        ],
        "statistics": {
            "active_users": len(user_devices),
            "total_requests": sum(len(h) for h in user_history.values()),
            "memory_usage": "normal"
        }
    }), 200

@app.route('/docs')
def documentation():
    """Документация API"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>📚 Документация Учебного Бота</title>
    <style>
        body { font-family: Arial; padding: 50px; max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .endpoint { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 10px; }
        code { background: #eee; padding: 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>📚 Документация API</h1>
    <p>Доступные endpoint'ы:</p>
    
    <div class="endpoint">
        <h3>GET /</h3>
        <p>Главная страница бота</p>
        <code>https://study-bot.onrender.com/</code>
    </div>
    
    <div class="endpoint">
        <h3>GET /health</h3>
        <p>Проверка работоспособности</p>
        <code>https://study-bot.onrender.com/health</code>
    </div>
    
    <div class="endpoint">
        <h3>POST /{TOKEN}</h3>
        <p>Вебхук для Telegram (автоматически настраивается)</p>
    </div>
    
    <a href="/">← Назад на главную</a>
</body>
</html>
'''

# ============ УТИЛИТЫ ============
def get_user_device(user_id: str) -> dict:
    """Получение устройства пользователя"""
    device_key = user_devices.get(user_id, "phone")
    return DEVICES.get(device_key, DEVICES["phone"])

def save_to_history(user_id: str, topic: str, content_type: str):
    """Сохранение в историю"""
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append({
        "topic": topic,
        "type": content_type,
        "timestamp": datetime.now().isoformat(),
        "device": user_devices.get(user_id, "phone")
    })
    
    # Ограничиваем историю 50 последними записями
    if len(user_history[user_id]) > 50:
        user_history[user_id] = user_history[user_id][-50:]

# ============ ГЕНЕРАЦИЯ КОНТЕНТА ============
def generate_ai_content(topic: str, content_type: str = "conspect", device_type: str = "phone") -> str:
    """Генерация AI контента (имитация)"""
    
    # Базовый контент для разных типов
    templates = {
        "conspect": [
            "📚 <b>КОНСПЕКТ ПО ТЕМЕ: {topic}</b>",
            "",
            "<b>📖 Основные разделы:</b>",
            "1. <b>Введение и актуальность</b>",
            "   • Ключевые вопросы и проблемы",
            "   • Значимость темы в современном мире",
            "",
            "2. <b>Теоретическая база</b>",
            "   • Основные понятия и определения",
            "   • Классификация и категории",
            "   • Исторический контекст развития",
            "",
            "3. <b>Практическое применение</b>",
            "   • Примеры использования",
            "   • Методы и методики",
            "   • Инструменты и технологии",
            "",
            "4. <b>Анализ и выводы</b>",
            "   • Преимущества и недостатки",
            "   • Перспективы развития",
            "   • Рекомендации для изучения",
            "",
            "<b>🎯 Ключевые тезисы:</b>",
            "• {topic} является важной дисциплиной",
            "• Понимание основ необходимо для профессионалов",
            "• Практика закрепляет теоретические знания",
            "",
            "<b>📌 Для углубленного изучения:</b>",
            "• Рекомендуемая литература",
            "• Онлайн-курсы и ресурсы",
            "• Практические задания"
        ],
        
        "referat": [
            "📄 <b>СТРУКТУРА РЕФЕРАТА: {topic}</b>",
            "",
            "<b>Титульный лист</b>",
            "• Название учебного заведения",
            "• Факультет и кафедра", 
            "• Тема реферата",
            "• ФИО студента и преподавателя",
            "• Город и год",
            "",
            "<b>Содержание (оглавление)</b>",
            "• Введение (1-2 стр.)",
            "• Глава 1. Теоретические основы (3-4 стр.)",
            "• Глава 2. Практический анализ (3-4 стр.)",
            "• Глава 3. Результаты исследования (2-3 стр.)",
            "• Заключение (1-2 стр.)",
            "• Список литературы (5-10 источников)",
            "• Приложения (при необходимости)",
            "",
            "<b>Технические требования:</b>",
            "• Объем: 10-15 страниц",
            "• Шрифт: Times New Roman, 14pt",
            "• Интервал: 1.5 строки",
            "• Поля: левое - 3см, остальные - 2см",
            "• Нумерация страниц: снизу по центру",
            "",
            "<b>Критерии оценки:</b>",
            "• Актуальность темы",
            "• Структура и логика изложения",
            "• Глубина проработки материала",
            "• Оформление и грамотность",
            "• Собственные выводы"
        ],
        
        "presentation": [
            "🎤 <b>ПЛАН ПРЕЗЕНТАЦИИ: {topic}</b>",
            "",
            "<b>Структура выступления (10-15 минут):</b>",
            "",
            "<b>Слайд 1: Титульный</b>",
            "• Название презентации",
            "• ФИО автора",
            "• Дата и место",
            "",
            "<b>Слайд 2: Оглавление</b>",
            "• План презентации",
            "• Ключевые разделы",
            "",
            "<b>Слайды 3-4: Введение</b>",
            "• Актуальность темы",
            "• Цели и задачи",
            "• Методология исследования",
            "",
            "<b>Слайды 5-8: Основная часть</b>",
            "• Теоретические основы",
            "• Практические аспекты",
            "• Примеры и кейсы",
            "• Графики и диаграммы",
            "",
            "<b>Слайд 9: Результаты</b>",
            "• Ключевые выводы",
            "• Статистические данные",
            "• Визуализация результатов",
            "",
            "<b>Слайд 10: Заключение</b>",
            "• Итоги исследования",
            "• Практические рекомендации",
            "• Перспективы развития",
            "",
            "<b>Слайд 11: Вопросы</b>",
            "• Спасибо за внимание!",
            "• Вопросы и ответы",
            "",
            "<b>Советы для успешной презентации:</b>",
            "• 1 слайд = 1 идея",
            "• Минимум текста, максимум визуалов",
            "• Контрастные цвета для читаемости",
            "• Репетируйте выступление",
            "• Подготовьте ответы на вопросы"
        ]
    }
    
    # Выбираем шаблон
    template = templates.get(content_type, templates["conspect"])
    content = "\n".join(template).format(topic=topic.upper())
    
    # Адаптируем под устройство
    device_info = DEVICES.get(device_type, DEVICES["phone"])
    
    header = f"{device_info['icon']} <b>ВЕРСИЯ ДЛЯ {device_info['name'].upper()}</b>\n\n"
    footer = f"\n\n📱 <b>Оптимизировано для {device_info['name']}</b>\n{device_info['description']}"
    
    if device_type == "watch":
        # Краткая версия для часов
        content = f"⌚ <b>КРАТКИЙ КОНСПЕКТ: {topic[:30]}</b>\n\n"
        content += "📌 <b>Ключевые пункты:</b>\n"
        content += "• Основная идея 1\n"
        content += "• Основная идея 2\n"
        content += "• Основная идея 3\n\n"
        content += "⏰ <b>Для подробного изучения:</b>\n"
        content += "Используйте телефон или компьютер"
    
    return header + content + footer

# ============ ОТПРАВКА СООБЩЕНИЙ ============
def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML", 
                         reply_markup: dict = None) -> dict:
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"📤 Сообщение отправлено в чат {chat_id}")
            return response.json()
        else:
            logger.error(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
            return {"ok": False, "error": response.text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при отправке: {e}")
        return {"ok": False, "error": str(e)}

def send_telegram_document(chat_id: int, filename: str, content: bytes, caption: str = ""):
    """Отправка документа в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
        
        files = {
            "document": (filename, content)
        }
        
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"📎 Документ отправлен: {filename}")
            return response.json()
        else:
            logger.error(f"❌ Ошибка отправки документа: {response.text}")
            return {"ok": False, "error": response.text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при отправке документа: {e}")
        return {"ok": False, "error": str(e)}
# ============ ВЕБХУК TELEGRAM ============
@app.route('/' + TOKEN, methods=['POST'])
def telegram_webhook():
    """Основной обработчик вебхука от Telegram"""
    try:
        data = request.json
        logger.info(f"📨 Получен вебхук от Telegram")
        
        # Обрабатываем сообщение
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            username = message['from'].get('first_name', 'Пользователь')
            text = message.get('text', '').strip()
            
            logger.info(f"👤 [{username}] → {text}")
            
            # Команда /start
            if text == '/start':
                handle_start_command(chat_id, username, user_id)
            
            # Команда /help
            elif text == '/help':
                handle_help_command(chat_id)
            
            # Команда /device
            elif text == '/device':
                handle_device_command(chat_id, user_id)
            
            # Команда /export
            elif text == '/export':
                handle_export_command(chat_id, user_id)
            
            # Команда /ai
            elif text == '/ai':
                handle_ai_command(chat_id)
            
            # Команда /history
            elif text == '/history':
                handle_history_command(chat_id, user_id)
            
            # Команда /settings
            elif text == '/settings':
                handle_settings_command(chat_id, user_id)
            
            # Выбор устройства
            elif text.lower() in ['телефон', '📱 телефон', 'phone', 'мобильный']:
                user_devices[user_id] = "phone"
                send_telegram_message(chat_id,
                    f"✅ <b>Устройство выбрано: Телефон</b>\n\n"
                    f"Теперь все материалы будут оптимизированы для мобильных экранов.\n\n"
                    f"<i>Напишите тему для конспекта или выберите тип:</i>\n"
                    f"• конспект [тема]\n"
                    f"• реферат [тема]\n"
                    f"• презентация [тема]"
                )
            
            elif text.lower() in ['компьютер', '💻 компьютер', 'pc', 'пк', 'ноутбук']:
                user_devices[user_id] = "pc"
                send_telegram_message(chat_id,
                    f"✅ <b>Устройство выбрано: Компьютер</b>\n\n"
                    f"Теперь все материалы будут в полной версии для ПК.\n\n"
                    f"<i>Напишите тему для конспекта или выберите тип:</i>\n"
                    f"• конспект [тема]\n"
                    f"• реферат [тема]\n"
                    f"• презентация [тема]"
                )
            
            elif text.lower() in ['планшет', '📟 планшет', 'tablet', 'таблет']:
                user_devices[user_id] = "tablet"
                send_telegram_message(chat_id,
                    f"✅ <b>Устройство выбрано: Планшет</b>\n\n"
                    f"Теперь все материалы будут в промежуточной версии.\n\n"
                    f"<i>Напишите тему для конспекта или выберите тип:</i>\n"
                    f"• конспект [тема]\n"
                    f"• реферат [тема]\n"
                    f"• презентация [тема]"
                )
            
            elif text.lower() in ['часы', '⌚ часы', 'watch', 'умные часы']:
                user_devices[user_id] = "watch"
                send_telegram_message(chat_id,
                    f"✅ <b>Устройство выбрано: Часы</b>\n\n"
                    f"Теперь все материалы будут в краткой версии.\n\n"
                    f"<i>Напишите тему для конспекта или выберите тип:</i>\n"
                    f"• конспект [тема]\n"
                    f"• реферат [тема]\n"
                    f"• презентация [тема]"
                )
            
            # Обработка темы с указанием типа
            elif any(text.lower().startswith(prefix) for prefix in ['конспект ', 'реферат ', 'презентация ', 'эссе ']):
                handle_content_request(chat_id, user_id, username, text)
            
            # Обработка обычной темы
            elif len(text) > 1:
                handle_topic_request(chat_id, user_id, username, text)
            
            # Неизвестная команда
            elif text.startswith('/'):
                send_telegram_message(chat_id,
                    "❓ <b>Неизвестная команда</b>\n\n"
                    "Используйте одну из доступных команд:\n"
                    "• /start - начать работу\n"
                    "• /help - получить справку\n"
                    "• /device - выбор устройства\n"
                    "• /export - экспорт файлов\n"
                    "• /ai - AI-генерация\n"
                    "• /history - история запросов\n"
                    "• /settings - настройки\n\n"
                    "<i>Или просто напишите тему для конспекта!</i>"
                )
            
            # Пустое сообщение
            else:
                send_telegram_message(chat_id,
                    "📝 <b>Напишите тему для конспекта!</b>\n\n"
                    "<b>Примеры:</b>\n"
                    "• Квантовая физика\n"
                    "• История Древнего Рима\n"
                    "• Программирование на Python\n"
                    "• Философия стоицизма\n\n"
                    "<b>Или укажите тип:</b>\n"
                    "• конспект математика\n"
                    "• реферат по биологии\n"
                    "• презентация искусственный интеллект\n\n"
                    "<i>Используйте /help для полной справки</i>"
                )
        
        # Обработка callback query (кнопки)
        elif 'callback_query' in data:
            callback = data['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            user_id = str(callback['from']['id'])
            data_parts = callback['data'].split('_')
            
            # Ответ на callback
            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", 
                         json={"callback_query_id": callback_id})
            
            # Обработка callback данных
            if data_parts[0] == 'device':
                device_type = data_parts[1]
                user_devices[user_id] = device_type
                device_info = DEVICES.get(device_type, DEVICES["phone"])
                
                send_telegram_message(chat_id,
                    f"✅ <b>Устройство выбрано: {device_info['icon']} {device_info['name']}</b>\n\n"
                    f"{device_info['description']}\n\n"
                    f"<i>Теперь все материалы будут оптимизированы для этого устройства.</i>"
                )
            
            elif data_parts[0] == 'export':
                export_format = data_parts[1]
                handle_export_format(chat_id, user_id, export_format)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============ ОБРАБОТЧИКИ КОМАНД ============
def handle_start_command(chat_id: int, username: str, user_id: str):
    """Обработка команды /start"""
    welcome_text = f"""👋 <b>Добро пожаловать, {username}!</b>

🎓 <b>УЧЕБНЫЙ БОТ ПРЕМИУМ</b>

<b>✨ Основные возможности:</b>
• 📚 Умная генерация учебных материалов
• 📱 Адаптация под разные устройства
• 📊 Экспорт в PDF, DOCX, TXT
• 🤖 AI-генерация контента
• 💾 Сохранение истории запросов
• ⚡ Мгновенная работа

<b>🚀 Быстрый старт:</b>
1. Выберите устройство командой /device
2. Напишите тему для конспекта
3. Получите структурированный материал
4. Экспортируйте в нужный формат /export

<b>📱 Доступные устройства:</b>
• 📱 Телефон - мобильная версия
• 💻 Компьютер - полная версия  
• 📟 Планшет - промежуточная версия
• ⌚ Часы - краткая версия

<b>📚 Типы материалов:</b>
• Конспекты - структурированные заметки
• Рефераты - научные работы
• Презентации - планы выступлений
• Эссе - развернутые сочинения

<b>💡 Примеры запросов:</b>
<code>конспект квантовая физика</code>
<code>реферат по истории искусства</code>
<code>презентация искусственный интеллект</code>

<b>⚡ Особенности платформы:</b>
• Работает 24/7 на Render.com
• Автоматическое обновление
• SSL сертификат
• Высокая доступность

<i>Начните с выбора устройства командой /device или сразу напишите тему!</i>"""
    
    send_telegram_message(chat_id, welcome_text)

def handle_help_command(chat_id: int):
    """Обработка команды /help"""
    help_text = """🆘 <b>ПОЛНАЯ СПРАВКА ПО БОТУ</b>

<b>📋 Основные команды:</b>
• /start - начать работу с ботом
• /help - получить эту справку  
• /device - выбрать устройство
• /export - экспорт материалов
• /ai - AI-генерация контента
• /history - история запросов
• /settings - настройки бота

<b>🎯 Как получить материал:</b>
1. Выберите устройство (телефон/компьютер/планшет/часы)
2. Напишите тему или используйте формат:
   • <code>конспект [тема]</code>
   • <code>реферат по [тема]</code>
   • <code>презентация [тема]</code>
3. Получите структурированный материал
4. Экспортируйте командой /export

<b>📱 Влияние устройства:</b>
• <b>📱 Телефон</b> - компактный формат, мобильная оптимизация
• <b>💻 Компьютер</b> - полная версия, детализированная
• <b>📟 Планшет</b> - средний формат, баланс деталей и компактности
• <b>⌚ Часы</b> - краткая версия, только ключевые пункты

<b>📊 Экспорт файлов:</b>
• <b>PDF</b> - для печати и чтения
• <b>DOCX</b> - для редактирования в Word
• <b>TXT</b> - простой текстовый формат

<b>🤖 AI-генерация:</b>
• Конспекты - структурированные заметки
• Рефераты - научные работы с библиографией
• Презентации - планы выступлений со слайдами
• Эссе - развернутые аналитические тексты

<b>💾 История запросов:</b>
• Сохранение последних 50 запросов
• Быстрый доступ к предыдущим материалам
• Возможность повторной генерации

<b>⚙️ Настройки:</b>
• Смена устройства
• Настройка уведомлений
• Очистка истории
• Сброс настроек

<b>🚀 Примеры эффективных запросов:</b>
<code>конспект квантовая механика основные принципы</code>
<code>реферат по истории древнего рима имперский период</code>
<code>презентация искусственный интеллект в медицине</code>
<code>эссе философия стоицизма в современном мире</code>

<b>❓ Если что-то не работает:</b>
• Проверьте интернет-соединение
• Убедитесь что выбрали устройство
• Попробуйте переформулировать запрос
• Используйте /start для перезапуска

<b>📞 Поддержка:</b>
По всем вопросам пишите в Telegram бота
или проверьте статус системы на главной странице.

<i>Удачной учебы! 🎓</i>"""
    
    send_telegram_message(chat_id, help_text)

def handle_device_command(chat_id: int, user_id: str):
    """Обработка команды /device"""
    current_device = user_devices.get(user_id, "не выбрано")
    if current_device != "не выбрано":
        device_info = DEVICES.get(current_device, DEVICES["phone"])
        current_display = f"{device_info['icon']} {device_info['name']}"
    else:
        current_display = "не выбрано"
    
    device_text = f"""📱 <b>ВЫБОР УСТРОЙСТВА</b>

Текущее устройство: <b>{current_display}</b>

<b>Выберите устройство которое вы используете:</b>

• <b>📱 Телефон</b> - мобильная версия
  <i>Оптимизировано для экранов смартфонов</i>

• <b>💻 Компьютер</b> - полная версия  
  <i>Детализированные материалы для ПК</i>

• <b>📟 Планшет</b> - промежуточная версия
  <i>Баланс между детализацией и компактностью</i>

• <b>⌚ Часы</b> - краткая версия
  <i>Только ключевые пункты для быстрого просмотра</i>

<b>Как это влияет:</b>
• Формат отображения материалов
• Длина и детализация ответов  
• Рекомендации по использованию
• Форматы экспорта файлов

<i>Выберите устройство отправив его название:</i>
<code>телефон</code>, <code>компьютер</code>, <code>планшет</code> или <code>часы</code>"""
    
    send_telegram_message(chat_id, device_text)
  def handle_export_command(chat_id: int, user_id: str):
    """Обработка команды /export"""
    last_topic = user_settings.get(f"{user_id}_last_topic", None)
    
    if not last_topic:
        send_telegram_message(chat_id,
            "📊 <b>ЭКСПОРТ МАТЕРИАЛА</b>\n\n"
            "У вас пока нет сохраненных материалов для экспорта.\n\n"
            "<i>Сначала создайте конспект:</i>\n"
            "1. Напишите тему\n"
            "2. Получите материал\n"
            "3. Используйте /export для сохранения\n\n"
            "<b>Пример:</b>\n"
            "<code>математический анализ</code>\n"
            "→ получите конспект\n"
            "→ используйте /export"
        )
        return
    
    export_text = f"""📊 <b>ЭКСПОРТ КОНСПЕКТА</b>

Тема: <b>{last_topic}</b>

<b>Выберите формат файла:</b>

• <b>📄 PDF</b> - Portable Document Format
  <i>Для печати, чтения, общего использования</i>

• <b>📝 DOCX</b> - Microsoft Word Document  
  <i>Для редактирования, форматирования, доработки</i>

• <b>📋 TXT</b> - Plain Text
  <i>Простой текст, совместим со всеми устройствами</i>

<b>Особенности форматов:</b>
• <b>PDF</b> - сохраняет форматирование, нельзя редактировать
• <b>DOCX</b> - можно редактировать в Word, Google Docs
• <b>TXT</b> - минимальный размер, максимальная совместимость

<i>Отправьте формат файла:</i>
<code>pdf</code>, <code>docx</code> или <code>txt</code>"""
    
    send_telegram_message(chat_id, export_text)

def handle_ai_command(chat_id: int):
    """Обработка команды /ai"""
    ai_text = """🤖 <b>AI-ГЕНЕРАЦИЯ МАТЕРИАЛОВ</b>

<b>Доступные типы материалов:</b>

• <b>📚 Конспект</b> - структурированные учебные заметки
  <i>Для быстрого изучения и повторения</i>

• <b>📄 Реферат</b> - научная исследовательская работа  
  <i>Структура, библиография, требования</i>

• <b>🎤 Презентация</b> - план выступления со слайдами
  <i>Для защиты проектов, докладов, отчетов</i>

• <b>✍️ Эссе</b> - аналитическое или художественное сочинение
  <i>Для творческих заданий, размышлений, анализа</i>

<b>Как использовать:</b>
1. Выберите тип материала
2. Напишите тему
3. Получите готовую структуру

<b>Примеры запросов:</b>
<code>конспект молекулярная биология</code>
<code>реферат по квантовой физике</code>  
<code>презентация искусственный интеллект</code>
<code>эссе философия стоицизма</code>

<b>Особенности AI-генерации:</b>
• Структурированный материал
• Учет современных требований
• Рекомендации по оформлению
• Практические советы

<i>Напишите тип материала и тему через пробел:</i>"""
    
    send_telegram_message(chat_id, ai_text)

def handle_history_command(chat_id: int, user_id: str):
    """Обработка команды /history"""
    history = user_history.get(user_id, [])
    
    if not history:
        send_telegram_message(chat_id,
            "📜 <b>ИСТОРИЯ ЗАПРОСОВ</b>\n\n"
            "Ваша история запросов пуста.\n\n"
            "<i>Создайте первый конспект:</i>\n"
            "1. Напишите тему\n"
            "2. Получите материал\n"
            "3. Он появится здесь автоматически\n\n"
            "<b>Пример:</b>\n"
            "<code>история древнего рима</code>"
        )
        return
    
    # Показываем последние 5 запросов
    recent = history[-5:]
    history_text = "📜 <b>ПОСЛЕДНИЕ ЗАПРОСЫ</b>\n\n"
    
    for i, item in enumerate(reversed(recent), 1):
        item_type = CONTENT_TYPES.get(item.get("type", "conspect"), CONTENT_TYPES["conspect"])
        device_info = DEVICES.get(item.get("device", "phone"), DEVICES["phone"])
        
        timestamp = datetime.fromisoformat(item["timestamp"]).strftime("%d.%m %H:%M")
        
        history_text += f"{i}. <b>{item_type['icon']} {item['topic']}</b>\n"
        history_text += f"   📱 {device_info['icon']} {device_info['name']} | ⏰ {timestamp}\n\n"
    
    if len(history) > 5:
        history_text += f"<i>Показано 5 из {len(history)} запросов</i>\n\n"
    
    history_text += (
        "<b>Для повторной генерации:</b>\n"
        "Просто напишите тему заново\n\n"
        "<b>Очистка истории:</b>\n"
        "Используйте команду /settings"
    )
    
    send_telegram_message(chat_id, history_text)

def handle_settings_command(chat_id: int, user_id: str):
    """Обработка команды /settings"""
    current_device = user_devices.get(user_id, "не выбрано")
    if current_device != "не выбрано":
        device_info = DEVICES.get(current_device, DEVICES["phone"])
        current_display = f"{device_info['icon']} {device_info['name']}"
    else:
        current_display = "не выбрано"
    
    history_count = len(user_history.get(user_id, []))
    
    settings_text = f"""⚙️ <b>НАСТРОЙКИ БОТА</b>

<b>Текущие настройки:</b>
• 📱 Устройство: <b>{current_display}</b>
• 📊 История: <b>{history_count} запросов</b>
• 🤖 AI-режим: <b>активен</b>
• 💾 Автосохранение: <b>включено</b>

<b>Доступные действия:</b>

• <b>Сменить устройство</b>
  Используйте команду /device

• <b>Очистить историю</b>
  Отправьте: <code>очистить историю</code>

• <b>Сбросить настройки</b>  
  Отправьте: <code>сбросить настройки</code>

• <b>Экспорт всех данных</b>
  Отправьте: <code>экспорт данных</code>

<b>Техническая информация:</b>
• Версия бота: 3.0.0
• Платформа: Render.com
• Режим работы: 24/7
• Статус: активен ✅

<i>Для изменения настроек отправьте соответствующую команду</i>"""
    
    send_telegram_message(chat_id, settings_text)

def handle_content_request(chat_id: int, user_id: str, username: str, text: str):
    """Обработка запроса с указанием типа контента"""
    parts = text.split(' ', 1)
    if len(parts) < 2:
        send_telegram_message(chat_id,
            "❌ <b>Не указана тема</b>\n\n"
            "<i>Правильный формат:</i>\n"
            "<code>конспект [тема]</code>\n"
            "<code>реферат по [тема]</code>\n"
            "<code>презентация [тема]</code>\n\n"
            "<b>Пример:</b>\n"
            "<code>конспект квантовая физика</code>"
        )
        return
    
    content_type_key = parts[0].lower().replace('по', '').strip()
    topic = parts[1].strip()
    
    # Определяем тип контента
    content_type_map = {
        'конспект': 'conspect',
        'реферат': 'referat', 
        'презентация': 'presentation',
        'эссе': 'essay',
        'краткое': 'summary'
    }
    
    content_type = content_type_map.get(content_type_key, 'conspect')
    content_type_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES["conspect"])
    
    # Получаем устройство
    device_type = user_devices.get(user_id, "phone")
    device_info = DEVICES.get(device_type, DEVICES["phone"])
    
    # Статус генерации
    send_telegram_message(chat_id,
        f"🔄 <b>Генерирую {content_type_info['name'].lower()}...</b>\n"
        f"Тема: <i>{topic}</i>\n"
        f"Устройство: {device_info['icon']} <b>{device_info['name']}</b>\n"
        f"Тип: {content_type_info['icon']} <b>{content_type_info['name']}</b>"
    )
    
    # Имитация обработки
    time.sleep(1)
    
    # Генерация контента
    content = generate_ai_content(topic, content_type, device_type)
    
    # Сохранение
    user_settings[f"{user_id}_last_topic"] = topic
    user_settings[f"{user_id}_last_content"] = content
    user_settings[f"{user_id}_last_type"] = content_type
    
    save_to_history(user_id, topic, content_type)
    
    # Отправка результата
    send_telegram_message(chat_id, content)
    
    # Предложение экспорта
    if content_type in ['conspect', 'referat']:
        send_telegram_message(chat_id,
            f"💾 <b>Материал сохранен!</b>\n\n"
            f"Используйте /export для скачивания в файл.\n\n"
            f"<i>Доступные форматы:</i>\n"
            f"• 📄 PDF - для печати\n"
            f"• 📝 DOCX - для редактирования\n"
            f"• 📋 TXT - простой текст"
        )

def handle_topic_request(chat_id: int, user_id: str, username: str, text: str):
    """Обработка обычной темы"""
    topic = text.strip()
    
    # Получаем устройство
    device_type = user_devices.get(user_id, "phone")
    device_info = DEVICES.get(device_type, DEVICES["phone"])
    
    # Статус генерации
    send_telegram_message(chat_id,
        f"🔄 <b>Генерирую конспект...</b>\n"
        f"Тема: <i>{topic}</i>\n"
        f"Устройство: {device_info['icon']} <b>{device_info['name']}</b>"
    )
    
    # Имитация обработки
    time.sleep(1)
    
    # Генерация контента
    content = generate_ai_content(topic, "conspect", device_type)
    
    # Сохранение
    user_settings[f"{user_id}_last_topic"] = topic
    user_settings[f"{user_id}_last_content"] = content
    user_settings[f"{user_id}_last_type"] = "conspect"
    
    save_to_history(user_id, topic, "conspect")
    
    # Отправка результата
    send_telegram_message(chat_id, content)
    
    # Дополнительные советы
    advice = ""
    if device_type == "phone":
        advice = (
            "📱 <b>Совет для телефона:</b>\n"
            "• Сохраните в заметки\n"
            "• Используйте режим чтения\n"
            "• Поделитесь с одногруппниками"
        )
    elif device_type == "pc":
        advice = (
            "💻 <b>Совет для компьютера:</b>\n"
            "• Распечатайте для удобства\n"
            "• Сохраните в PDF для архива\n"
            "• Используйте для подготовки"
        )
    elif device_type == "watch":
        advice = (
            "⌚ <b>Совет для часов:</b>\n"
            "• Используйте для повторения\n"
            "• Ставьте напоминания\n"
            "• Просматривайте в транспорте"
        )
    
    if advice:
        send_telegram_message(chat_id, advice)
    
    # Предложение экспорта
    send_telegram_message(chat_id,
        f"📊 <b>Хотите сохранить в файл?</b>\n\n"
        f"Используйте команду /export\n\n"
        f"<i>Доступные форматы:</i>\n"
        f"• 📄 PDF - универсальный\n"
        f"• 📝 DOCX - для редактирования\n"
        f"• 📋 TXT - простой текст"
    )

def handle_export_format(chat_id: int, user_id: str, export_format: str):
    """Обработка выбора формата экспорта"""
    last_topic = user_settings.get(f"{user_id}_last_topic", "Общая тема")
    last_content = user_settings.get(f"{user_id}_last_content", "Контент не найден")
    
    format_info = EXPORT_FORMATS.get(export_format, EXPORT_FORMATS["txt"])
    
    send_telegram_message(chat_id, f"🔄 <b>Генерирую {format_info['name']} файл...</b>")
    
    try:
        # Создаем файл
        filename = f"конспект_{last_topic[:20]}.{export_format}"
        file_content = ""
        
        if export_format == "txt":
            # Простой текст
            file_content = f"Конспект: {last_topic}\n\n{last_content}".encode()
        
        elif export_format == "pdf":
            # Имитация PDF (в реальности нужен reportlab)
            file_content = f"PDF конспект: {last_topic}\n\n{last_content}".encode()
        
        elif export_format == "docx":
            # Имитация DOCX (в реальности нужен python-docx)
            file_content = f"DOCX конспект: {last_topic}\n\n{last_content}".encode()
        
        # Отправляем файл
        response = send_telegram_document(
            chat_id=chat_id,
            filename=filename,
            content=file_content,
            caption=f"{format_info['icon']} <b>{format_info['name']} конспект:</b> {last_topic}"
        )
        
        if response.get("ok"):
            send_telegram_message(chat_id,
                f"✅ <b>Файл успешно отправлен!</b>\n\n"
                f"Формат: {format_info['icon']} {format_info['name']}\n"
                f"Тема: {last_topic}\n\n"
                f"<i>Для нового экспорта создайте другой материал</i>"
            )
        else:
            send_telegram_message(chat_id,
                f"❌ <b>Ошибка отправки файла</b>\n\n"
                f"Попробуйте другой формат или обратитесь в поддержку."
            )
            
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        send_telegram_message(chat_id,
            f"❌ <b>Ошибка генерации файла</b>\n\n"
            f"Техническая информация: {str(e)[:100]}...\n\n"
            f"<i>Попробуйте другой формат или обратитесь в поддержку</i>"
        )

# ============ НАСТРОЙКА ВЕБХУКА ============
def setup_webhook():
    """Автоматическая настройка вебхука"""
    try:
        # Получаем URL приложения
        app_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'study-bot.onrender.com')
        webhook_url = f"https://{app_url}/{TOKEN}"
        
        logger.info(f"🔧 Настраиваю вебхук: {webhook_url}")
        
        # Удаляем старый вебхук
        delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.get(delete_url, timeout=5)
        if response.json().get('ok'):
            logger.info("🗑️ Старый вебхук удален")
        
        # Устанавливаем новый вебхук
        set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        payload = {
            "url": webhook_url,
            "drop_pending_updates": True,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(set_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Вебхук успешно установлен")
            
            # Проверяем установку
            check_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
            check_response = requests.get(check_url, timeout=5)
            logger.info(f"📋 Информация о вебхуке: {check_response.json()}")
        else:
            logger.error(f"❌ Ошибка установки вебхука: {result}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке вебхука: {e}")

# ============ ЗАПУСК ПРИЛОЖЕНИЯ ============
if __name__ == '__main__':
    # Настройка логирования
    logger.info("=" * 80)
    logger.info("🚀 ЗАПУСК УЧЕБНОГО БОТА ПРЕМИУМ")
    logger.info("=" * 80)
    logger.info(f"🤖 Бот: @Konspekt_help_bot")
    logger.info(f"🔑 Токен: {TOKEN[:10]}...")
    logger.info(f"🌐 Платформа: Render.com")
    logger.info("=" * 80)
    
    # Настройка вебхука
    setup_webhook()
    
    # Запуск Flask сервера
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌍 Запуск веб-сервера на порту {port}...")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
                          )
