#!/usr/bin/env python3
"""
🎓 УЧЕБНЫЙ БОТ ПРЕМИУМ v9.0
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

# ============ БАЗЫ ДАННЫХ ============
user_devices = {}  # user_id -> device_type
user_settings = {}  # user_id -> settings
user_history = {}  # user_id -> list[history_entries]
pending_requests = {}  # user_id -> request_data
# ============ ФУНКЦИИ КЛАВИАТУР ============
def create_device_keyboard() -> dict:
    """Клавиатура для выбора устройства"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"{DEVICES['phone']['icon']} {DEVICES['phone']['name']}", "callback_data": "device_phone"},
                {"text": f"{DEVICES['pc']['icon']} {DEVICES['pc']['name']}", "callback_data": "device_pc"}
            ],
            [
                {"text": f"{DEVICES['tablet']['icon']} {DEVICES['tablet']['name']}", "callback_data": "device_tablet"},
                {"text": f"{DEVICES['watch']['icon']} {DEVICES['watch']['name']}", "callback_data": "device_watch"}
            ]
        ]
    }
    return keyboard

def create_content_type_keyboard() -> dict:
    """Клавиатура для выбора типа контента"""
    keyboard = {
        "inline_keyboard": []
    }
    
    for content_id, content_info in CONTENT_TYPES.items():
        keyboard["inline_keyboard"].append([{
            "text": f"{content_info['icon']} {content_info['name']}",
            "callback_data": f"type_{content_id}"
        }])
    
    return keyboard

def create_volume_keyboard(content_type: str = "conspect") -> dict:
    """Клавиатура для выбора объема"""
    keyboard = {"inline_keyboard": []}
    
    # Для презентаций ограничиваем объем
    if content_type == "presentation":
        volumes_to_show = ["3", "5", "7", "10", "12", "15"]
        volume_label = "слайдов"
    else:
        volumes_to_show = ["1", "2", "3", "5", "7", "10"]
        volume_label = "листов"
    
    row = []
    for vol in volumes_to_show:
        vol_info = VOLUME_LEVELS[vol] if vol in VOLUME_LEVELS else VOLUME_LEVELS["3"]
        row.append({
            "text": f"{vol_info['icon']} {vol} {volume_label}",
            "callback_data": f"volume_{content_type}_{vol}"
        })
        if len(row) == 2:
            keyboard["inline_keyboard"].append(row)
            row = []
    
    if row:
        keyboard["inline_keyboard"].append(row)
    
    return keyboard

def create_delivery_keyboard(content_type: str, volume: str, topic: str) -> dict:
    """Клавиатура для выбора формата доставки"""
    keyboard = {
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
    return keyboard

def create_format_keyboard(content_type: str, volume: str, topic: str) -> dict:
    """Клавиатура для выбора формата файла"""
    keyboard = {
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
        keyboard["inline_keyboard"][0].append(
            {"text": "🎨 PPTX", "callback_data": f"format_pptx_{content_type}_{volume}_{topic}"}
        )
    
    keyboard["inline_keyboard"].append([
        {"text": "🔙 Назад", "callback_data": f"delivery_text_{content_type}_{volume}_{topic}"}
    ])
    
    return keyboard

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
    text_lower = text.lower().strip()
    
    if not text_lower:
        return "", "conspect", "3"
    
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
        r'(\d+)\s*слайд[аов]*',
        r'\b(\d+)\s*$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            vol = match.group(1)
            if vol.isdigit() and 1 <= int(vol) <= 15:
                volume = vol
            break
    
    # Извлекаем тему - берем весь текст и убираем только ключевые слова объема
    topic = text_lower
    
    # Убираем слова с объемом
    for pattern in patterns:
        topic = re.sub(pattern, '', topic)
    
    # Убираем слова типа контента
    type_words = ["конспект", "реферат", "презентация", "эссе", "по", "о", "на", "теме", "тема", "про"]
    for word in type_words:
        topic = topic.replace(word, '')
    
    # Очищаем пробелы и лишние символы
    topic = re.sub(r'[^\w\sа-яА-ЯёЁ-]', '', topic)  # Оставляем только буквы, цифры, пробелы и дефисы
    topic = re.sub(r'\s+', ' ', topic).strip()
    
    # Если тема пустая, берем оригинальный текст без команд
    if not topic:
        # Убираем только команды, оставляем всё остальное
        clean_text = text
        for word in ["конспект", "реферат", "презентация", "эссе"]:
            clean_text = clean_text.lower().replace(word, '')
        topic = clean_text.strip()
    
    return topic[:200], content_type, volume

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
  # ============ ОБРАБОТКА КОМАНД ============
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
    
    logger.info(f"🔍 Парсинг запроса: текст='{text}', тема='{topic}', тип='{content_type}', объем='{volume}'")
    
    if not topic or len(topic) < 2:
        return send_telegram_message(
            chat_id=chat_id,
            text="❌ <b>Не удалось определить тему</b>\n\nПожалуйста, укажите тему более четко.\n\n<b>Примеры:</b>\n<code>конспект по философии</code>\n<code>реферат на тему экология 3 листа</code>\n<code>презентация про математику 10 слайдов</code>"
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
    
    # Сохраняем запрос в ожидании
    pending_requests[user_id] = {
        "topic": topic,
        "content_type": content_type,
        "volume": volume,
        "timestamp": datetime.now().isoformat(),
        "chat_id": chat_id
    }
    
    # Получаем информацию о типе контента и объеме
    content_info = CONTENT_TYPES[content_type]
    volume_info = VOLUME_LEVELS[volume] if volume in VOLUME_LEVELS else VOLUME_LEVELS["3"]
    
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
    delivery_keyboard = create_delivery_keyboard(content_type, volume, topic)
    
    return send_telegram_message(
        chat_id=chat_id,
        text=preview_message,
        reply_markup=delivery_keyboard
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
      # ============ ОБРАБОТКА CALLBACK-ЗАПРОСОВ ============
def handle_callback_query(callback_data: str, chat_id: int, user_id: str, message_id: int) -> dict:
    """Обработка callback-запросов от кнопок"""
    
    # Удаляем предыдущую клавиатуру
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/editMessageReplyMarkup"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []}
        }
        requests.post(url, json=payload, timeout=3)
    except:
        pass  # Игнорируем ошибку если не удалось удалить клавиатуру
    
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
        reply_markup=create_volume_keyboard(content_type)
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
    volume_info = VOLUME_LEVELS[volume] if volume in VOLUME_LEVELS else VOLUME_LEVELS["3"]
    
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
    format_text = f"""
📁 <b>ВЫБОР ФОРМАТА ФАЙЛА</b>

Тема: <b>{topic.replace('_', ' ')}</b>
Тип: {CONTENT_TYPES[content_type]['icon']} {content_type}
Объем: {VOLUME_LEVELS[volume]['icon']} {volume}

Выберите формат для скачивания:
"""
    
    return send_telegram_message(
        chat_id=chat_id,
        text=format_text,
        reply_markup=create_format_keyboard(content_type, volume, topic)
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
        # Декодируем тему (заменяем подчеркивания пробелами)
        decoded_topic = topic.replace('_', ' ')
        
        # Отправляем сообщение о начале генерации
        process_msg = send_telegram_message(
            chat_id=chat_id,
            text=f"⏳ <b>Генерирую {CONTENT_TYPES[content_type]['name'].lower()}...</b>\nТема: {decoded_topic}\nЭто займет несколько секунд."
        )
        
        # Получаем информацию об устройстве
        device_type = user_devices.get(user_id, "phone")
        device_info = DEVICES[device_type]
        
        # Генерируем контент
        try:
            volume_int = int(volume)
        except:
            volume_int = 3
            
        if content_type == "presentation":
            template = user_settings.get(user_id, {}).get("presentation_template", "academic")
            full_content = generate_full_content(decoded_topic, content_type, volume_int, template)
        else:
            full_content = generate_full_content(decoded_topic, content_type, volume_int)
        
        # Определяем текущее время для меток
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if delivery == "text":
            # Отправляем текстом
            result = send_telegram_message(
                chat_id=chat_id,
                text=full_content
            )
            
            if result.get("ok", False):
                # Добавляем кнопки после текста
                after_text = f"""
✅ <b>Материал готов!</b>

📊 <b>Итог:</b>
Тема: {decoded_topic}
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
                save_to_history(user_id, decoded_topic, content_type, volume, delivery)
                
                return {"ok": True}
            else:
                return result
            
        elif delivery == "file" and file_format:
            # Создаем файл
            filename = f"{content_type}_{decoded_topic}_{timestamp}.{file_format}"
            filename = re.sub(r'[^\w\sа-яА-ЯёЁ.-]', '', filename)  # Очищаем имя файла
            
            # Для простоты всегда отправляем TXT (реализацию PDF/DOCX можно добавить позже)
            content_bytes = full_content.encode('utf-8')
            caption = f"📄 {CONTENT_TYPES[content_type]['name']}: {decoded_topic}"
            
            # Отправляем файл
            result = send_telegram_document(
                chat_id=chat_id,
                filename=filename,
                content=content_bytes,
                caption=caption
            )
            
            if result.get("ok", False):
                # Сохраняем в историю
                save_to_history(user_id, decoded_topic, content_type, volume, f"file_{file_format}")
                
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
                error_text = f"❌ <b>Ошибка отправки файла</b>\n\nПопробуйте получить материал текстом."
                send_telegram_message(chat_id=chat_id, text=error_text)
                return result
        
        else:
            error_text = "❌ <b>Неизвестный метод доставки</b>\n\nИспользуйте /help для справки."
            return send_telegram_message(chat_id=chat_id, text=error_text)
            
    except Exception as e:
        logger.error(f"❌ Ошибка генерации контента: {e}")
        error_text = f"❌ <b>Произошла ошибка при генерации</b>\n\nОшибка: {str(e)[:100]}...\n\nПопробуйте изменить параметры запроса."
        return send_telegram_message(chat_id=chat_id, text=error_text)

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
      # ============ HTML СТРАНИЦА ============
@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Конспект Хелпер Бот - @Konspekt_help_bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 40px 20px;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        
        .bot-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .bot-info {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .bot-avatar {
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #FF6B6B, #FFD93D);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5em;
        }
        
        .bot-details h2 {
            margin-bottom: 5px;
        }
        
        .bot-username {
            color: #FFD93D;
            font-size: 1.2em;
            font-weight: bold;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature {
            background: rgba(255, 255, 255, 0.08);
            padding: 20px;
            border-radius: 15px;
            transition: transform 0.3s;
        }
        
        .feature:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.12);
        }
        
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .btn {
            display: inline-block;
            background: linear-gradient(45deg, #00b09b, #96c93d);
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 1.2em;
            font-weight: bold;
            margin: 20px 10px;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(0, 176, 155, 0.4);
            text-align: center;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(0, 176, 155, 0.6);
        }
        
        .btn-telegram {
            background: linear-gradient(45deg, #0088cc, #00c6ff);
            box-shadow: 0 5px 15px rgba(0, 136, 204, 0.4);
        }
        
        .btn-telegram:hover {
            box-shadow: 0 8px 20px rgba(0, 136, 204, 0.6);
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        
        .stat {
            text-align: center;
            padding: 15px 25px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            min-width: 120px;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #FFD93D;
            margin-bottom: 5px;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .telegram-link {
            font-size: 1.3em;
            margin: 20px 0;
            padding: 15px;
            background: rgba(0, 136, 204, 0.2);
            border-radius: 10px;
            border: 2px solid #0088cc;
        }
        
        @media (max-width: 768px) {
            .bot-info {
                flex-direction: column;
                text-align: center;
            }
            
            .features {
                grid-template-columns: 1fr;
            }
            
            .stats {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Конспект Хелпер Бот</h1>
            <p class="subtitle">@Konspekt_help_bot - создание учебных материалов</p>
        </header>
        
        <div class="bot-card">
            <div class="bot-info">
                <div class="bot-avatar">
                    📚
                </div>
                <div class="bot-details">
                    <h2>Конспект Хелпер Бот</h2>
                    <div class="bot-username">@Konspekt_help_bot</div>
                    <p>Умный помощник для студентов и преподавателей</p>
                </div>
            </div>
            
            <div class="telegram-link">
                🔗 <strong>Ссылка на бота:</strong> 
                <a href="https://t.me/Konspekt_help_bot" style="color: #FFD93D; text-decoration: none;">
                    https://t.me/Konspekt_help_bot
                </a>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">4</div>
                    <div>Типа контента</div>
                </div>
                <div class="stat">
                    <div class="stat-number">10</div>
                    <div>Объемов А4</div>
                </div>
                <div class="stat">
                    <div class="stat-number">3</div>
                    <div>Формата файлов</div>
                </div>
                <div class="stat">
                    <div class="stat-number">24/7</div>
                    <div>Работает</div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://t.me/Konspekt_help_bot" class="btn btn-telegram" target="_blank">
                    📱 Открыть в Telegram
                </a>
                <a href="/health" class="btn">
                    ❤️ Статус сервера
                </a>
            </div>
        </div>
        
        <h2 style="text-align: center; margin: 40px 0 20px 0;">✨ Что умеет бот</h2>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📚</div>
                <h3>Конспекты</h3>
                <p>Структурированные учебные материалы по любой теме. Указывайте объем в листах А4.</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📄</div>
                <h3>Рефераты</h3>
                <p>Полноценные научные работы с введением, основной частью и заключением.</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🎤</div>
                <h3>Презентации</h3>
                <p>Структура слайдов с описанием дизайна и рекомендациями по выступлению.</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">✍️</div>
                <h3>Эссе</h3>
                <p>Аналитические сочинения с аргументацией и личной позицией.</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📱</div>
                <h3>Для всех устройств</h3>
                <p>Адаптируется под телефон, компьютер, планшет или смарт-часы.</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📁</div>
                <h3>Экспорт файлов</h3>
                <p>Скачивайте материалы в форматах PDF, DOCX или обычным текстом.</p>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <h3>🎯 Как использовать</h3>
            <p style="margin: 15px 0; opacity: 0.9;">
                Просто напишите боту: <strong>"конспект по философии 3 листа"</strong><br>
                Или: <strong>"презентация на тему экология 10 слайдов"</strong>
            </p>
            
            <div style="background: rgba(255, 255, 255, 0.08); padding: 20px; border-radius: 15px; margin: 20px 0;">
                <h4>📌 Прямая ссылка для перехода:</h4>
                <p style="font-size: 1.1em;">
                    <a href="https://t.me/Konspekt_help_bot" style="color: #00c6ff; text-decoration: none; font-weight: bold;">
                        👉 t.me/Konspekt_help_bot
                    </a>
                </p>
                <p style="opacity: 0.8; margin-top: 10px;">
                    Нажмите ссылку выше или отсканируйте QR-код
                </p>
            </div>
            
            <a href="https://t.me/Konspekt_help_bot" class="btn btn-telegram" target="_blank" style="font-size: 1.3em; padding: 18px 50px;">
                🚀 Начать пользоваться ботом
            </a>
        </div>
        
        <footer>
            <p>© 2024 Конспект Хелпер Бот (@Konspekt_help_bot)</p>
            <p>Создание учебных материалов стало проще | Версия 9.0</p>
            <p>Работает на Python + Flask | Автоматическая генерация контента</p>
            <p style="margin-top: 10px;">
                <strong>Техническая информация:</strong> 
                <a href="/health" style="color: #FFD93D;">Статус</a> | 
                <a href="/stats" style="color: #FFD93D;">Статистика</a>
            </p>
        </footer>
    </div>
</body>
</html>
'''

# ============ HEALTH CHECK ============
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "Учебный бот премиум v9.0",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(user_devices),
        "history_entries": sum(len(h) for h in user_history.values()),
        "pending_requests": len(pending_requests)
    }), 200

@app.route('/stats')
def stats():
    """Статистика"""
    stats_data = {
        "total_users": len(user_devices),
        "total_history_entries": sum(len(h) for h in user_history.values()),
        "pending_requests": len(pending_requests),
        "devices": {},
        "content_types": {}
    }
    
    # Статистика по устройствам
    for device_id, device_info in DEVICES.items():
        count = sum(1 for dev in user_devices.values() if dev == device_id)
        stats_data["devices"][device_info["name"]] = count
    
    # Статистика по типам контента
    for user_id, history in user_history.items():
        for entry in history:
            content_type = entry["type"]
            stats_data["content_types"][content_type] = stats_data["content_types"].get(content_type, 0) + 1
    
    return jsonify(stats_data), 200

# ============ НАСТРОЙКА ВЕБХУКА ============
def setup_webhook():
    """Автоматическая настройка вебхука"""
    try:
        app_url = os.environ.get('RENDER_EXTERNAL_URL', '') or os.environ.get('WEBHOOK_URL', '')
        if not app_url:
            logger.warning("⚠️ WEBHOOK_URL не настроен, используется polling")
            return False
        
        webhook_url = f"https://{app_url}/webhook"
        
        logger.info(f"🔧 Настраиваю вебхук: {webhook_url}")
        
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
