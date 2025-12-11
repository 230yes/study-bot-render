#!/usr/bin/env python3
"""
🎓 ТЕСТОВЫЙ БОТ
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Настройка
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

TOKEN = os.environ.get('BOT_TOKEN', '')
if not TOKEN:
    logger.error("❌ НЕТ ТОКЕНА")
    exit()

# БД в памяти
user_data = {}

# Парсинг запроса - ПРОСТАЯ ВЕРСИЯ
def parse_request(text: str):
    """Простой парсинг: берем всё как тему"""
    text = text.lower().strip()
    
    # Убираем команды
    if text.startswith('/'):
        return "", "conspect", "3"
    
    # Ищем цифры для объема
    import re
    volume = "3"
    for match in re.finditer(r'(\d+)\s*лист', text):
        vol = match.group(1)
        if vol.isdigit() and 1 <= int(vol) <= 10:
            volume = vol
            text = text.replace(match.group(0), '')
    
    # Убираем слова типа
    for word in ["конспект", "реферат", "эссе", "по", "о", "на"]:
        text = text.replace(word, '')
    
    topic = text.strip()
    return topic if topic else "общая тема", "conspect", volume

# Генерация конспекта - ПРОСТАЯ
def generate_conspect(topic: str, pages: int):
    """Генерируем простой конспект"""
    sections = min(pages, 5)
    
    content = [f"📚 КОНСПЕКТ: {topic.upper()}"]
    content.append(f"📊 Объем: {pages} листа(ов)")
    content.append(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    content.append("")
    content.append("1. ВВЕДЕНИЕ")
    content.append(f"Тема '{topic}' является важной для изучения.")
    content.append("")
    
    for i in range(1, sections):
        content.append(f"{i+1}. РАЗДЕЛ {i}")
        content.append(f"• Основной пункт {i}.1")
        content.append(f"• Основной пункт {i}.2")
        content.append(f"• Основной пункт {i}.3")
        content.append("")
    
    content.append(f"{sections+1}. ЗАКЛЮЧЕНИЕ")
    content.append("• Вывод 1")
    content.append("• Вывод 2")
    content.append("• Вывод 3")
    
    return "\n".join(content)

# Отправка сообщения
def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

# Вебхук
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False}), 400
        
        if "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            
            logger.info(f"Сообщение: {text}")
            
            if text.startswith('/start'):
                send_message(chat_id, "👋 Привет! Напиши тему для конспекта, например: 'война 3 листа'")
            else:
                topic, _, volume = parse_request(text)
                pages = int(volume) if volume.isdigit() else 3
                
                send_message(chat_id, f"⏳ Генерирую конспект '{topic}' на {pages} листов...")
                
                content = generate_conspect(topic, pages)
                send_message(chat_id, content)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "Бот работает! Используйте /webhook для Telegram"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
