#!/usr/bin/env python3
"""
🎓 УЧЕБНЫЙ БОТ ПРЕМИУМ v8.0 - ИСПРАВЛЕННАЯ ВЕРСИЯ
С полноценным контентом и разными форматами
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
import threading

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
export_queue = {}
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

# ============ ОБЪЕМ В ЛИСТАХ А4 ============
VOLUME_LEVELS = {
    "1": {"icon": "📄", "name": "1 лист", "pages": 1, "words": "300-400"},
    "2": {"icon": "📄📄", "name": "2 листа", "pages": 2, "words": "600-800"},
    "3": {"icon": "📄📄📄", "name": "3 листа", "pages": 3, "words": "900-1200"},
    "4": {"icon": "📄📄📄📄", "name": "4 листа", "pages": 4, "words": "1200-1600"},
    "5": {"icon": "📄📄📄📄📄", "name": "5 листов", "pages": 5, "words": "1500-2000"},
    "6": {"icon": "📚", "name": "6 листов", "pages": 6, "words": "1800-2400"},
    "7": {"icon": "📚📄", "name": "7 листов", "pages": 7, "words": "2100-2800"},
    "8": {"icon": "📚📚", "name": "8 листов", "pages": 8, "words": "2400-3200"},
    "9": {"icon": "📚📚📄", "name": "9 листов", "pages": 9, "words": "2700-3600"},
    "10": {"icon": "📘", "name": "10 листов", "pages": 10, "words": "3000-4000"}
}

# ============ БАЗА ЗНАНИЙ ПО ТЕМАМ ============
KNOWLEDGE_BASE = {
    "семья": {
        "definition": "Семья - это социальная группа, основанная на браке или кровном родстве, связанная общностью быта и взаимной ответственностью.",
        "sections": [
            {
                "title": "Понятие и признаки семьи",
                "content": [
                    "Малая социальная группа",
                    "Основана на браке или родстве",
                    "Совместное проживание и ведение хозяйства",
                    "Взаимная поддержка и ответственность",
                    "Эмоциональные связи между членами"
                ]
            },
            {
                "title": "Функции семьи",
                "content": [
                    "Репродуктивная - продолжение рода",
                    "Воспитательная - социализация детей",
                    "Хозяйственная - организация быта",
                    "Эмоциональная - психологическая поддержка",
                    "Социальная - передача ценностей"
                ]
            },
            {
                "title": "Типы семей",
                "content": [
                    "Нуклеарная (родители + дети)",
                    "Расширенная (несколько поколений)",
                    "Полная / неполная",
                    "Многодетная / малодетная",
                    "Традиционная / современная"
                ]
            }
        ]
    },
    "экология": {
        "definition": "Экология - наука о взаимоотношениях живых организмов между собой и с окружающей средой.",
        "sections": [
            {
                "title": "Основные понятия",
                "content": [
                    "Экосистема - сообщество организмов",
                    "Биосфера - глобальная экосистема",
                    "Популяция - группа одного вида",
                    "Сообщество - разные виды в одной среде"
                ]
            },
            {
                "title": "Экологические проблемы",
                "content": [
                    "Загрязнение воздуха и воды",
                    "Изменение климата",
                    "Уничтожение лесов",
                    "Исчезновение видов",
                    "Накопление отходов"
                ]
            }
        ]
    },
    "математика": {
        "definition": "Математика - наука о количественных отношениях и пространственных формах действительного мира.",
        "sections": [
            {
                "title": "Основные разделы",
                "content": [
                    "Алгебра - уравнения и функции",
                    "Геометрия - пространственные формы",
                    "Математический анализ - пределы и производные",
                    "Теория вероятностей - случайные события"
                ]
            }
        ]
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
    },
    "educational": {
        "name": "Образовательная",
        "style": "Интерактивный стиль для обучения",
        "color_scheme": "Зеленый, синий, оранжевый",
        "font": "Roboto, Lato"
    }
}

# ============ УТИЛИТЫ ============
def get_user_device(user_id: str) -> dict:
    """Получение устройства пользователя"""
    return DEVICES.get(user_devices.get(user_id, "phone"), DEVICES["phone"])

def save_to_history(user_id: str, topic: str, content_type: str, volume: str = "3"):
    """Сохранение в историю"""
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append({
        "topic": topic,
        "type": content_type,
        "volume": volume,
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

def parse_volume_from_text(text: str) -> tuple:
    """Извлечение объема из текста запроса - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    text_lower = text.lower()
    
    # Сначала ищем полные паттерны
    patterns = [
        r'(\d+)\s*лист[аов]*\s*а4',
        r'(\d+)\s*лист[аов]*',
        r'(\d+)\s*л\s*а4',
        r'(\d+)\s*л\b',
        r'(\d+)\s*стр[аиц]*\s*а4',
        r'(\d+)\s*стр[аиц]*',
        r'\b(\d+)\s*$',
    ]
    
    volume = None
    clean_text = text
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            volume = match.group(1)
            # Убираем найденный паттерн из оригинального текста
            start = text_lower.find(match.group(0))
            end = start + len(match.group(0))
            clean_text = text[:start] + text[end:]
            break
    
    # Если объем не найден, проверяем есть ли просто цифра
    if not volume:
        match = re.search(r'\b(\d+)\b', text_lower)
        if match:
            # Проверяем, что это не часть слова
            pos = match.start()
            if (pos == 0 or not text_lower[pos-1].isalpha()) and \
               (pos + len(match.group()) == len(text_lower) or not text_lower[pos + len(match.group())].isalpha()):
                volume = match.group(1)
    
    # Очищаем текст
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Определяем тип контента
    content_type = "conspect"
    if "презентация" in clean_text.lower() or "слайд" in clean_text.lower():
        content_type = "presentation"
        # Убираем эти слова для чистоты темы
        clean_text = re.sub(r'презентация|слайд[ов]*', '', clean_text.lower()).strip()
    elif "реферат" in clean_text.lower():
        content_type = "referat"
        clean_text = re.sub(r'реферат|по', '', clean_text.lower()).strip()
    elif "конспект" in clean_text.lower():
        clean_text = re.sub(r'конспект', '', clean_text.lower()).strip()
    elif "эссе" in clean_text.lower():
        content_type = "essay"
        clean_text = re.sub(r'эссе', '', clean_text.lower()).strip()
    
    # Убираем лишние предлоги и союзы
    clean_text = re.sub(r'^о|об|на|по|теме|тема\s*', '', clean_text).strip()
    
    # Объем по умолчанию
    if not volume:
        if content_type == "presentation":
            volume = "10"
        elif content_type == "referat":
            volume = "4"
        elif content_type == "essay":
            volume = "3"
        else:
            volume = "3"
    
    # Проверяем корректность объема
    try:
        volume_int = int(volume)
        if volume_int > 10:
            volume = "10"
        elif volume_int < 1:
            volume = "1"
    except:
        volume = "3"
    
    return clean_text, volume, content_type

def generate_sources(topic: str, count: int = 5) -> list:
    """Генерация списка источников"""
    base_sources = [
        "Учебник по социологии (А.И. Кравченко, 2020)",
        "Научный журнал 'Социологические исследования'",
        "Энциклопедия 'Большая Российская'",
        "Курс лекций МГУ по социальным наукам",
        "Материалы Российской академии наук",
        "Международный журнал социальных наук",
        "Сборник научных трудов 'Семья и общество'",
        "Демографический ежегодник России"
    ]
    
    # Выбираем случайные источники
    sources = random.sample(base_sources, min(count, len(base_sources)))
    
    # Добавляем тематические
    topic_lower = topic.lower()
    if "семья" in topic_lower:
        sources.append("Семейный кодекс Российской Федерации")
        sources.append("Исследования Института демографии")
    
    return sources[:count]
    # ============ ОТПРАВКА СООБЩЕНИЙ ============
def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML", 
                         reply_markup: dict = None) -> dict:
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
                "disable_web_page_preview": True
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
def generate_ai_content(topic: str, content_type: str = "conspect", 
                       device_type: str = "phone", volume_pages: int = 3,
                       presentation_template: str = "academic") -> str:
    """Генерация полноценного контента в зависимости от типа"""
    
    volume_key = str(volume_pages)
    volume_info = VOLUME_LEVELS.get(volume_key, VOLUME_LEVELS["3"])
    device_info = DEVICES.get(device_type, DEVICES["phone"])
    content_type_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES["conspect"])
    
    # Заголовок
    content = []
    content.append(f"{content_type_info['icon']} <b>{content_type_info['name'].upper()}: {topic.upper()}</b>")
    content.append("")
    content.append(f"📊 <b>ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:</b>")
    content.append(f"• Объем: {volume_info['icon']} {volume_info['name']}")
    
    if content_type == "presentation":
        content.append(f"• Слайдов: {volume_pages}")
        template_info = PRESENTATION_TEMPLATES.get(presentation_template, PRESENTATION_TEMPLATES["academic"])
        content.append(f"• Шаблон: {template_info['name']}")
        content.append(f"• Стиль: {template_info['style']}")
    else:
        content.append(f"• Слов: {volume_info['words']}")
    
    content.append(f"• Устройство: {device_info['icon']} {device_info['name']}")
    content.append(f"• Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    content.append("")
    
    # ГЕНЕРАЦИЯ РАЗНОГО КОНТЕНТА ДЛЯ РАЗНЫХ ТИПОВ
    if content_type == "conspect":
        content.extend(generate_full_conspect(topic, volume_pages))
    
    elif content_type == "referat":
        content.extend(generate_full_referat(topic, volume_pages))
    
    elif content_type == "presentation":
        content.extend(generate_presentation_content(topic, volume_pages, presentation_template))
    
    elif content_type == "essay":
        content.extend(generate_full_essay(topic, volume_pages))
    
    # Источники (не для презентаций)
    if content_type != "presentation":
        content.append("")
        content.append("📚 <b>ИСТОЧНИКИ ИНФОРМАЦИИ:</b>")
        sources = generate_sources(topic, min(volume_pages + 2, 8))
        for i, source in enumerate(sources, 1):
            content.append(f"{i}. {source}")
    
    # Рекомендации
    content.append("")
    content.append("💡 <b>РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ:</b>")
    
    if content_type == "conspect":
        content.append("• Используйте для подготовки к занятиям")
        content.append("• Дополняйте своими примерами и заметками")
        content.append("• Структурируйте материал по разделам")
        content.append("• Регулярно повторяйте для лучшего запоминания")
    
    elif content_type == "presentation":
        content.append(f"• Время выступления: {volume_pages * 1.5:.1f} минут")
        content.append("• 1 слайд = 1 ключевая идея")
        content.append("• Минимум текста, максимум визуальных элементов")
        content.append("• Используйте графики, диаграммы и качественные изображения")
        content.append("• Репетируйте выступление несколько раз")
        content.append("• Подготовьте ответы на возможные вопросы")
    
    elif content_type == "referat":
        content.append("• Проверьте актуальность указанных источников")
        content.append("• Соблюдайте академический стиль изложения")
        content.append("• Оформите работу по требованиям вашего учебного заведения")
        content.append("• Добавьте собственные выводы и анализ")
    
    elif content_type == "essay":
        content.append("• Развивайте собственную точку зрения")
        content.append("• Подкрепляйте аргументы примерами и цитатами")
        content.append("• Следите за логикой и структурой изложения")
        content.append("• Проверьте грамотность и стиль")
    
    # Советы по устройству
    if device_type == "phone":
        content.append("")
        content.append("📱 <b>СОВЕТ ДЛЯ ТЕЛЕФОНА:</b>")
        content.append("• Сохраните в заметки для быстрого доступа")
        content.append("• Используйте режим чтения для удобства")
        content.append("• Поделитесь с одногруппниками")
    
    return "\n".join(content)

def generate_full_conspect(topic: str, volume_pages: int) -> list:
    """Генерация полноценного конспекта с содержанием"""
    content = []
    
    # Получаем информацию по теме
    topic_lower = topic.lower()
    topic_info = None
    
    for key in KNOWLEDGE_BASE:
        if key in topic_lower:
            topic_info = KNOWLEDGE_BASE[key]
            break
    
    if not topic_info:
        # Если темы нет в базе, создаем общую структуру
        topic_info = {
            "definition": f"{topic.capitalize()} - важная тема для изучения, требующая детального рассмотрения.",
            "sections": [
                {
                    "title": "Основные понятия и определения",
                    "content": [
                        "Ключевые термины и их значения",
                        "Основные характеристики и свойства",
                        "Важность и актуальность изучения"
                    ]
                },
                {
                    "title": "Теоретические основы",
                    "content": [
                        "Фундаментальные принципы",
                        "Законы и закономерности",
                        "Научные подходы и теории"
                    ]
                }
            ]
        }
    
    content.append("<b>📖 СОДЕРЖАНИЕ КОНСПЕКТА:</b>")
    content.append("")
    
    # 1. Определение
    content.append("<b>1. ОПРЕДЕЛЕНИЕ И СУЩНОСТЬ</b>")
    content.append(topic_info["definition"])
    content.append("")
    
    # 2. Основные разделы
    for i, section in enumerate(topic_info["sections"], 2):
        if i > 2 and volume_pages < 3:
            break  # Для маленьких объемов ограничиваем количество разделов
        
        content.append(f"<b>{i}. {section['title'].upper()}</b>")
        for j, item in enumerate(section["content"], 1):
            content.append(f"{j}. {item}")
        content.append("")
        
        # Для большего объема добавляем подробности
        if volume_pages >= 4 and i == 2:
            content.append("<i>Подробное объяснение:</i>")
            content.append("Данный аспект требует детального изучения, так как является фундаментальным для понимания всей темы.")
            content.append("")
    
    # 3. Практическое применение
    if volume_pages >= 3:
        content.append(f"<b>{len(topic_info['sections']) + 2}. ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ</b>")
        content.append("• Примеры использования в реальной жизни")
        content.append("• Практические задания и упражнения")
        content.append("• Связь с другими дисциплинами")
        content.append("")
    
    # 4. Выводы
    content.append(f"<b>{len(topic_info['sections']) + 3}. ВЫВОДЫ И РЕКОМЕНДАЦИИ</b>")
    content.append("• Ключевые моменты для запоминания")
    content.append("• Рекомендации для дальнейшего изучения")
    content.append("• Практическая значимость материала")
    
    return content

def generate_full_referat(topic: str, volume_pages: int) -> list:
    """Генерация полноценного реферата"""
    content = []
    
    content.append("<b>📄 СТРУКТУРА РЕФЕРАТА:</b>")
    content.append("")
    
    # Титульный лист
    content.append("<b>1. ТИТУЛЬНЫЙ ЛИСТ</b>")
    content.append("• Название учебного заведения")
    content.append(f"• Тема: «{topic}»")
    content.append("• ФИО студента")
    content.append("• ФИО преподавателя")
    content.append("• Город, год")
    content.append("")
    
    # Оглавление
    content.append("<b>2. ОГЛАВЛЕНИЕ</b>")
    content.append("• Введение..........................стр. 1")
    content.append("• Основная часть....................стр. 2-4")
    content.append("• Заключение.......................стр. 5")
    content.append("• Список литературы.................стр. 6")
    content.append("")
    
    # Введение
    content.append("<b>3. ВВЕДЕНИЕ</b>")
    content.append(f"Актуальность темы «{topic}» обусловлена её важностью в современном обществе.")
    content.append("Цель работы: изучить основные аспекты данной темы.")
    content.append("Задачи:")
    content.append("1. Рассмотреть теоретические основы")
    content.append("2. Проанализировать ключевые положения")
    content.append("3. Сделать выводы и рекомендации")
    content.append("")
    
    # Основная часть
    content.append("<b>4. ОСНОВНАЯ ЧАСТЬ</b>")
    
    chapters = min(3, max(2, volume_pages - 3))
    for i in range(1, chapters + 1):
        content.append("")
        content.append(f"<b>4.{i}. Глава {i}</b>")
        content.append(f"В данной главе рассматриваются основные аспекты темы, связанные с {['теоретическими основами', 'практическим применением', 'анализом результатов'][i-1]}.")
        content.append(f"Ключевые моменты главы {i}:")
        content.append("• Важный аспект 1")
        content.append("• Важный аспект 2")
        content.append("• Важный аспект 3")
    
    # Заключение
    content.append("")
    content.append("<b>5. ЗАКЛЮЧЕНИЕ</b>")
    content.append(f"В результате исследования темы «{topic}» были сделаны следующие выводы:")
    content.append("1. Вывод 1 с обоснованием")
    content.append("2. Вывод 2 с обоснованием")
    content.append("3. Вывод 3 с обоснованием")
    content.append("")
    content.append("Работа имеет практическую значимость для...")
    
    return content

def generate_presentation_content(topic: str, slides_count: int, template: str = "academic") -> list:
    """Генерация структуры презентации"""
    content = []
    
    template_info = PRESENTATION_TEMPLATES.get(template, PRESENTATION_TEMPLATES["academic"])
    
    content.append("<b>🎤 СТРУКТУРА ПРЕЗЕНТАЦИИ:</b>")
    content.append(f"Шаблон: {template_info['name']}")
    content.append(f"Цветовая схема: {template_info['color_scheme']}")
    content.append(f"Шрифты: {template_info['font']}")
    content.append("")
    
    # Генерируем слайды
    slides = [
        {"title": "Титульный слайд", "content": ["Название презентации", f"Тема: {topic}", "ФИО автора", "Дата"]},
        {"title": "Содержание", "content": ["План презентации", "Ключевые разделы", "Ожидаемые результаты"]},
        {"title": "Актуальность темы", "content": ["Почему эта тема важна", "Статистика или факты", "Проблематика"]},
        {"title": "Цели и задачи", "content": ["Основная цель", "Конкретные задачи", "Ожидаемые результаты"]},
        {"title": "Теоретические основы", "content": ["Основные понятия", "Ключевые теории", "Научные подходы"]},
        {"title": "Практическая часть", "content": ["Методы исследования", "Полученные данные", "Анализ результатов"]},
        {"title": "Результаты", "content": ["Ключевые выводы", "Графики и диаграммы", "Сравнительный анализ"]},
        {"title": "Заключение", "content": ["Основные выводы", "Рекомендации", "Перспективы"]},
        {"title": "Спасибо за внимание!", "content": ["Вопросы?", "Контакты", "Дополнительные материалы"]}
    ]
    
    # Ограничиваем количество слайдов
    slides = slides[:min(slides_count, len(slides))]
    
    for i, slide in enumerate(slides, 1):
        content.append(f"<b>Слайд {i}: {slide['title']}</b>")
        
        # Содержание слайда
        for item in slide["content"]:
            content.append(f"• {item}")
        
        # Рекомендации по оформлению
        if i == 1:
            content.append("<i>Рекомендации: крупный заголовок, минимальный текст</i>")
        elif i == len(slides):
            content.append("<i>Рекомендации: контактная информация, призыв к вопросам</i>")
        elif "график" in slide["title"].lower() or "результат" in slide["title"].lower():
            content.append("<i>Рекомендации: используйте диаграммы, минимум текста</i>")
        
        content.append("")
    
    # Общие рекомендации
    content.append("<b>🎯 ОБЩИЕ РЕКОМЕНДАЦИИ:</b>")
    content.append(f"• Количество слайдов: {len(slides)}")
    content.append(f"• Примерное время: {len(slides) * 1.5:.1f} минут")
    content.append("• 1 слайд = 1 основная идея")
    content.append("• Шрифт заголовков: 32-44pt")
    content.append("• Шрифт основного текста: 24-28pt")
    content.append("• Используйте единый стиль всех слайдов")
    content.append("• Проверьте контрастность текста и фона")
    
    return content

def generate_full_essay(topic: str, volume_pages: int) -> list:
    """Генерация полноценного эссе"""
    content = []
    
    content.append("<b>✍️ СТРУКТУРА ЭССЕ:</b>")
    content.append("")
    
    # Вступление
    content.append("<b>1. ВСТУПЛЕНИЕ (10-15% объема)</b>")
    content.append(f"Тема «{topic}» представляет значительный интерес для современного общества.")
    content.append("В данном эссе будут рассмотрены ключевые аспекты этой темы.")
    content.append("Основной тезис: [формулируйте вашу основную идею здесь]")
    content.append("")
    
    # Основная часть
    paragraphs = min(5, max(3, volume_pages * 2))
    content.append(f"<b>2. ОСНОВНАЯ ЧАСТЬ ({paragraphs} абзацев)</b>")
    
    for i in range(1, paragraphs + 1):
        content.append("")
        content.append(f"<b>Абзац {i}:</b>")
        content.append("Основная мысль абзаца: [опишите ключевую идею]")
        content.append("Аргументы:")
        content.append("• Аргумент 1 с обоснованием")
        content.append("• Аргумент 2 с примером")
        content.append("• Связь с основным тезисом")
    
    # Заключение
    content.append("")
    content.append("<b>3. ЗАКЛЮЧЕНИЕ</b>")
    content.append("В заключении следует:")
    content.append("• Обобщить основные идеи")
    content.append("• Подтвердить или развить основной тезис")
    content.append("• Представить собственные размышления")
    content.append("• Указать перспективы дальнейшего исследования")
    
    return content
    # ============ СОЗДАНИЕ ФАЙЛОВ ============
def create_txt_file(topic: str, content: str, content_type: str) -> tuple:
    """Создание TXT файла"""
    import re
    
    # Убираем HTML теги
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    # Заголовок файла
    file_content = "=" * 60 + "\n"
    file_content += f"{CONTENT_TYPES[content_type]['name'].upper()}: {topic.upper()}\n"
    file_content += "=" * 60 + "\n\n"
    file_content += clean_content
    file_content += f"\n\n{'=' * 60}\n"
    file_content += f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    file_content += f"Бот: @Konspekt_help_bot\n"
    file_content += "=" * 60
    
    filename = f"{content_type}_{topic[:30].replace(' ', '_')}.txt"
    return filename, file_content.encode('utf-8')

def create_pdf_file(topic: str, content: str, content_type: str) -> tuple:
    """Создание PDF файла"""
    import re
    
    if not PDF_AVAILABLE:
        return create_txt_file(topic, content, content_type)
    
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Заголовок
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"{CONTENT_TYPES[content_type]['name'].upper()}: {topic.upper()}", ln=1, align='C')
        pdf.ln(5)
        
        # Линия
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # Контент
        pdf.set_font("Arial", size=12)
        
        # Убираем HTML теги
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Разбиваем на строки
        lines = clean_content.split('\n')
        for line in lines:
            if line.strip():
                if line.strip().startswith('=') or any(x in line for x in ['СОДЕРЖАНИЕ', 'ПАРАМЕТРЫ', 'ИСТОЧНИКИ', 'РЕКОМЕНДАЦИИ']):
                    pdf.ln(5)
                    pdf.set_font("Arial", 'B', 14)
                    pdf.multi_cell(0, 10, txt=line.strip())
                    pdf.set_font("Arial", size=12)
                else:
                    pdf.multi_cell(0, 8, txt=line)
            else:
                pdf.ln(5)
        
        # Подвал
        pdf.ln(10)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, txt=f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=1, align='C')
        pdf.cell(200, 10, txt="Бот: @Konspekt_help_bot", ln=1, align='C')
        
        filename = f"{content_type}_{topic[:30].replace(' ', '_')}.pdf"
        return filename, pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания PDF: {e}")
        return create_txt_file(topic, content, content_type)

def create_docx_file(topic: str, content: str, content_type: str) -> tuple:
    """Создание DOCX файла"""
    import re
    from io import BytesIO
    
    if not DOCX_AVAILABLE:
        return create_txt_file(topic, content, content_type)
    
    try:
        doc = Document()
        
        # Заголовок
        title = doc.add_heading(f'{CONTENT_TYPES[content_type]["name"].upper()}: {topic.upper()}', 0)
        title.alignment = 1
        
        # Контент
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        for line in clean_content.split('\n'):
            if line.strip():
                if line.strip().startswith('=') or any(x in line for x in ['СОДЕРЖАНИЕ', 'ПАРАМЕТРЫ', 'ИСТОЧНИКИ']):
                    doc.add_heading(line.strip(), level=1)
                elif line.strip().startswith('•'):
                    doc.add_paragraph(line.strip())
                elif any(line.strip().startswith(x) for x in ['1.', '2.', '3.', '4.', '5.']):
                    doc.add_paragraph(line.strip())
                else:
                    doc.add_paragraph(line.strip())
        
        # Подвал
        doc.add_paragraph()
        doc.add_paragraph(f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        doc.add_paragraph("Бот: @Konspekt_help_bot")
        
        file_stream = BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        filename = f"{content_type}_{topic[:30].replace(' ', '_')}.docx"
        return filename, file_stream.read()
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания DOCX: {e}")
        return create_txt_file(topic, content, content_type)
        # ============ ОБРАБОТЧИКИ КОМАНД ============
def handle_start_command(chat_id: int, username: str, user_id: str):
    """Обработка команды /start"""
    welcome_text = f"""👋 <b>Добро пожаловать, {username}!</b>

🎓 <b>УЧЕБНЫЙ БОТ ПРЕМИУМ v8.0</b>
📄 <b>С ПОЛНОЦЕННЫМ КОНТЕНТОМ И РАЗНЫМИ ФОРМАТАМИ</b>

<b>✨ ВОЗМОЖНОСТИ:</b>
• 📚 <b>Конспекты</b> - полноценные учебные материалы
• 🎤 <b>Презентации</b> - структура слайдов с описанием
• 📄 <b>Рефераты</b> - научные работы со структурой
• ✍️ <b>Эссе</b> - аналитические сочинения
• 📊 <b>Объем в листах А4</b> - от 1 до 10 листов

<b>🚀 КАК РАБОТАЕТ:</b>
1. Напишите запрос с указанием объема
2. Бот создает полноценный материал
3. Получаете структурированный контент
4. Скачиваете в нужном формате

<b>📝 ФОРМАТ ЗАПРОСОВ:</b>
<code>[тип] [тема] [объем]</code>

<b>🎯 ПРИМЕРЫ:</b>
<code>конспект семья 3 листа</code>
<code>презентация экология 5 слайдов</code>
<code>реферат математика 4л</code>
<code>эссе философия 2 страницы</code>

<b>🤖 КОМАНДЫ:</b>
• /help - полная справка
• /volume - выбрать объем
• /presentation - создать презентацию
• /export - скачать файл
• /history - история запросов
• /settings - настройки

<i>Начните с запроса с указанием объема!</i>"""
    
    send_telegram_message(chat_id, welcome_text)

def handle_help_command(chat_id: int):
    """Обработка команды /help"""
    help_text = """🆘 <b>ПОЛНАЯ СПРАВКА ПО БОТУ v8.0</b>

<b>📋 ДОСТУПНЫЕ ТИПЫ МАТЕРИАЛОВ:</b>

1. <b>📚 Конспект</b>
   • Полноценный учебный материал
   • Структурированное содержание
   • Ключевые понятия и определения
   • Примеры и практические задания

2. <b>🎤 Презентация</b>
   • Структура слайдов с описанием
   • 4 готовых шаблона
   • Рекомендации по оформлению
   • Расчет времени выступления

3. <b>📄 Реферат</b>
   • Научная структура работы
   • Введение, основная часть, заключение
   • Список литературы
   • Требования к оформлению

4. <b>✍️ Эссе</b>
   • Аналитическая структура
   • Аргументация и примеры
   • Логика изложения
   • Критерии оценки

<b>📊 ФОРМАТ ЗАПРОСОВ:</b>
<code>[тип] [тема] [объем] [доп. параметры]</code>

<b>🎯 ПРИМЕРЫ:</b>
<code>конспект семья 4 листа</code>
<code>презентация экология 8 слайдов бизнес</code>
<code>реферат математика 5л</code>
<code>эссе философия 3 страницы</code>

<b>🎤 ШАБЛОНЫ ПРЕЗЕНТАЦИЙ:</b>
• <b>academic</b> - академический (по умолчанию)
• <b>business</b> - бизнес-презентация
• <b>creative</b> - креативный дизайн
• <b>educational</b> - образовательный стиль

<b>📄 ЭКСПОРТ ФАЙЛОВ:</b>
• PDF - готов к печати
• DOCX - для редактирования
• TXT - простой текст

<b>📱 АДАПТАЦИЯ:</b>
• Телефон - компактный формат
• Компьютер - полная версия
• Планшет - промежуточный вариант
• Часы - краткая версия

<b>🤖 КОМАНДЫ:</b>
• /start - начать работу
• /help - эта справка
• /volume - выбор объема
• /presentation - презентации
• /export - скачать файл
• /history - история
• /settings - настройки

<i>Для начала напишите запрос с указанием объема</i>"""
    
    send_telegram_message(chat_id, help_text)

def handle_volume_command(chat_id: int, user_id: str):
    """Обработка команды /volume"""
    current_volume = user_settings.get(f"{user_id}_volume", "3")
    volume_info = VOLUME_LEVELS[current_volume]
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "1л", "callback_data": "volume_1"},
                {"text": "2л", "callback_data": "volume_2"}, 
                {"text": "3л", "callback_data": "volume_3"},
                {"text": "4л", "callback_data": "volume_4"}
            ],
            [
                {"text": "5л", "callback_data": "volume_5"},
                {"text": "6л", "callback_data": "volume_6"},
                {"text": "8л", "callback_data": "volume_8"},
                {"text": "10л", "callback_data": "volume_10"}
            ]
        ]
    }
    
    volume_text = f"""📄 <b>ВЫБОР ОБЪЕМА РАБОТЫ</b>

Текущий объем: {volume_info['icon']} <b>{volume_info['name']}</b>
📝 Слов: {volume_info['words']}

<b>🎯 РЕКОМЕНДАЦИИ ПО ОБЪЕМУ:</b>
• 1-2 листа - краткий конспект, тезисы
• 3-4 листа - стандартный материал
• 5-6 листов - подробный анализ
• 7-10 листов - исследовательская работа

<b>📝 ПРИМЕРЫ ЗАПРОСОВ:</b>
<code>конспект тема 3 листа</code>
<code>реферат предмет 4л</code>
<code>презентация проект 8 слайдов</code>

<i>Нажмите на кнопку или напишите количество листов</i>"""
    
    user_settings[f"{user_id}_awaiting_volume"] = True
    send_telegram_message(chat_id, volume_text, reply_markup=keyboard)

def handle_presentation_command(chat_id: int, user_id: str):
    """Обработка команды /presentation"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🎓 Академическая", "callback_data": "presentation_academic"},
                {"text": "💼 Бизнес", "callback_data": "presentation_business"}
            ],
            [
                {"text": "🎨 Креативная", "callback_data": "presentation_creative"},
                {"text": "📚 Образовательная", "callback_data": "presentation_educational"}
            ]
        ]
    }
    
    presentation_text = """🎤 <b>СОЗДАНИЕ ПРЕЗЕНТАЦИИ</b>

<b>Выберите шаблон презентации:</b>

• <b>🎓 Академическая</b>
  <i>Для научных работ, дипломов, курсовых</i>
  <i>Строгий стиль, логическая структура</i>

• <b>💼 Бизнес-презентация</b>
  <i>Для проектов, стартапов, отчетов</i>
  <i>Корпоративный стиль, акцент на результатах</i>

• <b>🎨 Креативная</b>
  <i>Для творческих проектов, портфолио</i>
  <i>Современный дизайн, визуальные эффекты</i>

• <b>📚 Образовательная</b>
  <i>Для уроков, лекций, семинаров</i>
  <i>Интерактивные элементы, вопросы</i>

<b>📝 ФОРМАТ ЗАПРОСА:</b>
<code>презентация [тема] [слайды] [шаблон]</code>

<b>ПРИМЕРЫ:</b>
<code>презентация экология 10 слайдов академическая</code>
<code>презентация стартап 12 бизнес</code>
<code>презентация искусство 8 креативная</code>

<i>Нажмите на кнопку шаблона или напишите полный запрос</i>"""
    
    send_telegram_message(chat_id, presentation_text, reply_markup=keyboard)

def handle_export_command(chat_id: int, user_id: str):
    """Обработка команды /export"""
    last_topic = user_settings.get(f"{user_id}_last_topic", None)
    
    if not last_topic:
        send_telegram_message(chat_id,
            "📊 <b>ЭКСПОРТ МАТЕРИАЛА</b>\n\n"
            "У вас пока нет сохраненных материалов.\n\n"
            "<i>Сначала создайте материал:</i>\n"
            "<code>конспект тема 3 листа</code>\n"
            "→ получите полноценный контент\n"
            "→ используйте /export для скачивания"
        )
        return
    
    user_settings[f"{user_id}_awaiting_export"] = True
    
    export_text = f"""📊 <b>ЭКСПОРТ МАТЕРИАЛА</b>

Тема: <b>{last_topic}</b>
Тип: <b>{CONTENT_TYPES.get(user_settings.get(f'{user_id}_last_type', 'conspect'), CONTENT_TYPES['conspect'])['name']}</b>

<b>Выберите формат файла (напишите цифру):</b>

1. <b>📄 PDF</b> - для печати и чтения
   <i>Сохраняет форматирование, готов к печати</i>

2. <b>📝 DOCX</b> - для редактирования  
   <i>Можно редактировать в Word, Google Docs</i>

3. <b>📋 TXT</b> - простой текст
   <i>Совместим со всеми устройствами</i>

<b>Особенности:</b>
• Все форматы включают полноценный контент
• PDF готов к отправке на печать
• DOCX можно дорабатывать и редактировать
• TXT - минимальный размер, максимальная совместимость

<i>Напишите цифру от 1 до 3:</i>
<code>1</code> (PDF), <code>2</code> (DOCX) или <code>3</code> (TXT)"""
    
    send_telegram_message(chat_id, export_text)

def handle_ai_command(chat_id: int, user_id: str = None):
    """Обработка команды /ai"""
    ai_text = """🤖 <b>AI-ГЕНЕРАЦИЯ МАТЕРИАЛОВ</b>

<b>Доступные типы материалов:</b>

• <b>📚 Конспект</b> - полноценные учебные заметки
  <i>Структурированный материал с содержанием</i>

• <b>📄 Реферат</b> - научная работа  
  <i>Академическая структура, список литературы</i>

• <b>🎤 Презентация</b> - структура слайдов
  <i>Готовые шаблоны, рекомендации по оформлению</i>

• <b>✍️ Эссе</b> - аналитическое сочинение
  <i>Логическая структура, аргументация</i>

<b>📝 ФОРМАТ ЗАПРОСА:</b>
<code>[тип] [тема] [объем]</code>

<b>ПРИМЕРЫ:</b>
<code>конспект математика 3 листа</code>
<code>реферат физика 4л</code>  
<code>презентация экология 10 слайдов</code>
<code>эссе философия 2 страницы</code>

<b>🎯 УКАЗЫВАЙТЕ ОБЪЕМ:</b>
• В листах А4: 1, 2, 3, 4, 5...
• В слайдах: 5, 8, 10, 12...
• Сокращения: 3л, 4листа, 5страниц

<i>Напишите запрос в нужном формате</i>"""
    
    send_telegram_message(chat_id, ai_text)

def handle_history_command(chat_id: int, user_id: str):
    """Обработка команды /history"""
    history = user_history.get(user_id, [])
    
    if not history:
        send_telegram_message(chat_id,
            "📜 <b>ИСТОРИЯ ЗАПРОСОВ</b>\n\n"
            "История запросов пуста.\n\n"
            "<i>Создайте первый материал:</i>\n"
            "<code>конспект тема 3 листа</code>"
        )
        return
    
    # Показываем последние 5 запросов
    recent = history[-5:]
    history_text = "📜 <b>ПОСЛЕДНИЕ ЗАПРОСЫ</b>\n\n"
    
    for i, item in enumerate(reversed(recent), 1):
        item_type = CONTENT_TYPES.get(item.get("type", "conspect"), CONTENT_TYPES["conspect"])
        volume = item.get("volume", "3")
        volume_info = VOLUME_LEVELS.get(volume, VOLUME_LEVELS["3"])
        
        timestamp = datetime.fromisoformat(item["timestamp"]).strftime("%d.%m %H:%M")
        
        history_text += f"{i}. <b>{item_type['icon']} {item['topic']}</b>\n"
        history_text += f"   📊 {volume_info['name']} | ⏰ {timestamp}\n\n"
    
    if len(history) > 5:
        history_text += f"<i>Показано 5 из {len(history)} запросов</i>\n\n"
    
    history_text += (
        "<b>Для повторной генерации:</b>\n"
        "Просто напишите тему заново\n\n"
        "<b>Очистка истории:</b>\n"
        "В настройках /settings"
    )
    
    send_telegram_message(chat_id, history_text)

def handle_settings_command(chat_id: int, user_id: str):
    """Обработка команды /settings"""
    current_device = user_devices.get(user_id, "phone")
    device_info = DEVICES[current_device]
    
    current_volume = user_settings.get(f"{user_id}_volume", "3")
    volume_info = VOLUME_LEVELS[current_volume]
    
    history_count = len(user_history.get(user_id, []))
    
    settings_text = f"""⚙️ <b>НАСТРОЙКИ БОТА v8.0</b>

<b>Текущие настройки:</b>
• 📱 Устройство: <b>{device_info['icon']} {device_info['name']}</b>
• 📊 Объем по умолчанию: <b>{volume_info['icon']} {volume_info['name']}</b>
• 📜 История запросов: <b>{history_count}</b>

<b>Доступные действия:</b>

1. <b>Сменить устройство</b>
   Напишите: <code>телефон</code>, <code>компьютер</code>

2. <b>Изменить объем</b>
   Команда: /volume

3. <b>Очистить историю</b>
   Напишите: <code>очистить историю</code>

4. <b>Сбросить настройки</b>
   Напишите: <code>сбросить настройки</code>

<b>Техническая информация:</b>
• Версия бота: 8.0.0
• Платформа: Render.com
• Режим работы: 24/7
• Статус: активен ✅

<i>Для изменения напишите команду или действие</i>"""
    
    send_telegram_message(chat_id, settings_text)
    # ============ ОБРАБОТКА ЗАПРОСОВ ============
def handle_content_request(chat_id: int, user_id: str, text: str):
    """Основная обработка запросов пользователя"""
    
    # Парсим запрос
    clean_text, volume, content_type = parse_volume_from_text(text)
    
    if not clean_text.strip():
        send_telegram_message(chat_id,
            "❌ <b>Не указана тема</b>\n\n"
            "<b>Правильный формат:</b>\n"
            "<code>[тип] [тема] [объем]</code>\n\n"
            "<b>Примеры:</b>\n"
            "<code>конспект семья 3 листа</code>\n"
            "<code>презентация экология 10 слайдов</code>"
        )
        return
    
    topic = clean_text.strip()
    
    # Сохраняем настройки
    user_settings[f"{user_id}_volume"] = volume
    
    # Определяем шаблон презентации
    presentation_template = "academic"
    if content_type == "presentation":
        # Ищем шаблон в тексте
        for template in PRESENTATION_TEMPLATES.keys():
            if template in text.lower():
                presentation_template = template
                user_settings[f"{user_id}_presentation_template"] = template
                break
    
    # Генерируем и отправляем
    generate_and_send_content(chat_id, user_id, topic, content_type, int(volume), presentation_template)

def generate_and_send_content(chat_id: int, user_id: str, topic: str, 
                            content_type: str = "conspect", volume_pages: int = 3,
                            presentation_template: str = None):
    """Генерация и отправка контента"""
    
    device_type = user_devices.get(user_id, "phone")
    content_type_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES["conspect"])
    volume_info = VOLUME_LEVELS.get(str(volume_pages), VOLUME_LEVELS["3"])
    
    # Статус генерации
    status_msg = (
        f"🔄 <b>ГЕНЕРАЦИЯ {content_type_info['name'].upper()}</b>\n\n"
        f"📝 Тема: <i>{topic}</i>\n"
        f"📊 Объем: {volume_info['icon']} <b>{volume_info['name']}</b>\n"
    )
    
    if content_type == "presentation":
        template_info = PRESENTATION_TEMPLATES.get(presentation_template, PRESENTATION_TEMPLATES["academic"])
        status_msg += f"🎤 Шаблон: <b>{template_info['name']}</b>\n"
        status_msg += f"📈 Слайдов: <b>{volume_pages}</b>\n\n"
    else:
        status_msg += f"📝 Слов: <b>{volume_info['words']}</b>\n\n"
    
    status_msg += "<i>Создаю полноценный материал...</i>"
    
    send_telegram_message(chat_id, status_msg)
    time.sleep(1)  # Имитация обработки
    
    # Генерируем контент
    content = generate_ai_content(topic, content_type, device_type, volume_pages, presentation_template)
    
    # Отправляем контент
    logger.info(f"📤 Отправляю {content_type} в чат {chat_id}")
    send_telegram_message(chat_id, content)
    
    # Сохраняем для экспорта
    user_settings[f"{user_id}_last_topic"] = topic
    user_settings[f"{user_id}_last_content"] = content
    user_settings[f"{user_id}_last_type"] = content_type
    user_settings[f"{user_id}_last_volume"] = str(volume_pages)
    
    if presentation_template:
        user_settings[f"{user_id}_last_template"] = presentation_template
    
    save_to_history(user_id, topic, content_type, str(volume_pages))
    
    # Предлагаем экспорт
    keyboard = {
        "inline_keyboard": [[
            {"text": "📥 Скачать файл", "callback_data": "export_menu"},
            {"text": "🔄 Новый материал", "callback_data": "new_topic"}
        ]]
    }
    
    final_text = (
        f"✅ <b>{content_type_info['name']} готов!</b>\n\n"
        f"<b>ПАРАМЕТРЫ МАТЕРИАЛА:</b>\n"
        f"• Тема: {topic}\n"
        f"• Тип: {content_type_info['name']}\n"
    )
    
    if content_type == "presentation":
        final_text += f"• Слайдов: {volume_pages}\n"
        if presentation_template:
            template_info = PRESENTATION_TEMPLATES.get(presentation_template, PRESENTATION_TEMPLATES["academic"])
            final_text += f"• Шаблон: {template_info['name']}\n"
    else:
        final_text += f"• Листов А4: {volume_pages}\n"
        final_text += f"• Слов: {volume_info['words']}\n"
    
    final_text += f"• Устройство: {get_user_device(user_id)['name']}\n\n"
    
    final_text += (
        "<b>ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:</b>\n"
        "1 - Скачать файл (/export)\n"
        "2 - Новый материал\n"
        "3 - Изменить настройки (/settings)\n\n"
        "<i>Напишите цифру или используйте кнопки</i>"
    )
    
    send_telegram_message(chat_id, final_text, reply_markup=keyboard)

def handle_export_format(chat_id: int, user_id: str, export_format: str):
    """Обработка выбора формата экспорта"""
    last_topic = user_settings.get(f"{user_id}_last_topic", "Тема")
    last_content = user_settings.get(f"{user_id}_last_content", "")
    last_type = user_settings.get(f"{user_id}_last_type", "conspect")
    
    format_info = EXPORT_FORMATS.get(export_format, EXPORT_FORMATS["txt"])
    
    # Убираем состояние ожидания
    user_settings[f"{user_id}_awaiting_export"] = False
    
    send_telegram_message(chat_id, f"🔄 <b>Создаю {format_info['name']} файл...</b>")
    
    try:
        # Создаем файл
        if export_format == "txt":
            filename, file_content = create_txt_file(last_topic, last_content, last_type)
        
        elif export_format == "pdf":
            filename, file_content = create_pdf_file(last_topic, last_content, last_type)
        
        elif export_format == "docx":
            filename, file_content = create_docx_file(last_topic, last_content, last_type)
        
        else:
            filename, file_content = create_txt_file(last_topic, last_content, last_type)
        
        # Отправляем файл
        caption = (
            f"{format_info['icon']} <b>{format_info['name']} {CONTENT_TYPES[last_type]['name']}:</b> {last_topic}\n\n"
            f"📅 Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"📊 Включает полноценный контент\n"
            f"🤖 Бот: @Konspekt_help_bot"
        )
        
        response = send_telegram_document(
            chat_id=chat_id,
            filename=filename,
            content=file_content,
            caption=caption
        )
        
        if response.get("ok"):
            send_telegram_message(chat_id,
                f"✅ <b>Файл успешно отправлен!</b>\n\n"
                f"Формат: {format_info['icon']} {format_info['name']}\n"
                f"Тема: {last_topic}\n"
                f"Тип: {CONTENT_TYPES[last_type]['name']}\n"
                f"Размер: {len(file_content) // 1024} KB\n\n"
                f"<i>Для нового материала напишите запрос</i>"
            )
        else:
            send_telegram_message(chat_id,
                f"❌ <b>Ошибка отправки файла</b>\n\n"
                f"Попробуйте другой формат."
            )
            
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        send_telegram_message(chat_id,
            f"❌ <b>Ошибка создания файла</b>\n\n"
            f"Попробуйте другой формат.\n"
            f"<i>Ошибка: {str(e)[:50]}</i>"
                             )
        # ============ CALLBACK ОБРАБОТЧИКИ ============
def handle_volume_callback(callback_data: str, chat_id: int, user_id: str):
    """Обработка callback для выбора объема"""
    if callback_data.startswith('volume_'):
        volume = callback_data.split('_')[1]
        if volume in VOLUME_LEVELS:
            volume_info = VOLUME_LEVELS[volume]
            user_settings[f"{user_id}_volume"] = volume
            
            send_telegram_message(chat_id,
                f"✅ <b>Объем установлен: {volume_info['icon']} {volume_info['name']}</b>\n\n"
                f"📄 Листов А4: {volume_info['pages']}\n"
                f"📝 Слов: {volume_info['words']}\n\n"
                f"<i>Теперь напишите запрос с темой:</i>\n"
                f"<code>конспект ваша_тема {volume}л</code>\n"
                f"<code>реферат предмет {volume} листа</code>"
            )

def handle_presentation_callback(callback_data: str, chat_id: int, user_id: str):
    """Обработка callback для выбора шаблона презентации"""
    if callback_data.startswith('presentation_'):
        template = callback_data.split('_')[1]
        template_info = PRESENTATION_TEMPLATES.get(template, PRESENTATION_TEMPLATES["academic"])
        
        user_settings[f"{user_id}_presentation_template"] = template
        
        send_telegram_message(chat_id,
            f"✅ <b>Шаблон установлен: {template_info['name']}</b>\n\n"
            f"🎨 Стиль: {template_info['style']}\n"
            f"🎨 Цвета: {template_info['color_scheme']}\n"
            f"📝 Шрифты: {template_info['font']}\n\n"
            f"<i>Теперь напишите запрос:</i>\n"
            f"<code>презентация ваша_тема 10 слайдов</code>\n"
            f"Или просто: <code>презентация тема 12</code>"
        )

def handle_export_callback(callback_data: str, chat_id: int, user_id: str):
    """Обработка callback для экспорта"""
    if callback_data == "export_menu":
        handle_export_command(chat_id, user_id)
    elif callback_data == "new_topic":
        send_telegram_message(chat_id,
            "🔄 <b>Создание нового материала</b>\n\n"
            "<i>Напишите запрос с указанием объема:</i>\n\n"
            "<b>Примеры:</b>\n"
            "<code>конспект новая_тема 3 листа</code>\n"
            "<code>презентация проект 10 слайдов бизнес</code>\n"
            "<code>реферат предмет 4л</code>"
        )

# ============ ОБРАБОТКА ТЕКСТОВЫХ КОМАНД ============
def handle_text_commands(chat_id: int, user_id: str, text: str):
    """Обработка текстовых команд"""
    text_lower = text.lower()
    
    # Очистка истории
    if text_lower in ['очистить историю', 'clear history', 'удалить историю']:
        if user_id in user_history:
            user_history[user_id] = []
        send_telegram_message(chat_id, "🗑️ <b>История очищена</b>")
    
    # Сброс настроек
    elif text_lower in ['сбросить настройки', 'reset settings', 'default']:
        for key in list(user_settings.keys()):
            if key.startswith(user_id):
                del user_settings[key]
        send_telegram_message(chat_id, "🔄 <b>Настройки сброшены</b>")
    
    # Выбор устройства
    elif text_lower in ['телефон', 'phone', 'смартфон']:
        user_devices[user_id] = "phone"
        send_telegram_message(chat_id, "✅ <b>Устройство: Телефон</b>")
    
    elif text_lower in ['компьютер', 'комп', 'pc', 'ноутбук']:
        user_devices[user_id] = "pc"
        send_telegram_message(chat_id, "✅ <b>Устройство: Компьютер</b>")
    
    elif text_lower in ['планшет', 'tablet']:
        user_devices[user_id] = "tablet"
        send_telegram_message(chat_id, "✅ <b>Устройство: Планшет</b>")
    
    elif text_lower in ['часы', 'watch']:
        user_devices[user_id] = "watch"
        send_telegram_message(chat_id, "✅ <b>Устройство: Часы</b>")
    
    # Цифровые команды после генерации
    elif text in ['1', '2', '3']:
        if user_settings.get(f"{user_id}_awaiting_export"):
            format_map = {"1": "pdf", "2": "docx", "3": "txt"}
            handle_export_format(chat_id, user_id, format_map[text])
        elif user_settings.get(f"{user_id}_awaiting_volume"):
            volume = text
            if volume in VOLUME_LEVELS:
                volume_info = VOLUME_LEVELS[volume]
                user_settings[f"{user_id}_volume"] = volume
                user_settings[f"{user_id}_awaiting_volume"] = False
                send_telegram_message(chat_id,
                    f"✅ <b>Объем: {volume_info['name']}</b>\n"
                    f"<i>Теперь напишите тему</i>"
                )
    
    # Обычный запрос
    else:
        handle_content_request(chat_id, user_id, text)

# ============ ВЕБХУК TELEGRAM ============
@app.route('/' + TOKEN, methods=['POST'])
def telegram_webhook():
    """Основной обработчик вебхука"""
    try:
        data = request.json
        logger.info(f"📨 Получен вебхук")
        
        # Обрабатываем сообщение
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            username = message['from'].get('first_name', 'Пользователь')
            text = message.get('text', '').strip()
            
            logger.info(f"👤 [{username}] → {text}")
            
            # Основные команды
            if text == '/start':
                handle_start_command(chat_id, username, user_id)
            
            elif text == '/help':
                handle_help_command(chat_id)
            
            elif text == '/volume':
                handle_volume_command(chat_id, user_id)
            
            elif text == '/presentation':
                handle_presentation_command(chat_id, user_id)
            
            elif text == '/export':
                handle_export_command(chat_id, user_id)
            
            elif text == '/ai':
                handle_ai_command(chat_id, user_id)
            
            elif text == '/history':
                handle_history_command(chat_id, user_id)
            
            elif text == '/settings':
                handle_settings_command(chat_id, user_id)
            
            # Обработка текстовых сообщений
            elif text and not text.startswith('/'):
                handle_text_commands(chat_id, user_id, text)
            
            # Неизвестная команда
            elif text.startswith('/'):
                send_telegram_message(chat_id,
                    "❓ <b>Неизвестная команда</b>\n\n"
                    "Используйте:\n"
                    "• /start - начать\n"
                    "• /help - справка\n"
                    "• /volume - объем\n"
                    "• /presentation - презентация\n"
                    "• /export - скачать\n\n"
                    "<i>Или напишите запрос с объемом</i>"
                )
            
            # Пустое сообщение
            else:
                send_telegram_message(chat_id,
                    "📝 <b>Напишите запрос!</b>\n\n"
                    "<b>Примеры:</b>\n"
                    "• конспект семья 3 листа\n"
                    "• презентация экология 10 слайдов\n"
                    "• реферат математика 4л\n\n"
                    "<i>Используйте /help для справки</i>"
                )
        
        # Обработка callback query (кнопки)
        elif 'callback_query' in data:
            callback = data['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            user_id = str(callback['from']['id'])
            callback_data = callback['data']
            
            # Ответ на callback
            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", 
                         json={"callback_query_id": callback_id})
            
            # Обработка callback данных
            if callback_data.startswith('volume_'):
                handle_volume_callback(callback_data, chat_id, user_id)
            
            elif callback_data.startswith('presentation_'):
                handle_presentation_callback(callback_data, chat_id, user_id)
            
            elif callback_data in ['export_menu', 'new_topic']:
                handle_export_callback(callback_data, chat_id, user_id)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
        # ============ HTML СТРАНИЦА ============
@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎓 Учебный Бот Премиум v8.0</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Учебный Бот Премиум v8.0</h1>
        
        <div class="status">
            ✅ Активен на Render 24/7
        </div>
        
        <p style="font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; line-height: 1.6;">
            Интеллектуальный помощник для создания полноценных учебных материалов<br>
            с разными форматами и указанием объема в листах А4
        </p>
        
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
            <a href="https://t.me/Konspekt_help_bot" class="btn" target="_blank">
                <span>📱</span>
                Открыть в Telegram
            </a>
        </div>
        
        <div style="margin-top: 40px; padding-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            <p>🚀 Работает на Render.com | 📄 Объем в листах А4 | 🎤 4 шаблона презентаций</p>
            <p>📚 База знаний по темам | 🤖 AI-генерация | 📱 Адаптация под устройства</p>
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
        "service": "study-bot-premium-v8",
        "version": "8.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "full_content_generation",
            "volume_selection_a4", 
            "presentation_templates",
            "knowledge_base",
            "pdf_export",
            "docx_export",
            "device_optimization"
        ]
    }), 200

# ============ НАСТРОЙКА ВЕБХУКА ============
def setup_webhook():
    """Автоматическая настройка вебхука"""
    try:
        app_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'study-bot.onrender.com')
        webhook_url = f"https://{app_url}/{TOKEN}"
        
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
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(set_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Вебхук установлен")
        else:
            logger.error(f"❌ Ошибка вебхука: {result}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка настройки вебхука: {e}")

# ============ ЗАПУСК ПРИЛОЖЕНИЯ ============
if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 ЗАПУСК УЧЕБНОГО БОТА ПРЕМИУМ v8.0")
    logger.info("=" * 80)
    logger.info(f"🤖 Бот: @Konspekt_help_bot")
    logger.info(f"🔑 Токен: {TOKEN[:10]}...")
    logger.info("=" * 80)
    
    # Настройка вебхука
    setup_webhook()
    
    # Запуск Flask сервера
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌍 Запуск на порту {port}...")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )
