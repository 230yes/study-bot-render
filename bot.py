import os
import re
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
TOKEN = os.environ.get('BOT_TOKEN', '')

# ПРАВИЛЬНЫЙ ПАРСИНГ
def parse_request(text: str):
    """Правильно извлекает тему и объем"""
    text_lower = text.lower()
    
    # 1. Находим объем (цифры перед "лист" или в конце)
    volume = "3"
    
    # Варианты: "3 листа", "5л", "2 листа"
    volume_patterns = [
        r'(\d+)\s*лист\w*',    # "3 листа", "5листов"
        r'(\d+)\s*л\b',        # "5л"
        r'^(\d+)\s',           # "3 философия"
        r'\s(\d+)$'            # "философия 3"
    ]
    
    for pattern in volume_patterns:
        match = re.search(pattern, text_lower)
        if match:
            vol = match.group(1)
            if vol.isdigit() and 1 <= int(vol) <= 10:
                volume = vol
                # Убираем найденный объем из текста
                text_lower = text_lower.replace(match.group(0), '')
            break
    
    # 2. Убираем слова "конспект", "реферат", "эссе"
    for word in ["конспект", "реферат", "эссе", "по", "о", "на", "теме", "тема"]:
        text_lower = text_lower.replace(word, '')
    
    # 3. Очищаем и получаем тему
    topic = re.sub(r'\s+', ' ', text_lower).strip()
    
    # 4. Если тема короткая, берем больше слов
    if len(topic) < 3:
        # Берем все слова кроме цифр
        words = text.split()
        topic_words = []
        for word in words:
            if not word.isdigit() and word not in ["лист", "л", "листа", "листов"]:
                topic_words.append(word)
        topic = ' '.join(topic_words)
    
    return topic if topic else "общая тема", volume

# ГЕНЕРАЦИЯ КОНСПЕКТА
def generate_conspect(topic: str, pages: int):
    """Генерирует конспект правильного объема"""
    # Для 3 листов - больше контента
    if pages == 1:
        return f"""📚 КОНСПЕКТ: {topic.upper()}

📊 Объем: 1 лист А4

1. ОСНОВНЫЕ ПОЛОЖЕНИЯ
Тема "{topic}" требует внимательного изучения основных аспектов и концепций.

2. КЛЮЧЕВЫЕ ИДЕИ
• Идея 1 по теме {topic}
• Идея 2 по теме {topic}
• Идея 3 по теме {topic}

3. ЗАКЛЮЧЕНИЕ
Выводы по изученному материалу."""
    
    elif pages == 2:
        return f"""📚 КОНСПЕКТ: {topic.upper()}

📊 Объем: 2 листа А4

1. ВВЕДЕНИЕ
Тема "{topic}" представляет значительный интерес для исследования в современных условиях.

2. ОСНОВНАЯ ЧАСТЬ
2.1. Теоретические аспекты {topic}
• Основная концепция 1
• Основная концепция 2

2.2. Практическое значение
• Применение в реальной жизни
• Примеры использования

3. ЗАКЛЮЧЕНИЕ
• Вывод 1
• Вывод 2
• Вывод 3"""
    
    else:  # 3+ листов
        sections = min(pages, 5)
        content = [f"📚 КОНСПЕКТ: {topic.upper()}"]
        content.append(f"📊 Объем: {pages} листа(ов) А4")
        content.append("")
        content.append("1. ВВЕДЕНИЕ")
        content.append(f'Тема "{topic}" является комплексной и требует детального анализа различных аспектов.')
        content.append("")
        
        for i in range(1, sections):
            content.append(f"{i+1}. РАЗДЕЛ {i}: ОСНОВНЫЕ АСПЕКТЫ")
            content.append(f"• Подраздел {i}.1: Важный аспект темы")
            content.append(f"• Подраздел {i}.2: Дополнительные сведения")
            content.append(f"• Подраздел {i}.3: Практическое применение")
            content.append("")
        
        content.append(f"{sections+1}. ЗАКЛЮЧЕНИЕ")
        content.append("• Итоговый вывод 1")
        content.append("• Итоговый вывод 2")
        content.append("• Итоговый вывод 3")
        content.append("• Рекомендации для дальнейшего изучения")
        
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
            reply = "✅ Бот работает!\nПример: <code>конспект по войне 3 листа</code>"
        else:
            topic, volume = parse_request(text)
            pages = int(volume) if volume.isdigit() else 3
            
            # Проверяем парсинг
            test_msg = f"📋 Распознано:\nТема: <b>{topic}</b>\nОбъем: <b>{pages} лист(а/ов)</b>"
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": test_msg, "parse_mode": "HTML"}
            )
            
            # Генерация
            reply = generate_conspect(topic, pages)
        
        # Отправка
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply, "parse_mode": "HTML"}
        )
    
    return jsonify({"ok": True}), 200

@app.route('/health')
def health():
    return jsonify({"status": "working", "bot": "@Konspekt_help_bot"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
