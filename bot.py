import os
import re
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
TOKEN = os.environ.get('BOT_TOKEN', '')

# ПРАВИЛЬНЫЙ парсинг
def parse_correct(text: str):
    """Правильно парсит тему и объем"""
    original = text
    text_lower = text.lower()
    
    # 1. Ищем ЛЮБУЮ цифру как объем
    volume = "3"
    volume_match = None
    
    # Все варианты где может быть цифра
    matches = re.finditer(r'\b(\d+)\b', text_lower)
    for match in matches:
        vol = match.group(1)
        if vol.isdigit() and 1 <= int(vol) <= 10:
            volume = vol
            volume_match = match.group(0)
            break
    
    # 2. Убираем объем
    clean_text = original
    if volume_match:
        # Заменяем цифру с пробелами вокруг
        clean_text = re.sub(r'\s*' + volume_match + r'\s*', ' ', clean_text)
    
    # 3. Убираем только слова "лист", "л" если они рядом с цифрами
    clean_text = re.sub(r'\s*лист\w*\s*', ' ', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\s*л\s*\b', ' ', clean_text, flags=re.IGNORECASE)
    
    # 4. Убираем типы материалов
    clean_text = re.sub(r'\b(конспект|реферат|эссе)\b', '', clean_text, flags=re.IGNORECASE)
    
    # 5. Убираем предлоги
    clean_text = re.sub(r'\b(по|о|на|теме|тема|про|об)\b', '', clean_text, flags=re.IGNORECASE)
    
    # 6. Очищаем
    topic = re.sub(r'\s+', ' ', clean_text).strip()
    
    # 7. Если тема короткая, берем оригинал
    if len(topic) < 2:
        # Берем все кроме цифр и "лист"
        words = original.split()
        filtered = []
        for word in words:
            word_lower = word.lower()
            if (not word.isdigit() and 
                'лист' not in word_lower and
                word not in ['л', 'листа', 'листов']):
                filtered.append(word)
        topic = ' '.join(filtered)
    
    print(f"✅ Распознано: Тема='{topic}', Объем={volume}л")
    return topic[:100], volume

# ПРАВИЛЬНАЯ генерация объема
def generate_real_volume(topic: str, pages: int):
    """Генерирует РЕАЛЬНЫЙ объем"""
    # 1 лист = больше текста
    base_content = f"""📚 <b>КОНСПЕКТ: {topic.upper()}</b>

📊 <b>Объем:</b> {pages} лист(а/ов) А4
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

<b>1. ВВЕДЕНИЕ</b>
Тема «{topic}» представляет собой важный предмет для исследования в современных условиях. 
Данная тема затрагивает различные аспекты и требует комплексного подхода к изучению.

<b>2. ОСНОВНАЯ ЧАСТЬ</b>"""
    
    # Добавляем разделы в зависимости от объема
    sections = []
    
    if pages == 1:
        sections = [
            "2.1. Ключевые понятия",
            "2.2. Основные характеристики",
            "2.3. Практическое значение"
        ]
    elif pages == 2:
        sections = [
            "2.1. Теоретические основы",
            "2.2. Исторический контекст", 
            "2.3. Современное состояние",
            "2.4. Практическое применение"
        ]
    else:  # 3+ листов
        num_sections = min(pages + 1, 6)
        sections = [f"2.{i}. Раздел {i}" for i in range(1, num_sections)]
    
    content = [base_content]
    
    for section in sections:
        content.append(f"<b>{section}</b>")
        content.append(f"• Подраздел 1: Важный аспект темы «{topic}»")
        content.append(f"• Подраздел 2: Дополнительные сведения")
        content.append(f"• Подраздел 3: Примеры и иллюстрации")
        content.append("")
    
    content.append("<b>3. ЗАКЛЮЧЕНИЕ</b>")
    content.append("• Вывод 1: Основные итоги исследования")
    content.append("• Вывод 2: Практические рекомендации")
    content.append("• Вывод 3: Перспективы дальнейшего изучения")
    
    content.append("")
    content.append("<b>📚 ИСТОЧНИКИ:</b>")
    content.append("1. Научные публикации по теме")
    content.append("2. Учебные материалы")
    content.append("3. Интернет-ресурсы")
    
    return "\n".join(content)

# ВЕБХУК
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        if text == "/start":
            reply = "✅ Бот работает!\nПример: <code>война 3 листа</code>"
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": reply, "parse_mode": "HTML"}
            )
        else:
            # Парсим
            topic, volume = parse_correct(text)
            pages = int(volume) if volume.isdigit() else 3
            
            # Показываем что распознал
            test_msg = f"📋 <b>РАСПОЗНАНО:</b>\nТема: {topic}\nОбъем: {pages} лист(а/ов)"
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": test_msg, "parse_mode": "HTML"}
            )
            
            # Генерация с правильным объемом
            reply = generate_real_volume(topic, pages)
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": reply, "parse_mode": "HTML"}
            )
    
    return jsonify({"ok": True}), 200

@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot": "@Konspekt_help_bot"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
