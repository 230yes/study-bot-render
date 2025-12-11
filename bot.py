#!/usr/bin/env python3
"""
🎓 БОТ С РЕАЛЬНЫМ ОБЪЕМОМ ТЕКСТА
"""

import os
import re
import random
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
TOKEN = os.environ.get('BOT_TOKEN', '')

# ============ ПРАВИЛЬНЫЙ ПАРСИНГ ============
def parse_request_final(text: str):
    """Финальный парсинг"""
    original = text
    
    # Удаляем команду
    if text.startswith('/'):
        text = text[1:]
    
    # Ищем цифру
    volume = "3"
    for match in re.finditer(r'\b(\d+)\b', text):
        vol = match.group(1)
        if vol.isdigit() and 1 <= int(vol) <= 10:
            volume = vol
            text = text[:match.start()] + text[match.end():]
            break
    
    # Убираем слова
    remove_words = ["конспект", "реферат", "эссе", "лист", "листа", "листов", "л", 
                   "по", "о", "на", "теме", "тема", "про", "об"]
    for word in remove_words:
        text = re.sub(r'\b' + word + r'\b', '', text, flags=re.IGNORECASE)
    
    # Очищаем
    topic = re.sub(r'\s+', ' ', text).strip()
    
    if not topic or len(topic) < 2:
        topic = original.split()[0] if original.split() else "тема"
    
    return topic[:50], volume

# ============ ГЕНЕРАЦИЯ РЕАЛЬНОГО ТЕКСТА ============
def generate_real_text(topic: str, pages: int):
    """Генерирует РЕАЛЬНЫЙ текст нужного объема"""
    
    # 1 лист ≈ 300 слов ≈ 1800 символов
    target_words = pages * 300
    
    paragraphs = []
    current_words = 0
    
    # Абзацы для генерации
    paragraph_templates = [
        f"Тема «{topic}» представляет собой важный предмет для исследования. ",
        f"Изучение {topic} позволяет рассмотреть различные аспекты и подходы. ",
        f"Историческое развитие {topic} оказало значительное влияние. ",
        f"В современном контексте {topic} приобретает новые значения. ",
        f"Теоретические основы изучения {topic} включают различные методологии. ",
        f"Практическое применение знаний о {topic} имеет широкий спектр. ",
        f"Анализ {topic} требует комплексного подхода. ",
        f"Исследование {topic} открывает новые перспективы. ",
        f"Ключевые аспекты {topic} требуют детального рассмотрения. ",
        f"Значение {topic} в современном мире постоянно возрастает. "
    ]
    
    # Генерируем абзацы пока не наберем нужный объем
    while current_words < target_words:
        # Берем случайные шаблоны
        num_sentences = random.randint(3, 6)
        paragraph = ""
        
        for _ in range(num_sentences):
            template = random.choice(paragraph_templates)
            # Немного меняем шаблон
            variations = [
                template,
                template.replace("представляет", "является"),
                template.replace("позволяет", "дает возможность"),
                template.replace("оказало", "оказала"),
                template.replace("включают", "содержат"),
                template.replace("требует", "нуждается в"),
                template.replace("открывает", "предоставляет")
            ]
            paragraph += random.choice(variations)
        
        paragraphs.append(paragraph)
        current_words += len(paragraph.split())
    
    # Формируем структурированный текст
    content = []
    
    # ЗАГОЛОВОК
    content.append(f"📚 <b>КОНСПЕКТ: {topic.upper()}</b>")
    content.append(f"📊 <b>Объем:</b> {pages} лист(а/ов) А4")
    content.append(f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    content.append("")
    
    # ВВЕДЕНИЕ (первые 3 абзаца)
    content.append("<b>1. ВВЕДЕНИЕ</b>")
    for i in range(min(3, len(paragraphs))):
        content.append(paragraphs[i])
    content.append("")
    
    # ОСНОВНАЯ ЧАСТЬ
    content.append("<b>2. ОСНОВНАЯ ЧАСТЬ</b>")
    
    # Делим оставшиеся абзацы на разделы
    remaining = paragraphs[3:] if len(paragraphs) > 3 else paragraphs
    
    # Количество разделов зависит от объема
    num_sections = min(pages, 5)
    section_size = len(remaining) // num_sections if remaining else 0
    
    for section in range(1, num_sections + 1):
        content.append(f"<b>2.{section}. РАЗДЕЛ {section}</b>")
        
        start_idx = (section - 1) * section_size
        end_idx = section * section_size if section < num_sections else len(remaining)
        
        if start_idx < len(remaining):
            section_paragraphs = remaining[start_idx:end_idx]
            for para in section_paragraphs:
                content.append(para)
        
        content.append("")
    
    # ЗАКЛЮЧЕНИЕ
    content.append("<b>3. ЗАКЛЮЧЕНИЕ</b>")
    conclusion = [
        f"В результате проведенного исследования по теме «{topic}» можно сделать следующие выводы:",
        f"Тема {topic} является комплексной и многогранной, требующей дальнейшего изучения.",
        f"Полученные знания о {topic} могут быть применены в различных сферах деятельности.",
        f"Исследование {topic} открывает перспективы для дальнейших научных изысканий."
    ]
    
    for line in conclusion:
        content.append(line)
    
    content.append("")
    
    # ИСТОЧНИКИ
    content.append("<b>📚 ИСТОЧНИКИ:</b>")
    sources = [
        "1. Научные исследования и публикации",
        "2. Учебные пособия и монографии",
        "3. Статьи в научных журналах",
        "4. Материалы конференций",
        "5. Интернет-ресурсы",
        "6. Архивные материалы",
        "7. Статистические данные",
        "8. Международные исследования"
    ]
    
    for i in range(min(pages * 2, 8)):
        content.append(sources[i])
    
    # Фактический объем
    full_text = "\n".join(content)
    words = len(full_text.split())
    chars = len(full_text)
    
    content.append("")
    content.append(f"<i>Фактический объем: {words} слов ({chars} символов)</i>")
    content.append(f"<i>Целевой объем: {target_words} слов ({pages} листов А4)</i>")
    
    return "\n".join(content)

# ============ ВЕБХУК ============
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        if text == "/start":
            reply = "✅ Бот работает!\nНапиши: <code>война 3 листа</code>"
        else:
            # Парсим
            topic, volume = parse_request_final(text)
            pages = int(volume) if volume.isdigit() else 3
            
            # Информация
            info = f"📋 <b>ПАРСИНГ:</b>\nТема: {topic}\nОбъем: {pages} лист(а/ов)\nГенерация..."
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": info, "parse_mode": "HTML"}
            )
            
            # Генерация РЕАЛЬНОГО текста
            reply = generate_real_text(topic, pages)
        
        # Отправка
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
