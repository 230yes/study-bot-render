#!/usr/bin/env python3
"""
🎓 УЧЕБНЫЙ БОТ ПРЕМИУМ v9.0
С выбором формата отправки и кратким предпросмотром
"""

import os
import logging
import json
import time
import re
import random
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Импорты для создания файлов
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("⚠️ Библиотека fpdf не установлена")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("⚠️ Библиотека python-docx не установлена")

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
    logger.error("❌ ТОКЕН НЕ НАЙДЕН! Добавьте BOT_TOKEN в Environment Variables")
    exit()

logger.info(f"✅ Токен получен: {TOKEN[:10]}...")

# ============ БАЗЫ ДАННЫХ ============
user_devices = {}
user_settings = {}
user_history = {}
pending_requests = {}  # Временное хранение запросов перед генерацией
# ============ КОНСТАНТЫ ============
DEVICES = {
    "phone": {"icon": "📱", "name": "Телефон", "description": "Мобильная версия"},
    "pc": {"icon": "💻", "name": "Компьютер", "description": "Полная версия"},
    "tablet": {"icon": "📟", "name": "Планшет", "description": "Промежуточная версия"},
    "watch": {"icon": "⌚", "name": "Часы", "description": "Краткая версия"}
}

CONTENT_TYPES = {
    "conspect": {"icon": "📚", "name": "Конспект", "description": "Учебные заметки с подробным содержанием"},
    "referat": {"icon": "📄", "name": "Реферат", "description": "Научная работа со структурой"},
    "presentation": {"icon": "🎤", "name": "Презентация", "description": "Структура слайдов с описанием"},
    "essay": {"icon": "✍️", "name": "Эссе", "description": "Аналитическое сочинение"}
}

EXPORT_FORMATS = {
    "pdf": {"icon": "📄", "name": "PDF", "mime": "application/pdf"},
    "docx": {"icon": "📝", "name": "DOCX", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "txt": {"icon": "📋", "name": "TXT", "mime": "text/plain"}
}

DELIVERY_TYPES = {
    "text": {"icon": "💬", "name": "Текстом в чат", "description": "Полный текст сразу в чате"},
    "file": {"icon": "📁", "name": "Файлом", "description": "Скачивание в выбранном формате"}
}

# ============ ОБЪЕМ В ЛИСТАХ А4 ============
VOLUME_LEVELS = {
    "1": {"icon": "📄", "name": "1 лист", "pages": 1, "words": "250-300"},
    "2": {"icon": "📄📄", "name": "2 листа", "pages": 2, "words": "500-600"},
    "3": {"icon": "📄📄📄", "name": "3 листа", "pages": 3, "words": "750-900"},
    "4": {"icon": "📄📄📄📄", "name": "4 листа", "pages": 4, "words": "1000-1200"},
    "5": {"icon": "📄📄📄📄📄", "name": "5 листов", "pages": 5, "words": "1250-1500"},
    "6": {"icon": "📚", "name": "6 листов", "pages": 6, "words": "1500-1800"},
    "7": {"icon": "📚📄", "name": "7 листов", "pages": 7, "words": "1750-2100"},
    "8": {"icon": "📚📚", "name": "8 листов", "pages": 8, "words": "2000-2400"},
    "9": {"icon": "📚📚📄", "name": "9 листов", "pages": 9, "words": "2250-2700"},
    "10": {"icon": "📘", "name": "10 листов", "pages": 10, "words": "2500-3000"}
}

# ============ БАЗА ЗНАНИЙ ПО ТЕМАМ ============
KNOWLEDGE_BASE = {
    "семья": {
        "definition": "Семья - это социальная группа, основанная на браке или кровном родстве, связанная общностью быта и взаимной ответственностью.",
        "key_points": [
            "Малая социальная группа",
            "Основана на браке или родстве", 
            "Совместное проживание и хозяйство",
            "Взаимная поддержка",
            "Эмоциональные связи"
        ],
        "short_preview": "Семья - базовая ячейка общества, выполняющая репродуктивную, воспитательную и экономическую функции. Рассматриваются типы семей, их структура и современные тенденции."
    },
    "экология": {
        "definition": "Экология - наука о взаимоотношениях живых организмов между собой и с окружающей средой.",
        "key_points": [
            "Изучение экосистем",
            "Взаимодействие организмов",
            "Влияние человека на природу",
            "Экологические проблемы",
            "Охрана окружающей среды"
        ],
        "short_preview": "Экология изучает взаимосвязи в природе, влияние человеческой деятельности на окружающую среду и пути решения экологических проблем для устойчивого развития."
    },
    "математика": {
        "definition": "Математика - наука о количественных отношениях и пространственных формах действительного мира.",
        "key_points": [
            "Алгебра и уравнения",
            "Геометрия и пространство",
            "Математический анализ",
            "Теория вероятностей",
            "Прикладная математика"
        ],
        "short_preview": "Математика - фундаментальная наука, изучающая структуры, пространственные формы и количественные отношения. Включает основные разделы: алгебру, геометрию, анализ."
    },
    "философия": {
        "definition": "Философия - наука о наиболее общих законах развития природы, общества и мышления.",
        "key_points": [
            "Онтология - учение о бытии",
            "Гносеология - теория познания",
            "Этика - учение о морали",
            "Эстетика - учение о прекрасном",
            "Логика - наука о мышлении"
        ],
        "short_preview": "Философия исследует фундаментальные вопросы бытия, познания, ценностей и разума. Рассматривает основные философские направления и их влияние на культуру."
    }
}

# ============ ШАБЛОНЫ ПРЕЗЕНТАЦИЙ ============
PRESENTATION_TEMPLATES = {
    "academic": {
        "name": "Академическая",
        "style": "Строгий стиль для научных работ",
        "color_scheme": "Синий, белый, серый",
        "font": "Times New Roman, Calibri"
    },
    "business": {
        "name": "Бизнес",
        "style": "Корпоративный стиль для презентаций",
        "color_scheme": "Синий, бежевый, серый",
        "font": "Arial, Helvetica"
    },
    "creative": {
        "name": "Креативная",
        "style": "Современный дизайн для творческих проектов",
        "color_scheme": "Яркие цвета, градиенты",
        "font": "Montserrat, Open Sans"
    }
}

# ============ УТИЛИТЫ ============
def get_user_device(user_id: str) -> dict:
    """Получение устройства пользователя"""
    return DEVICES.get(user_devices.get(user_id, "phone"), DEVICES["phone"])

def save_to_history(user_id: str, topic: str, content_type: str, volume: str = "3", delivery: str = "text"):
    """Сохранение в историю"""
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append({
        "topic": topic,
        "type": content_type,
        "volume": volume,
        "delivery": delivery,
        "timestamp": datetime.now().isoformat(),
        "device": user_devices.get(user_id, "phone")
    })
    
    # Ограничиваем историю 50 записями
    if len(user_history[user_id]) > 50:
        user_history[user_id] = user_history[user_id][-50:]

def split_message(text: str, max_length: int = 4000) -> list:
    """Разделение длинного сообщения на части"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        split_point = max_length
        for i in range(max_length - 100, max_length):
            if i < len(text) and text[i] in ['\n', '.', '!', '?']:
                split_point = i + 1
                break
        
        parts.append(text[:split_point])
        text = text[split_point:].strip()
    
    return parts

def parse_request(text: str) -> tuple:
    """Парсинг запроса пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    text_lower = text.lower()
    
    # Определяем тип контента
    content_type = "conspect"
    if "презентация" in text_lower or "слайд" in text_lower:
        content_type = "presentation"
    elif "реферат" in text_lower:
        content_type = "referat"
    elif "эссе" in text_lower:
        content_type = "essay"
    
    # Извлекаем объем
    volume = "3"  # По умолчанию
    patterns = [
        r'(\d+)\s*лист[аов]*',
        r'(\d+)\s*л\b',
        r'(\d+)\s*стр[аиц]*',
        r'\b(\d+)\s*$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            vol = match.group(1)
            if vol.isdigit() and 1 <= int(vol) <= 10:
                volume = vol
            break
    
    # Извлекаем тему (убираем служебные слова)
    clean_text = text_lower
    for word in ['конспект', 'реферат', 'презентация', 'эссе', 'по', 'о', 'на', 'теме', 'тема']:
        clean_text = clean_text.replace(word, '')
    
    # Убираем объем из текста
    for pattern in patterns:
        clean_text = re.sub(pattern, '', clean_text)
    
    # Очищаем пробелы
    topic = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Если тема пустая, берем последнее слово
    if not topic and ' ' in text:
        topic = text.split()[-1]
    
    return topic, content_type, volume

def generate_short_preview(topic: str, content_type: str) -> str:
    """Генерация краткого предпросмотра"""
    topic_lower = topic.lower()
    
    # Ищем тему в базе знаний
    preview = ""
    for key in KNOWLEDGE_BASE:
        if key in topic_lower:
            preview = KNOWLEDGE_BASE[key]["short_preview"]
            break
    
    if not preview:
        # Генерация общего предпросмотра
        previews = {
            "conspect": f"Конспект по теме '{topic}' будет содержать основные понятия, ключевые тезисы и структурированное изложение материала.",
            "referat": f"Реферат на тему '{topic}' будет включать введение, основную часть с анализом литературы, заключение и список источников.",
            "presentation": f"Презентация по теме '{topic}' будет содержать структуру слайдов с рекомендациями по оформлению и визуальным элементам.",
            "essay": f"Эссе на тему '{topic}' представит аналитический разбор проблемы с аргументацией и личной позицией автора."
        }
        preview = previews.get(content_type, previews["conspect"])
    
    return preview

def generate_sources(topic: str, count: int = 5) -> list:
    """Генерация списка источников"""
    base_sources = [
        "Научный журнал 'Вестник Московского университета' (2020-2023)",
        "Учебник по основам дисциплины (последнее издание)",
        "Материалы Российской академии наук",
        "Международные научные публикации",
        "Образовательные ресурсы и онлайн-курсы",
        "Сборники научных трудов и конференций",
        "Энциклопедические издания",
        "Академические исследования и монографии"
    ]
    
    # Выбираем случайные источники
    sources = random.sample(base_sources, min(count, len(base_sources)))
    
    # Добавляем тематические
    if "семья" in topic.lower():
        sources.append("Семейный кодекс Российской Федерации")
        sources.append("Социологические исследования института семьи")
    
    return sources[:count]
# ============ ОТПРАВКА СООБЩЕНИЙ ============
def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML", 
                         reply_markup: dict = None, disable_preview: bool = True) -> dict:
    """Отправка сообщения в Telegram"""
    try:
        # Разделяем длинные сообщения
        message_parts = split_message(text)
        
        for i, part in enumerate(message_parts):
            if i > 0:
                part = f"📄 Часть {i+1}:\n\n{part}"
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": part,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_preview
            }
            
            if reply_markup and i == len(message_parts) - 1:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Ошибка отправки: {response.text}")
                return {"ok": False, "error": response.text}
        
        logger.info(f"📤 Сообщение отправлено в чат {chat_id}")
        return {"ok": True}
            
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
            "caption": caption[:1024],
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
        # ============ ГЕНЕРАЦИЯ КОНТЕНТА ============
def generate_full_content(topic: str, content_type: str, volume_pages: int, 
                         presentation_template: str = "academic") -> str:
    """Генерация полного контента с учетом объема"""
    
    volume_info = VOLUME_LEVELS.get(str(volume_pages), VOLUME_LEVELS["3"])
    content_type_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES["conspect"])
    
    content = []
    
    # Заголовок
    content.append(f"{content_type_info['icon']} <b>{content_type_info['name'].upper()}: {topic.upper()}</b>")
    content.append("")
    content.append(f"📊 <b>ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:</b>")
    content.append(f"• Объем: {volume_info['icon']} {volume_info['name']} А4")
    
    if content_type == "presentation":
        content.append(f"• Слайдов: {volume_pages}")
        template_info = PRESENTATION_TEMPLATES.get(presentation_template, PRESENTATION_TEMPLATES["academic"])
        content.append(f"• Шаблон: {template_info['name']}")
    else:
        content.append(f"• Примерно слов: {volume_info['words']}")
    
    content.append(f"• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    content.append("")
    
    # ГЕНЕРАЦИЯ ОСНОВНОГО КОНТЕНТА
    if content_type == "conspect":
        content.extend(generate_conspect_content(topic, volume_pages))
    elif content_type == "referat":
        content.extend(generate_referat_content(topic, volume_pages))
    elif content_type == "presentation":
        content.extend(generate_presentation_content(topic, volume_pages, presentation_template))
    elif content_type == "essay":
        content.extend(generate_essay_content(topic, volume_pages))
    
    # Источники (не для презентаций)
    if content_type != "presentation":
        content.append("")
        content.append("📚 <b>ИСТОЧНИКИ ИНФОРМАЦИИ:</b>")
        sources = generate_sources(topic, min(volume_pages + 2, 8))
        for i, source in enumerate(sources, 1):
            content.append(f"{i}. {source}")
    
    return "\n".join(content)

def generate_conspect_content(topic: str, volume_pages: int) -> list:
    """Генерация контента конспекта с учетом объема"""
    content = []
    
    topic_lower = topic.lower()
    topic_info = None
    
    # Ищем в базе знаний
    for key in KNOWLEDGE_BASE:
        if key in topic_lower:
            topic_info = KNOWLEDGE_BASE[key]
            break
    
    content.append("<b>📖 СОДЕРЖАНИЕ КОНСПЕКТА:</b>")
    content.append("")
    
    if volume_pages == 1:
        # 1 лист - только самое важное
        if topic_info:
            content.append(f"<b>1. ОПРЕДЕЛЕНИЕ</b>")
            content.append(topic_info["definition"])
            content.append("")
            content.append(f"<b>2. КЛЮЧЕВЫЕ ПУНКТЫ</b>")
            for point in topic_info["key_points"][:3]:
                content.append(f"• {point}")
        else:
            content.append(f"<b>1. ОСНОВНЫЕ ПОЛОЖЕНИЯ</b>")
            content.append(f"Тема '{topic}' охватывает важные аспекты, требующие изучения.")
            content.append("")
            content.append(f"<b>2. ГЛАВНЫЕ ИДЕИ</b>")
            content.append("• Ключевая идея 1")
            content.append("• Ключевая идея 2")
            content.append("• Ключевая идея 3")
    
    elif volume_pages == 2:
        # 2 листа
        content.append(f"<b>1. ВВЕДЕНИЕ</b>")
        if topic_info:
            content.append(topic_info["definition"])
        else:
            content.append(f"Тема '{topic}' представляет значительный интерес для изучения.")
        content.append("")
        
        content.append(f"<b>2. ОСНОВНАЯ ЧАСТЬ</b>")
        if topic_info:
            for i, point in enumerate(topic_info["key_points"][:4], 1):
                content.append(f"{i}. {point}")
        else:
            for i in range(1, 5):
                content.append(f"{i}. Основной аспект {i}")
        content.append("")
        
        content.append(f"<b>3. ЗАКЛЮЧЕНИЕ</b>")
        content.append("• Ключевые выводы")
        content.append("• Практическая значимость")
    
    else:
        # 3+ листов
        content.append(f"<b>1. ВВЕДЕНИЕ</b>")
        if topic_info:
            content.append(topic_info["definition"])
        else:
            content.append(f"Тема '{topic}' является важной областью знания, требующей детального рассмотрения.")
        content.append("")
        
        # Количество разделов зависит от объема
        sections = min(volume_pages - 1, 5)
        
        for i in range(1, sections + 1):
            content.append(f"<b>{i+1}. РАЗДЕЛ {i}</b>")
            if topic_info and i == 1:
                for point in topic_info["key_points"][:5]:
                    content.append(f"• {point}")
            else:
                for j in range(1, 4):
                    content.append(f"• Подраздел {i}.{j}")
            
            # Для больших объемов добавляем подробности
            if volume_pages >= 4 and i <= 2:
                content.append("<i>Дополнительные пояснения и примеры...</i>")
            
            content.append("")
        
        content.append(f"<b>{sections + 2}. ЗАКЛЮЧЕНИЕ</b>")
        content.append("• Обобщение основных положений")
        content.append("• Практические рекомендации")
        content.append("• Перспективы дальнейшего изучения")
    
    return content

def generate_referat_content(topic: str, volume_pages: int) -> list:
    """Генерация содержания реферата"""
    content = []
    
    content.append("<b>📄 СТРУКТУРА РЕФЕРАТА:</b>")
    content.append("")
    
    content.append("<b>1. ТИТУЛЬНЫЙ ЛИСТ</b>")
    content.append("• Название учебного заведения")
    content.append(f"• Тема: «{topic}»")
    content.append("• ФИО студента и преподавателя")
    content.append("• Город, год")
    content.append("")
    
    content.append("<b>2. СОДЕРЖАНИЕ</b>")
    content.append("• Введение")
    
    # Количество глав зависит от объема
    chapters = min(3, max(2, volume_pages - 3))
    for i in range(1, chapters + 1):
        content.append(f"• Глава {i}")
    
    content.append("• Заключение")
    content.append("• Список литературы")
    content.append("")
    
    content.append("<b>3. ВВЕДЕНИЕ</b>")
    content.append(f"Актуальность темы «{topic}» обусловлена её значимостью в современной науке и практике.")
    content.append("Цель работы: изучить основные аспекты данной темы.")
    content.append("Задачи исследования:")
    content.append("1. Рассмотреть теоретические основы")
    content.append("2. Проанализировать ключевые положения")
    content.append("3. Сделать выводы")
    content.append("")
    
    for i in range(1, chapters + 1):
        content.append(f"<b>4.{i}. ГЛАВА {i}</b>")
        content.append(f"В данной главе рассматриваются вопросы, связанные с {['теоретическими основами', 'практическим анализом', 'результатами исследования'][i-1 if i-1 < 3 else 2]} темы.")
        content.append("Основные положения:")
        content.append("• Положение 1")
        content.append("• Положение 2")
        content.append("• Положение 3")
        content.append("")
    
    content.append("<b>5. ЗАКЛЮЧЕНИЕ</b>")
    content.append("В результате исследования были сделаны следующие выводы:")
    content.append("1. Вывод 1")
    content.append("2. Вывод 2")
    content.append("3. Вывод 3")
    
    return content

def generate_presentation_content(topic: str, slides_count: int, template: str = "academic") -> list:
    """Генерация структуры презентации"""
    content = []
    
    template_info = PRESENTATION_TEMPLATES.get(template, PRESENTATION_TEMPLATES["academic"])
    
    content.append("<b>🎤 ИНСТРУКЦИЯ ДЛЯ СОЗДАНИЯ ПРЕЗЕНТАЦИИ:</b>")
    content.append("")
    content.append(f"<b>ШАБЛОН: {template_info['name']}</b>")
    content.append(f"СТИЛЬ: {template_info['style']}")
    content.append(f"ШРИФТЫ: {template_info['font']}")
    content.append("")
    
    content.append("<b>📋 СТРУКТУРА СЛАЙДОВ:</b>")
    content.append("")
    
    # Базовые слайды
    slides = [
        {
            "num": 1,
            "title": "Титульный слайд",
            "content": ["Крупный заголовок", "Автор и организация", "Дата"],
            "design": "Фон: градиент или тематическое изображение"
        },
        {
            "num": 2,
            "title": "Содержание",
            "content": ["План презентации", "Ключевые разделы", "Ожидаемые результаты"],
            "design": "Схема с иконками для навигации"
        }
    ]
    
    # Основные слайды
    main_slides = min(slides_count - 2, 6)
    for i in range(1, main_slides + 1):
        slide_types = [
            "Введение и актуальность",
            "Цели и задачи",
            "Теоретические основы",
            "Практическая часть",
            "Результаты",
            "Выводы"
        ]
        
        slides.append({
            "num": i + 2,
            "title": slide_types[i-1] if i-1 < len(slide_types) else f"Слайд {i+2}",
            "content": ["Основная идея", "Ключевые факты", "Примеры"],
            "design": "Графики, диаграммы, изображения"
        })
    
    # Заключительный слайд
    slides.append({
        "num": slides_count,
        "title": "Спасибо за внимание!",
        "content": ["Вопросы?", "Контакты", "Дополнительные материалы"],
        "design": "Финальное изображение, контактная информация"
    })
    
    # Ограничиваем количество слайдов
    slides = slides[:min(slides_count, len(slides))]
    
    for slide in slides:
        content.append(f"<b>СЛАЙД {slide['num']}: {slide['title']}</b>")
        content.append("<b>Контент:</b>")
        for item in slide["content"]:
            content.append(f"• {item}")
        content.append("<b>Дизайн:</b>")
        content.append(f"• {slide['design']}")
        content.append("")
    
    content.append("<b>🎯 РЕКОМЕНДАЦИИ:</b>")
    content.append(f"• Общее время: {slides_count * 1.5:.1f} минут")
    content.append("• 1 слайд = 1 основная идея")
    content.append("• Минимум текста, максимум визуалов")
    content.append("• Используйте единый стиль")
    content.append("• Репетируйте выступление")
    
    return content

def generate_essay_content(topic: str, volume_pages: int) -> list:
    """Генерация содержания эссе"""
    content = []
    
    content.append("<b>✍️ СТРУКТУРА ЭССЕ:</b>")
    content.append("")
    
    content.append("<b>1. ВСТУПЛЕНИЕ (10-15% объема)</b>")
    content.append(f"Тема «{topic}» представляет значительный интерес для анализа.")
    content.append("Основной тезис: [сформулируйте центральную идею эссе]")
    content.append("")
    
    # Количество абзацев зависит от объема
    paragraphs = min(5, max(3, volume_pages * 2))
    
    content.append(f"<b>2. ОСНОВНАЯ ЧАСТЬ ({paragraphs} абзацев)</b>")
    for i in range(1, paragraphs + 1):
        content.append("")
        content.append(f"<b>Абзац {i}:</b>")
        content.append("• Основная мысль абзаца")
        content.append("• Аргументы и доказательства")
        content.append("• Примеры и иллюстрации")
        content.append("• Связь с основным тезисом")
    
    content.append("")
    content.append("<b>3. ЗАКЛЮЧЕНИЕ</b>")
    content.append("• Обобщение основных идей")
    content.append("• Подтверждение тезиса")
    content.append("• Философское размышление")
    content.append("• Перспективы исследования")
    
    return content
    # ============ ОБРАБОТКА СООБЩЕНИЙ И КОМАНД ============
def handle_start_command(chat_id: int, user_id: str, username: str) -> dict:
    """Обработка команды /start"""
    welcome_text = f"""
👋 <b>Добро пожаловать, {username or 'студент'}!</b>

🎓 <b>УЧЕБНЫЙ БОТ ПРЕМИУМ v9.0</b>

Я помогу вам создать:
📚 Конспекты    📄 Рефераты
🎤 Презентации  ✍️ Эссе

<b>Как пользоваться:</b>
1. Выберите устройство для форматирования
2. Укажите тип нужного материала
3. Введите тему и объем
4. Получите готовый результат!

📱 <b>Выберите устройство:</b> 
Это поможет адаптировать контент под ваш экран.
"""
    
    return send_telegram_message(
        chat_id=chat_id,
        text=welcome_text,
        reply_markup=create_device_keyboard()
    )

def handle_help_command(chat_id: int) -> dict:
    """Обработка команды /help"""
    help_text = """
🆘 <b>ПОМОЩЬ И ИНСТРУКЦИЯ</b>

<b>Доступные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/device - Изменить устройство
/history - Посмотреть историю
/formats - Показать доступные форматы

<b>Как создать материал:</b>
1. <b>Выберите устройство</b> - бот адаптирует контент
2. <b>Выберите тип материала</b> (конспект, реферат и т.д.)
3. <b>Введите запрос</b> в формате:
   <i>конспект по философии 3 листа</i>
   <i>реферат на тему экология 5 листов</i>
   <i>презентация про математику 10 слайдов</i>

<b>Форматы вывода:</b>
• 💬 <b>Текст в чате</b> - сразу после генерации
• 📁 <b>Файл</b> - PDF, DOCX или TXT для скачивания

<b>Объем:</b> от 1 до 10 листов А4
<b>Презентации:</b> от 3 до 15 слайдов

📞 <b>Поддержка:</b> @username
"""
    
    return send_telegram_message(chat_id=chat_id, text=help_text)

def handle_formats_command(chat_id: int) -> dict:
    """Обработка команды /formats"""
    formats_text = """
📋 <b>ДОСТУПНЫЕ ФОРМАТЫ ЭКСПОРТА</b>

<b>Для текстовых материалов:</b>
📄 <b>PDF</b> - готов к печати, официальный формат
📝 <b>DOCX</b> - для редактирования в Microsoft Word
📋 <b>TXT</b> - простой текст, минимальный размер

<b>Для презентаций:</b>
🎨 <b>PPTX</b> - для Microsoft PowerPoint
📑 <b>PDF</b> - слайды в формате для печати
📄 <b>TXT</b> - текстовая структура с описанием

<b>Шаблоны презентаций:</b>
🎓 <b>Академическая</b> - строгий стиль для научных работ
💼 <b>Бизнес</b> - корпоративный стиль
🎨 <b>Креативная</b> - современный дизайн для проектов

<b>Типы материалов:</b>
📚 <b>Конспект</b> - учебные заметки, структурированный материал
📄 <b>Реферат</b> - научная работа с введением и заключением
🎤 <b>Презентация</b> - структура слайдов с дизайном
✍️ <b>Эссе</b> - аналитическое сочинение с аргументацией

<b>Объемы:</b>
• Конспекты/рефераты/эссе: 1-10 листов А4
• Презентации: 3-15 слайдов

<b>Как использовать:</b>
1. Выберите тип материала
2. Укажите тему и объем
3. Получите текст в чате
4. При необходимости экспортируйте в файл

📌 <b>Пример запроса:</b>
<code>конспект по философии 5 листов</code>
<code>презентация на тему экология 10 слайдов</code>
<code>реферат о семье 3 листа</code>
"""
    
    return send_telegram_message(chat_id=chat_id, text=formats_text)

def handle_device_command(chat_id: int, user_id: str) -> dict:
    """Обработка команды /device"""
    current_device = user_devices.get(user_id, "phone")
    device_info = DEVICES[current_device]
    
    device_text = f"""
📱 <b>НАСТРОЙКА УСТРОЙСТВА</b>

Текущее устройство: {device_info['icon']} <b>{device_info['name']}</b>
<i>{device_info['description']}</i>

Выберите новое устройство для адаптации контента:
"""
    
    return send_telegram_message(
        chat_id=chat_id,
        text=device_text,
        reply_markup=create_device_keyboard()
    )

def handle_history_command(chat_id: int, user_id: str) -> dict:
    """Обработка команды /history"""
    history = user_history.get(user_id, [])
    
    if not history:
        return send_telegram_message(
            chat_id=chat_id,
            text="📜 <b>История пуста</b>\n\nУ вас еще нет созданных материалов."
        )
    
    history_text = f"📜 <b>ИСТОРИЯ ЗАПРОСОВ</b>\nВсего: {len(history)}\n\n"
    
    # Показываем последние 5 записей
    for i, entry in enumerate(reversed(history[-5:]), 1):
        entry_time = datetime.fromisoformat(entry["timestamp"]).strftime("%d.%m.%Y %H:%M")
        history_text += f"<b>{i}. {entry_time}</b>\n"
        history_text += f"Тема: <i>{entry['topic']}</i>\n"
        history_text += f"Тип: {CONTENT_TYPES[entry['type']]['icon']} {entry['type']}\n"
        history_text += f"Объем: {VOLUME_LEVELS[entry['volume']]['icon']} {entry['volume']} л.\n"
        history_text += f"Устройство: {DEVICES[entry['device']]['icon']}\n"
        history_text += "─" * 30 + "\n\n"
    
    if len(history) > 5:
        history_text += f"<i>Показано 5 из {len(history)} записей</i>\n"
    
    history_text += "\n📌 <b>Используйте /start для нового запроса</b>"
    
    return send_telegram_message(chat_id=chat_id, text=history_text)

def handle_user_message(chat_id: int, user_id: str, text: str) -> dict:
    """Обработка текстового сообщения от пользователя"""
    # Парсим запрос
    topic, content_type, volume = parse_request(text)
    
    if not topic or len(topic) < 2:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ <b>Не удалось определить тему</b>\n\nПожалуйста, укажите тему более четко.\n\n<b>Примеры:</b>\n<code>конспект по философии</code>\n<code>реферат на тему экология 3 листа</code>"
        )
    
    # Проверяем объем для презентации
    if content_type == "presentation":
        try:
            slides_count = int(volume)
            if slides_count < 3:
                volume = "3"
            elif slides_count > 15:
                volume = "15"
        except:
            volume = "3"
    
    # Генерируем предпросмотр
    preview_text = generate_short_preview(topic, content_type)
    
    # Сохраняем запрос в ожидании выбора формата доставки
    pending_requests[user_id] = {
        "topic": topic,
        "content_type": content_type,
        "volume": volume,
        "timestamp": datetime.now().isoformat(),
        "chat_id": chat_id
    }
    
    # Получаем информацию о типе контента и объеме
    content_info = CONTENT_TYPES[content_type]
    volume_info = VOLUME_LEVELS[volume]
    
    # Формируем сообщение с предпросмотром
    preview_message = f"""
✅ <b>ЗАПРОС ПРИНЯТ!</b>

<b>Тема:</b> {topic}
<b>Тип:</b> {content_info['icon']} {content_info['name']}
<b>Объем:</b> {volume_info['icon']} {volume_info['name']}

📋 <b>КРАТКИЙ ОБЗОР:</b>
{preview_text}

🎯 <b>Выберите формат получения:</b>
"""
    
    # Создаем клавиатуру выбора формата доставки
    delivery_keyboard = {
        "inline_keyboard": [
            [
                {"text": "💬 Получить текстом", "callback_data": f"delivery_text_{content_type}_{volume}_{topic}"},
                {"text": "📁 Скачать файлом", "callback_data": f"delivery_file_{content_type}_{volume}_{topic}"}
            ],
            [
                {"text": "🔙 Изменить параметры", "callback_data": "change_params"}
            ]
        ]
    }
    
    return send_telegram_message(
        chat_id=chat_id,
        text=preview_message,
        reply_markup=delivery_keyboard
    )
    # ============ ОБРАБОТКА CALLBACK-ЗАПРОСОВ ============
def handle_callback_query(callback_data: str, chat_id: int, user_id: str, message_id: int) -> dict:
    """Обработка callback-запросов от кнопок"""
    
    # Удаляем предыдущую клавиатуру
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageReplyMarkup"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": {"inline_keyboard": []}
    }
    requests.post(url, json=payload)
    
    # Обрабатываем разные типы callback данных
    if callback_data.startswith("device_"):
        return handle_device_callback(callback_data, chat_id, user_id)
    
    elif callback_data.startswith("type_"):
        return handle_type_callback(callback_data, chat_id, user_id)
    
    elif callback_data.startswith("volume_"):
        return handle_volume_callback(callback_data, chat_id, user_id)
    
    elif callback_data.startswith("delivery_"):
        return handle_delivery_callback(callback_data, chat_id, user_id)
    
    elif callback_data.startswith("format_"):
        return handle_format_callback(callback_data, chat_id, user_id)
    
    elif callback_data.startswith("template_"):
        return handle_template_callback(callback_data, chat_id, user_id)
    
    elif callback_data == "change_params":
        return handle_change_params(chat_id, user_id)
    
    elif callback_data == "new_request":
        return handle_new_request(chat_id, user_id)
    
    else:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ <b>Неизвестная команда</b>\n\nИспользуйте /start для начала работы."
        )

def handle_device_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора устройства"""
    device_id = callback_data.replace("device_", "")
    
    if device_id not in DEVICES:
        device_id = "phone"
    
    # Сохраняем выбор устройства
    user_devices[user_id] = device_id
    device_info = DEVICES[device_id]
    
    # Отправляем подтверждение
    device_text = f"""
✅ <b>Устройство выбрано!</b>

{device_info['icon']} <b>{device_info['name']}</b>
<i>{device_info['description']}</i>

📌 Теперь выберите тип материала:
"""
    
    return send_telegram_message(
        chat_id=chat_id,
        text=device_text,
        reply_markup=create_content_type_keyboard()
    )

def handle_type_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора типа контента"""
    content_type = callback_data.replace("type_", "")
    
    if content_type not in CONTENT_TYPES:
        content_type = "conspect"
    
    content_info = CONTENT_TYPES[content_type]
    
    # Сохраняем выбор типа
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["last_content_type"] = content_type
    
    # Создаем клавиатуру выбора объема
    volume_keyboard = {
        "inline_keyboard": []
    }
    
    # Для презентаций ограничиваем объем
    if content_type == "presentation":
        volumes_to_show = ["3", "5", "7", "10", "12", "15"]
        volume_label = "слайдов"
    else:
        volumes_to_show = ["1", "2", "3", "5", "7", "10"]
        volume_label = "листов"
    
    row = []
    for vol in volumes_to_show:
        vol_info = VOLUME_LEVELS[vol]
        row.append({
            "text": f"{vol_info['icon']} {vol} {volume_label}",
            "callback_data": f"volume_{content_type}_{vol}"
        })
        if len(row) == 2:
            volume_keyboard["inline_keyboard"].append(row)
            row = []
    
    if row:
        volume_keyboard["inline_keyboard"].append(row)
    
    # Добавляем кнопку назад
    volume_keyboard["inline_keyboard"].append([
        {"text": "🔙 Назад к выбору типа", "callback_data": "change_params"}
    ])
    
    type_text = f"""
✅ <b>Тип выбран!</b>

{content_info['icon']} <b>{content_info['name']}</b>
<i>{content_info['description']}</i>

📊 Теперь выберите объем материала:
"""
    
    if content_type == "presentation":
        type_text += "\n🎨 <b>Для презентаций также доступны:</b>\n• Шаблоны оформления\n• Рекомендации по дизайну\n• Время выступления"
    
    return send_telegram_message(
        chat_id=chat_id,
        text=type_text,
        reply_markup=volume_keyboard
    )

def handle_volume_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора объема"""
    parts = callback_data.split("_")
    if len(parts) < 3:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ Ошибка выбора объема\n\nИспользуйте /start для начала работы."
        )
    
    content_type = parts[1]
    volume = parts[2]
    
    # Сохраняем выбор
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["last_volume"] = volume
    user_settings[user_id]["last_content_type"] = content_type
    
    content_info = CONTENT_TYPES[content_type]
    volume_info = VOLUME_LEVELS[volume]
    
    volume_text = f"""
✅ <b>Параметры установлены!</b>

<b>Тип:</b> {content_info['icon']} {content_info['name']}
<b>Объем:</b> {volume_info['icon']} {volume_info['name']}

📝 Теперь введите тему вашего материала.

<b>Примеры запросов:</b>
<code>история древнего рима</code>
<code>философия платона и аристотеля</code>
<code>экологические проблемы современности</code>
<code>математические методы в экономике</code>

<b>Или можно указать все сразу:</b>
<code>конспект по философии 3 листа</code>
<code>презентация на тему экология 10 слайдов</code>
"""
    
    return send_telegram_message(chat_id=chat_id, text=volume_text)

def handle_delivery_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора формата доставки"""
    parts = callback_data.split("_")
    if len(parts) < 5:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ Ошибка обработки запроса"
        )
    
    delivery_type = parts[1]
    content_type = parts[2]
    volume = parts[3]
    topic = "_".join(parts[4:])  # Тема может содержать несколько слов
    
    if delivery_type == "text":
        # Генерируем и отправляем текст
        return generate_and_send_content(chat_id, user_id, topic, content_type, volume, "text")
    
    elif delivery_type == "file":
        # Предлагаем выбрать формат файла
        return handle_file_format_selection(chat_id, user_id, topic, content_type, volume)
    
    else:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ Неизвестный формат доставки"
        )

def handle_file_format_selection(chat_id: int, user_id: str, topic: str, content_type: str, volume: str) -> dict:
    """Предложение выбора формата файла"""
    format_keyboard = {
        "inline_keyboard": [
            [
                {"text": "📄 PDF", "callback_data": f"format_pdf_{content_type}_{volume}_{topic}"},
                {"text": "📝 DOCX", "callback_data": f"format_docx_{content_type}_{volume}_{topic}"},
                {"text": "📋 TXT", "callback_data": f"format_txt_{content_type}_{volume}_{topic}"}
            ]
        ]
    }
    
    # Для презентаций добавляем дополнительные форматы
    if content_type == "presentation":
        format_keyboard["inline_keyboard"][0].append(
            {"text": "🎨 PPTX", "callback_data": f"format_pptx_{content_type}_{volume}_{topic}"}
        )
    
    format_keyboard["inline_keyboard"].append([
        {"text": "🔙 Назад", "callback_data": f"delivery_text_{content_type}_{volume}_{topic}"}
    ])
    
    format_text = f"""
📁 <b>ВЫБОР ФОРМАТА ФАЙЛА</b>

Тема: <b>{topic}</b>
Тип: {CONTENT_TYPES[content_type]['icon']} {content_type}
Объем: {VOLUME_LEVELS[volume]['icon']} {volume}

Выберите формат для скачивания:
"""
    
    return send_telegram_message(
        chat_id=chat_id,
        text=format_text,
        reply_markup=format_keyboard
    )
def handle_format_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора формата файла"""
    parts = callback_data.split("_")
    if len(parts) < 5:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ Ошибка обработки формата"
        )
    
    format_type = parts[1]
    content_type = parts[2]
    volume = parts[3]
    topic = "_".join(parts[4:])
    
    # Генерируем и отправляем файл
    return generate_and_send_content(chat_id, user_id, topic, content_type, volume, "file", format_type)

def handle_template_callback(callback_data: str, chat_id: int, user_id: str) -> dict:
    """Обработка выбора шаблона презентации"""
    template_id = callback_data.replace("template_", "")
    
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    user_settings[user_id]["presentation_template"] = template_id
    
    template_info = PRESENTATION_TEMPLATES.get(template_id, PRESENTATION_TEMPLATES["academic"])
    
    template_text = f"""
🎨 <b>Шаблон выбран!</b>

<b>{template_info['name']}</b>
<i>{template_info['style']}</i>

Цветовая схема: {template_info['color_scheme']}
Шрифты: {template_info['font']}

📌 Теперь введите тему презентации.
"""
    
    return send_telegram_message(chat_id=chat_id, text=template_text)

def handle_change_params(chat_id: int, user_id: str) -> dict:
    """Обработка изменения параметров"""
    return send_telegram_message(
        chat_id=chat_id,
        text="🔧 <b>ИЗМЕНЕНИЕ ПАРАМЕТРОВ</b>\n\nВыберите тип материала:",
        reply_markup=create_content_type_keyboard()
    )

def handle_new_request(chat_id: int, user_id: str) -> dict:
    """Обработка нового запроса"""
    return send_telegram_message(
        chat_id=chat_id,
        text="🔄 <b>НОВЫЙ ЗАПРОС</b>\n\nВыберите устройство для начала работы:",
        reply_markup=create_device_keyboard()
    )

def generate_and_send_content(chat_id: int, user_id: str, topic: str, 
                            content_type: str, volume: str, 
                            delivery: str, file_format: str = None) -> dict:
    """Генерация и отправка контента"""
    try:
        # Отправляем сообщение о начале генерации
        process_msg = send_telegram_message(
            chat_id=chat_id,
            text=f"⏳ <b>Генерирую {CONTENT_TYPES[content_type]['name'].lower()}...</b>\nТема: {topic}\nЭто займет несколько секунд."
        )
        
        # Получаем информацию об устройстве
        device_type = user_devices.get(user_id, "phone")
        device_info = DEVICES[device_type]
        
        # Генерируем контент
        if content_type == "presentation":
            template = user_settings.get(user_id, {}).get("presentation_template", "academic")
            full_content = generate_full_content(topic, content_type, int(volume), template)
        else:
            full_content = generate_full_content(topic, content_type, int(volume))
        
        # Определяем текущее время для меток
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if delivery == "text":
            # Отправляем текстом
            result = send_telegram_message(
                chat_id=chat_id,
                text=full_content
            )
            
            if result["ok"]:
                # Добавляем кнопки после текста
                after_text = f"""
✅ <b>Материал готов!</b>

📊 <b>Итог:</b>
Тема: {topic}
Тип: {CONTENT_TYPES[content_type]['icon']} {CONTENT_TYPES[content_type]['name']}
Объем: {VOLUME_LEVELS[volume]['icon']} {VOLUME_LEVELS[volume]['name']}
Устройство: {device_info['icon']} {device_info['name']}
Время: {datetime.now().strftime('%H:%M:%S')}

📌 <b>Что дальше?</b>
"""
                
                after_keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "📁 Экспортировать в файл", "callback_data": f"delivery_file_{content_type}_{volume}_{topic}"},
                            {"text": "🔄 Новый запрос", "callback_data": "new_request"}
                        ]
                    ]
                }
                
                send_telegram_message(
                    chat_id=chat_id,
                    text=after_text,
                    reply_markup=after_keyboard
                )
                
                # Сохраняем в историю
                save_to_history(user_id, topic, content_type, volume, delivery)
                
                return {"ok": True}
            else:
                return result
            
        elif delivery == "file" and file_format:
            # Создаем и отправляем файл
            filename = f"{content_type}_{topic}_{timestamp}.{file_format}"
            
            if file_format == "txt":
                # Текстовый файл
                content_bytes = full_content.encode('utf-8')
                caption = f"📄 {CONTENT_TYPES[content_type]['name']}: {topic}"
                
            elif file_format == "pdf" and PDF_AVAILABLE:
                # PDF файл
                content_bytes = create_pdf_file(topic, full_content, content_type)
                caption = f"📄 PDF: {CONTENT_TYPES[content_type]['name']} - {topic}"
                
            elif file_format == "docx" and DOCX_AVAILABLE:
                # DOCX файл
                content_bytes = create_docx_file(topic, full_content, content_type)
                caption = f"📝 DOCX: {CONTENT_TYPES[content_type]['name']} - {topic}"
                
            elif file_format == "pptx" and content_type == "presentation":
                # Для презентаций пока отправляем TXT с инструкцией
                content_bytes = full_content.encode('utf-8')
                filename = f"presentation_instructions_{timestamp}.txt"
                caption = f"🎤 Инструкция для презентации: {topic}"
                
            else:
                # Если формат не поддерживается, отправляем TXT
                content_bytes = full_content.encode('utf-8')
                filename = f"{content_type}_{topic}_{timestamp}.txt"
                caption = f"📋 {CONTENT_TYPES[content_type]['name']}: {topic} (формат {file_format} временно недоступен)"
            
            # Отправляем файл
            result = send_telegram_document(
                chat_id=chat_id,
                filename=filename,
                content=content_bytes,
                caption=caption
            )
            
            if result.get("ok", False):
                # Сохраняем в историю
                save_to_history(user_id, topic, content_type, volume, f"file_{file_format}")
                
                # Отправляем сообщение об успехе
                success_text = f"""
✅ <b>Файл отправлен!</b>

📁 <b>Файл:</b> {filename}
📊 <b>Формат:</b> {file_format.upper()}
💾 <b>Размер:</b> {len(content_bytes) // 1024} КБ

🔧 <b>Создано для:</b> {device_info['icon']} {device_info['name']}

🔄 <b>Для нового запроса используйте /start</b>
"""
                
                send_telegram_message(chat_id=chat_id, text=success_text)
                return {"ok": True}
            else:
                error_text = f"❌ <b>Ошибка отправки файла</b>\n\nПопробуйте получить материал текстом или выберите другой формат."
                send_telegram_message(chat_id=chat_id, text=error_text)
                return result
        
        else:
            error_text = "❌ <b>Неизвестный метод доставки</b>\n\nИспользуйте /help для справки."
            return send_telegram_message(chat_id=chat_id, text=error_text)
            
    except Exception as e:
        logger.error(f"❌ Ошибка генерации контента: {e}")
        error_text = f"❌ <b>Произошла ошибка при генерации</b>\n\nОшибка: {str(e)[:100]}...\n\nПопробуйте изменить параметры запроса."
        return send_telegram_message(chat_id=chat_id, text=error_text)

def create_pdf_file(topic: str, content: str, content_type: str) -> bytes:
    """Создание PDF файла"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        
        # Заголовок
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, topic, 0, 1, 'C')
        pdf.ln(5)
        
        # Информация о документе
        pdf.set_font('DejaVu', 'I', 10)
        doc_type = CONTENT_TYPES[content_type]['name']
        pdf.cell(0, 10, f'Тип: {doc_type}', 0, 1)
        pdf.cell(0, 10, f'Дата: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
        pdf.ln(10)
        
        # Основной текст
        pdf.set_font('DejaVu', '', 12)
        
        # Обрабатываем HTML теги для простого форматирования
        lines = content.split('\n')
        for line in lines:
            # Убираем HTML теги
            clean_line = re.sub(r'<[^>]+>', '', line)
            if clean_line.strip():
                pdf.multi_cell(0, 10, clean_line)
        
        # Возвращаем PDF как байты
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания PDF: {e}")
        # Возвращаем текст как UTF-8 если PDF не удалось создать
        return f"PDF ERROR: {e}\n\n{content}".encode('utf-8')
def create_docx_file(topic: str, content: str, content_type: str) -> bytes:
    """Создание DOCX файла"""
    try:
        document = Document()
        
        # Заголовок
        title = document.add_heading(topic, level=0)
        title.alignment = 1  # Center alignment
        
        # Подзаголовок с информацией
        doc_type = CONTENT_TYPES[content_type]['name']
        subtitle = document.add_paragraph()
        subtitle_run = subtitle.add_run(f'Тип документа: {doc_type}')
        subtitle_run.italic = True
        
        date_info = document.add_paragraph()
        date_run = date_info.add_run(f'Дата создания: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
        date_run.italic = True
        
        document.add_paragraph()  # Пустая строка
        
        # Обрабатываем контент
        lines = content.split('\n')
        for line in lines:
            if not line.strip():
                document.add_paragraph()
                continue
                
            # Определяем стиль на основе форматирования
            if line.strip().startswith('<b>') and line.strip().endswith('</b>'):
                # Заголовок
                clean_line = re.sub(r'<[^>]+>', '', line)
                heading = document.add_heading(clean_line.strip(), level=1)
            elif '📊' in line or '📚' in line or '🎤' in line or '✍️' in line:
                # Подзаголовок с иконкой
                clean_line = re.sub(r'<[^>]+>', '', line)
                para = document.add_paragraph(clean_line)
                para.runs[0].bold = True
            elif line.strip().startswith('•') or line.strip().startswith('-'):
                # Список
                clean_line = re.sub(r'<[^>]+>', '', line)
                para = document.add_paragraph(style='List Bullet')
                para.add_run(clean_line.strip()[1:].strip())
            elif re.match(r'^\d+\.', line.strip()):
                # Нумерованный список
                clean_line = re.sub(r'<[^>]+>', '', line)
                para = document.add_paragraph(style='List Number')
                para.add_run(clean_line.strip()[2:].strip())
            else:
                # Обычный текст
                clean_line = re.sub(r'<[^>]+>', '', line)
                if clean_line.strip():
                    document.add_paragraph(clean_line)
        
        # Сохраняем в байты
        import io
        byte_io = io.BytesIO()
        document.save(byte_io)
        byte_io.seek(0)
        return byte_io.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания DOCX: {e}")
        # Возвращаем текст как UTF-8 если DOCX не удалось создать
        return f"DOCX ERROR: {e}\n\n{content}".encode('utf-8')

# ============ ОСНОВНЫЕ ФУНКЦИИ ВЕБХУКА ============
@app.route('/webhook', methods=['POST'])
def webhook():
    """Основной обработчик вебхука от Telegram"""
    try:
        data = request.get_json()
        
        if not data:
            logger.error("❌ Пустой запрос от Telegram")
            return jsonify({"ok": False, "error": "Empty request"}), 400
        
        logger.info(f"📥 Получен запрос: {data.get('update_id')}")
        
        # Проверяем тип обновления
        if "message" in data:
            handle_message(data["message"])
        elif "callback_query" in data:
            handle_callback(data["callback_query"])
        elif "edited_message" in data:
            logger.info(f"✏️ Редактирование сообщения: {data['edited_message'].get('message_id')}")
        else:
            logger.warning(f"⚠️ Неизвестный тип обновления: {data.keys()}")
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

def handle_message(message: dict):
    """Обработка входящего сообщения"""
    try:
        chat_id = message["chat"]["id"]
        user_id = str(message["from"]["id"])
        username = message["from"].get("username", message["from"].get("first_name", "Пользователь"))
        
        # Логируем полученное сообщение
        if "text" in message:
            text = message["text"]
            logger.info(f"📨 Сообщение от {username} ({user_id}): {text[:100]}...")
            
            # Обработка команд
            if text.startswith('/'):
                handle_command(chat_id, user_id, username, text)
            else:
                handle_user_message(chat_id, user_id, text)
        else:
            logger.info(f"📎 Не текстовое сообщение от {username}")
            send_telegram_message(
                chat_id=chat_id,
                text="❌ <b>Я работаю только с текстом</b>\n\nОтправьте мне текстовое сообщение с вашим запросом."
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        chat_id = message.get("chat", {}).get("id")
        if chat_id:
            send_telegram_message(
                chat_id=chat_id,
                text="❌ <b>Произошла ошибка при обработке вашего сообщения</b>\n\nПопробуйте еще раз или используйте /help для справки."
            )

def handle_command(chat_id: int, user_id: str, username: str, text: str):
    """Обработка команд"""
    command = text.lower().split()[0]
    
    if command == "/start":
        handle_start_command(chat_id, user_id, username)
    elif command == "/help":
        handle_help_command(chat_id)
    elif command == "/device":
        handle_device_command(chat_id, user_id)
    elif command == "/history":
        handle_history_command(chat_id, user_id)
    elif command == "/formats":
        handle_formats_command(chat_id)
    else:
        send_telegram_message(
            chat_id=chat_id,
            text="❌ <b>Неизвестная команда</b>\n\nДоступные команды:\n/start - Начать работу\n/help - Помощь\n/device - Изменить устройство\n/history - История запросов\n/formats - Доступные форматы"
        )

def handle_callback(callback_query: dict):
    """Обработка callback-запроса"""
    try:
        data = callback_query["data"]
        chat_id = callback_query["message"]["chat"]["id"]
        user_id = str(callback_query["from"]["id"])
        message_id = callback_query["message"]["message_id"]
        
        logger.info(f"🔘 Callback от пользователя {user_id}: {data}")
        
        # Обрабатываем callback
        handle_callback_query(data, chat_id, user_id, message_id)
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки callback: {e}")

# ============ НАСТРОЙКА И ЗАПУСК ============
def set_webhook():
    """Установка вебхука"""
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    webhook_url = os.environ.get('WEBHOOK_URL', '')
    
    if not webhook_url:
        logger.warning("⚠️ WEBHOOK_URL не установлен, используется polling")
        return False
    
    payload = {
        "url": webhook_url,
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query", "edited_message"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"✅ Вебхук установлен: {webhook_url}")
            return True
        else:
            logger.error(f"❌ Ошибка установки вебхука: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Исключение при установке вебхука: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья приложения"""
    return jsonify({
        "status": "healthy",
        "service": "Учебный бот премиум v9.0",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(user_devices),
        "history_entries": sum(len(h) for h in user_history.values())
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """Получение статистики"""
    stats = {
        "total_users": len(user_devices),
        "total_history_entries": sum(len(h) for h in user_history.values()),
        "pending_requests": len(pending_requests),
        "memory_usage_mb": len(str(user_devices)) // 1024 // 1024,
        "pdf_available": PDF_AVAILABLE,
        "docx_available": DOCX_AVAILABLE
    }
    
    # Статистика по устройствам
    device_stats = {}
    for device_id, device_info in DEVICES.items():
        count = sum(1 for dev in user_devices.values() if dev == device_id)
        device_stats[device_info["name"]] = count
    
    stats["devices"] = device_stats
    
    # Статистика по типам контента
    content_stats = {}
    for user_id, history in user_history.items():
        for entry in history:
            content_type = entry["type"]
            content_stats[content_type] = content_stats.get(content_type, 0) + 1
    
    stats["content_types"] = content_stats
    
    return jsonify(stats), 200

@app.route('/', methods=['GET'])
def index():
    """Главная страница"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎓 Учебный бот премиум v9.0</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 20px;
                text-align: center;
            }
            .status {
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .btn {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 12px 24px;
                border-radius: 50px;
                text-decoration: none;
                font-weight: bold;
                margin: 10px 5px;
                transition: transform 0.3s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                background: rgba(255, 255, 255, 0.15);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
            }
            .feature-icon {
                font-size: 2em;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Учебный бот премиум v9.0</h1>
            <div class="status">
                ✅ <strong>Сервер работает</strong><br>
                📊 Пользователей: """ + str(len(user_devices)) + """<br>
                📚 Запросов в истории: """ + str(sum(len(h) for h in user_history.values())) + """<br>
                🕐 Время: """ + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + """
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">📚</div>
                    <h3>Конспекты</h3>
                    <p>Структурированные учебные материалы</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📄</div>
                    <h3>Рефераты</h3>
                    <p>Научные работы с полной структурой</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🎤</div>
                    <h3>Презентации</h3>
                    <p>Слайды с дизайном и рекомендациями</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">✍️</div>
                    <h3>Эссе</h3>
                    <p>Аналитические сочинения</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/health" class="btn">Проверить здоровье</a>
                <a href="/stats" class="btn">Статистика</a>
                <a href="https://t.me/YourBotUsername" class="btn">Перейти к боту</a>
            </div>
            
            <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.8; text-align: center;">
                Версия 9.0 • Поддерживаемые форматы: PDF, DOCX, TXT • Адаптация под устройства
            </div>
        </div>
    </body>
    </html>
    """
     if __name__ == "__main__":
    # Настройка логирования
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК УЧЕБНОГО БОТА ПРЕМИУМ v9.0")
    logger.info("=" * 50)
    
    # Проверка зависимостей
    logger.info(f"📦 Зависимости: PDF {'✅' if PDF_AVAILABLE else '❌'}, DOCX {'✅' if DOCX_AVAILABLE else '❌'}")
    
    # Настройка вебхука
    webhook_set = set_webhook()
    
    if not webhook_set:
        logger.info("ℹ️ Вебхук не настроен, возможно используется polling")
    
    # Получение информации о боте
    try:
        bot_info_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(bot_info_url, timeout=5)
        bot_info = response.json()
        
        if bot_info.get("ok"):
            bot_name = bot_info["result"]["first_name"]
            bot_username = bot_info["result"]["username"]
            logger.info(f"🤖 Бот: {bot_name} (@{bot_username})")
        else:
            logger.error(f"❌ Ошибка получения информации о боте: {bot_info}")
    except Exception as e:
        logger.error(f"❌ Не удалось получить информацию о боте: {e}")
    
    # Запуск Flask приложения
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"🌐 Веб-сервер запущен на {host}:{port}")
    logger.info(f"📊 Статистика: /stats")
    logger.info(f"❤️  Проверка здоровья: /health")
    logger.info("=" * 50)
    logger.info("✅ Бот готов к работе! Ожидание запросов...")
    
    # Запуск приложения
    app.run(
        host=host,
        port=port,
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )
    # ============ HTML СТРАНИЦА ============
@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎓 Учебный Бот Премиум v9.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
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
        }
        
        .stats-box {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00c6ff;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Учебный Бот Премиум v9.0</h1>
        
        <div class="status">
            ✅ Активен 24/7 • Пользователей: ''' + str(len(user_devices)) + '''
        </div>
        
        <p style="font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; line-height: 1.6;">
            Интеллектуальный помощник для создания полноценных учебных материалов<br>
            с разными форматами и указанием объема в листах А4
        </p>
        
        <div class="stats-box">
            <div class="stat-item">
                <div class="stat-value">''' + str(len(user_devices)) + '''</div>
                <div class="stat-label">Пользователей</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">''' + str(sum(len(h) for h in user_history.values())) + '''</div>
                <div class="stat-label">Запросов</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">''' + str(len(pending_requests)) + '''</div>
                <div class="stat-label">В работе</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">4</div>
                <div class="stat-label">Типа контента</div>
            </div>
        </div>
        
        <div class="features-grid">
            <div class="feature">
                <span class="feature-icon">📚</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Конспекты</div>
                <div>Полноценные учебные материалы</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">🎤</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Презентации</div>
                <div>Структура слайдов с описанием</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📄</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Рефераты</div>
                <div>Научные работы со структурой</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📊</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Объем в листах</div>
                <div>Указывайте: "3 листа", "4л"</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📱</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Адаптация</div>
                <div>Телефон, компьютер, планшет</div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📁</span>
                <div style="font-weight: bold; margin-bottom: 10px;">Экспорт</div>
                <div>PDF, DOCX, TXT файлы</div>
            </div>
        </div>
        
        <div style="margin: 40px 0;">
            <a href="/health" class="btn" style="background: linear-gradient(45deg, #00b09b, #96c93d);">
                <span>❤️</span>
                Проверить работоспособность
            </a>
            <a href="/stats" class="btn" style="background: linear-gradient(45deg, #8e2de2, #4a00e0);">
                <span>📊</span>
                Статистика системы
            </a>
        </div>
        
        <div style="margin: 40px 0;">
            <a href="https://t.me/Konspekt_help_bot" class="btn" target="_blank">
                <span>📱</span>
                Открыть в Telegram
            </a>
        </div>
        
        <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            <p>🚀 Работает на Render.com | 📄 Объем в листах А4 | 🎤 3 шаблона презентаций</p>
            <p>📚 База знаний по темам | 🤖 AI-генерация | 📱 Адаптация под устройства</p>
            <p>🕐 Время сервера: ''' + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + '''</p>
        </div>
    </div>
</body>
</html>
'''

# ============ HEALTH CHECK ============
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "study-bot-premium-v9",
        "version": "9.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "full_content_generation",
            "volume_selection_a4", 
            "presentation_templates",
            "knowledge_base",
            "pdf_export",
            "docx_export",
            "device_optimization",
            "preview_generation",
            "history_tracking",
            "format_selection"
        ],
        "statistics": {
            "users": len(user_devices),
            "history_entries": sum(len(h) for h in user_history.values()),
            "pending_requests": len(pending_requests),
            "pdf_support": PDF_AVAILABLE,
            "docx_support": DOCX_AVAILABLE
        }
    }), 200

# ============ НАСТРОЙКА ВЕБХУКА ============
def setup_webhook():
    """Автоматическая настройка вебхука"""
    try:
        app_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '') or os.environ.get('WEBHOOK_URL', '')
        if not app_url:
            logger.warning("⚠️ WEBHOOK_URL не настроен, используется polling")
            return False
        
        webhook_url = f"https://{app_url}/webhook"
        
        logger.info(f"🔧 Настраиваю вебхук: {webhook_url}")
        
        # Удаляем старый вебхук
        delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        requests.get(delete_url, timeout=5)
        
        # Устанавливаем новый вебхук
        set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        payload = {
            "url": webhook_url,
            "drop_pending_updates": True,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query", "edited_message"]
        }
        
        response = requests.post(set_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Вебхук установлен: {webhook_url}")
            return True
        else:
            logger.error(f"❌ Ошибка вебхука: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка настройки вебхука: {e}")
        return False

# ============ ЗАПУСК ПРИЛОЖЕНИЯ ============
if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 ЗАПУСК УЧЕБНОГО БОТА ПРЕМИУМ v9.0")
    logger.info("=" * 80)
    logger.info(f"🤖 Токен бота: {TOKEN[:10]}...")
    logger.info(f"📦 Зависимости: PDF {'✅' if PDF_AVAILABLE else '❌'}, DOCX {'✅' if DOCX_AVAILABLE else '❌'}")
    logger.info("=" * 80)
    
    # Получение информации о боте
    try:
        bot_info_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(bot_info_url, timeout=5)
        bot_info = response.json()
        
        if bot_info.get("ok"):
            bot_name = bot_info["result"]["first_name"]
            bot_username = bot_info["result"]["username"]
            logger.info(f"🤖 Имя бота: {bot_name}")
            logger.info(f"🤖 Username: @{bot_username}")
        else:
            logger.error(f"❌ Ошибка получения информации о боте: {bot_info}")
    except Exception as e:
        logger.error(f"❌ Не удалось получить информацию о боте: {e}")
    
    # Настройка вебхука
    webhook_set = setup_webhook()
    
    if not webhook_set:
        logger.info("ℹ️ Вебхук не настроен, возможно используется polling")
    
    # Запуск Flask сервера
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🌍 Запуск на {host}:{port}")
    logger.info(f"🔧 Режим отладки: {'✅' if debug_mode else '❌'}")
    logger.info("=" * 80)
    logger.info("✅ Бот готов к работе! Ожидание запросов...")
    logger.info("=" * 80)
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=False,
        threaded=True
        )
