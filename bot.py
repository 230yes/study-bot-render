#!/usr/bin/env python3
"""
📚 УЧЕБНЫЙ БОТ ПРЕМИУМ - ВЕРСИЯ ДЛЯ RENDER
С экспортом в PDF/DOCX и выбором устройства
"""

import os
import asyncio
import logging
import io
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file
import threading
import json
import time

# ============ 1. НАСТРОЙКА И FLASK APP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app для Render
app = Flask(__name__)

# Получаем токен из переменных окружения Render
TOKEN = os.environ.get('BOT_TOKEN', '')
if not TOKEN:
    logger.error("❌ Токен не найден! Добавьте BOT_TOKEN в Environment Variables Render")
    exit()

logger.info(f"✅ Токен получен: {TOKEN[:10]}...")

# База данных пользователей
user_devices = {}
user_settings = {}

# ============ 2. ИМПОРТ AIOGRAM ============
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.enums import ParseMode
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.client.default import DefaultBotProperties
    logger.info("✅ Библиотеки aiogram загружены")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    logger.info("📦 Установите: pip install aiogram")
    exit()

# ============ 3. ИНИЦИАЛИЗАЦИЯ БОТА ============
# Правильная инициализация для aiogram 3.7.0+
default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TOKEN, default=default)
dp = Dispatcher()

# ============ 4. ИМПОРТ ДЛЯ PDF/DOCX ============
try:
    # Для PDF
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    
    # Для DOCX
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    
    PDF_DOCX_AVAILABLE = True
    logger.info("✅ Библиотеки для PDF/DOCX загружены")
except ImportError:
    PDF_DOCX_AVAILABLE = False
    logger.warning("⚠️ Библиотеки для PDF/DOCX не установлены. Установите: pip install python-docx reportlab")

# ============ 5. FLASK РОУТЫ ============
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎓 Учебный Бот Премиум</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 800px;
                margin: 0 auto;
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .features {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin: 30px 0;
                text-align: left;
            }
            .feature {
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 10px;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: #0088cc;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-size: 1.2em;
                margin: 10px;
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
            <h1>🎓 Учебный Бот Премиум</h1>
            <div style="color: #4ade80; font-size: 1.5em; margin: 20px;">
                ✅ Активен на Render 24/7
            </div>
            
            <div class="features">
                <div class="feature">📚 Конспекты</div>
                <div class="feature">📄 Рефераты</div>
                <div class="feature">🎤 Доклады</div>
                <div class="feature">✍️ Эссе</div>
                <div class="feature">📱 Адаптация под устройства</div>
                <div class="feature">📊 Экспорт в PDF/DOCX</div>
                <div class="feature">🎨 Настройка оформления</div>
                <div class="feature">🤖 AI-генерация</div>
            </div>
            
            <a href="https://t.me/Konspekt_help_bot" class="btn" target="_blank">
                📱 Открыть в Telegram
            </a>
            <p style="margin-top: 30px; opacity: 0.8;">
                Платформа: Render.com | Режим: Web Service | Версия: Премиум
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "ok", 
        "service": "study-bot-premium",
        "features": ["pdf", "docx", "device_optimization", "ai_generation"],
        "version": "2.0.0"
    }), 200

# ============ 6. ГЕНЕРАЦИЯ ФАЙЛОВ ============
def generate_pdf(topic: str, content: str, device_type: str = None):
    """Генерация PDF файла"""
    buffer = io.BytesIO()
    
    # Создаем PDF документ
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # center
    )
    
    # Содержимое
    story = []
    
    # Заголовок
    story.append(Paragraph(f"Конспект: {topic}", title_style))
    story.append(Spacer(1, 12))
    
    # Информация о устройстве
    if device_type:
        device_text = f"<b>Оптимизировано для:</b> {device_type}"
        story.append(Paragraph(device_text, styles["Normal"]))
        story.append(Spacer(1, 12))
    
    # Дата
    date_text = f"<b>Дата создания:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, styles["Normal"]))
    story.append(Spacer(1, 24))
    
    # Контент
    content_paragraphs = content.split('\n')
    for paragraph in content_paragraphs:
        if paragraph.strip():
            p = Paragraph(paragraph.replace('*', '<b>').replace('_', '<i>'), styles["Normal"])
            story.append(p)
            story.append(Spacer(1, 6))
    
    # Футер
    story.append(Spacer(1, 30))
    footer = Paragraph(
        "<i>Сгенерировано Учебным Ботом на Render.com</i>",
        ParagraphStyle('Footer', parent=styles["Normal"], fontSize=10, textColor='gray')
    )
    story.append(footer)
    
    # Собираем PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_docx(topic: str, content: str, device_type: str = None):
    """Генерация DOCX файла"""
    # Создаем документ
    doc = Document()
    
    # Стили
    title_style = doc.styles.add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
    title_style.font.name = 'Arial'
    title_style.font.size = Pt(24)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    
    # Заголовок
    title = doc.add_paragraph(f'Конспект: {topic}')
    title.style = 'CustomTitle'
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Информация
    info = doc.add_paragraph()
    info.add_run(f'Дата создания: {datetime.now().strftime("%d.%m.%Y %H:%M")}\n').bold = True
    
    if device_type:
        info.add_run(f'Оптимизировано для: {device_type}\n').bold = True
    
    # Контент
    content_lines = content.split('\n')
    for line in content_lines:
        if line.strip():
            p = doc.add_paragraph(line.replace('*', '').replace('_', ''))
    
    # Футер
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.add_run('Сгенерировано Учебным Ботом на Render.com').italic = True
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Сохраняем в буфер
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ============ 7. ФУНКЦИИ ДЛЯ РАЗНЫХ УСТРОЙСТВ ============
def format_for_device(device_type: str, content: str, topic: str) -> str:
    """Форматирование под устройство"""
    formats = {
        "phone": f"""📱 <b>ВЕРСИЯ ДЛЯ ТЕЛЕФОНА</b>

{content}

📝 <b>Советы для телефона:</b>
• Используйте темную тему для чтения
• Сохраните в PDF для оффлайн-доступа
• Поделитесь с одногруппниками""",
        
        "pc": f"""💻 <b>ВЕРСИЯ ДЛЯ КОМПЬЮТЕРА</b>

{content}

📝 <b>Советы для ПК:</b>
• Распечатайте материал
• Сохраните в DOCX для редактирования
• Используйте для презентации""",
        
        "tablet": f"""📟 <b>ВЕРСИЯ ДЛЯ ПЛАНШЕТА</b>

{content}

📝 <b>Советы для планшета:</b>
• Используйте стилус для заметок
• Читайте в горизонтальном режиме
• Синхронизируйте с облаком""",
        
        "watch": f"""⌚ <b>КРАТКАЯ ВЕРСИЯ ДЛЯ ЧАСОВ</b>

<b>Конспект:</b> {topic[:50]}...

📌 <b>Ключевые пункты:</b>
• Основная идея 1
• Основная идея 2
• Основная идея 3

📝 <b>Советы для часов:</b>
• Используйте для быстрого повторения
• Ставьте напоминания
• Просматривайте в транспорте"""
    }
    
    return formats.get(device_type, content)

def generate_ai_content(topic: str, format_type: str = "conspect") -> str:
    """Генерация AI контента (имитация)"""
    formats = {
        "conspect": f"""📚 <b>КОНСПЕКТ ПО ТЕМЕ: {topic.upper()}</b>

<b>1. ВВЕДЕНИЕ</b>
Тема "{topic}" является одной из наиболее актуальных в современной науке/образовании.

<b>2. ОСНОВНЫЕ ПОНЯТИЯ</b>
• <i>Термин 1</i> - краткое объяснение
• <i>Термин 2</i> - краткое объяснение
• <i>Термин 3</i> - краткое объяснение

<b>3. ИСТОРИЧЕСКИЙ КОНТЕКСТ</b>
Краткая история развития темы.

<b>4. СОВРЕМЕННОЕ СОСТОЯНИЕ</b>
Текущие исследования и достижения.

<b>5. ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ</b>
Как используется в реальной жизни.

<b>6. ВЫВОДЫ</b>
Основные итоги и перспективы.""",
        
        "referat": f"""📄 <b>СТРУКТУРА РЕФЕРАТА: {topic.upper()}</b>

<b>Титульный лист</b>
- Название учебного заведения
- Тема реферата
- ФИО студента и преподавателя
- Год выполнения

<b>Оглавление</b>
- Введение (1-2 страницы)
- Основная часть (3-4 главы, 8-10 страниц)
- Заключение (1-2 страницы)
- Список литературы (5-10 источников)

<b>Требования:</b>
• Объем: 10-15 страниц
• Шрифт: Times New Roman, 14pt
• Интервал: 1.5
• Поля: 2см со всех сторон""",
        
        "presentation": f"""🎤 <b>ПЛАН ПРЕЗЕНТАЦИИ: {topic.upper()}</b>

<b>Слайд 1:</b> Титульный (тема, автор)
<b>Слайд 2:</b> Оглавление
<b>Слайд 3-5:</b> Введение и актуальность
<b>Слайд 6-10:</b> Основная часть
<b>Слайд 11:</b> Практические примеры
<b>Слайд 12:</b> Выводы
<b>Слайд 13:</b> Спасибо за внимание!

<b>Советы:</b>
• 1 слайд = 1 идея
• Минимум текста, максимум визуалов
• Время: 10-15 минут"""
    }
    
    return formats.get(format_type, formats["conspect"])

# ============ 8. КОМАНДЫ БОТА ============
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """Команда /start"""
    user = message.from_user
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="📱 Выбрать устройство", callback_data="menu_device"),
        InlineKeyboardButton(text="📊 Создать конспект", callback_data="menu_conspect")
    )
    keyboard.row(
        InlineKeyboardButton(text="📄 Экспорт в PDF/DOCX", callback_data="menu_export"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
    )
    
    await message.answer(
        f"👋 <b>Добро пожаловать, {user.first_name}!</b>\n\n"
        "🎓 <b>УЧЕБНЫЙ БОТ ПРЕМИУМ</b>\n\n"
        "<b>✨ Доступные функции:</b>\n"
        "• 📚 Умные конспекты и рефераты\n"
        "• 📱 Адаптация под ваше устройство\n"
        "• 📊 Экспорт в PDF и DOCX\n"
        "• 🎨 Настройка оформления\n"
        "• 🤖 AI-генерация материала\n"
        "• 💾 Сохранение истории\n\n"
        "<b>🚀 Как начать:</b>\n"
        "1. Выберите устройство\n"
        "2. Напишите тему\n"
        "3. Получите результат\n"
        "4. Экспортируйте в нужный формат\n\n"
        "<i>Используйте кнопки ниже или команды:</i>\n"
        "/device - выбор устройства\n"
        "/export - экспорт в файлы\n"
        "/ai - AI-генерация\n"
        "/help - полная справка",
        reply_markup=keyboard.as_markup()
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """Команда /help"""
    await message.answer(
        "🆘 <b>ПОЛНАЯ СПРАВКА</b>\n\n"
        "<b>📋 Основные команды:</b>\n"
        "/start - главное меню\n"
        "/help - эта справка\n"
        "/device - выбор устройства\n"
        "/export - экспорт в файлы\n"
        "/ai - AI-генерация\n"
        "/settings - настройки\n"
        "/history - история запросов\n\n"
        "<b>🎯 Как получить конспект:</b>\n"
        "1. Напишите тему (например: 'квантовая физика')\n"
        "2. Добавьте формат (например: 'реферат по истории')\n"
        "3. Получите материал\n"
        "4. Экспортируйте командой /export\n\n"
        "<b>📱 Доступные устройства:</b>\n"
        "• 📱 Телефон - мобильная версия\n"
        "• 💻 Компьютер - полная версия\n"
        "• 📟 Планшет - промежуточная версия\n"
        "• ⌚ Часы - краткая версия\n\n"
        "<b>📊 Форматы экспорта:</b>\n"
        "• PDF - для печати и чтения\n"
        "• DOCX - для редактирования\n"
        "• TXT - простой текст\n\n"
        "<b>⚡ Особенности версии:</b>\n"
        "• Работает 24/7 на Render\n"
        "• Быстрая генерация\n"
        "• Сохранение настроек\n"
        "• Регулярные обновления"
    )

@dp.message(Command("device"))
async def device_cmd(message: types.Message):
    """Выбор устройства"""
    user_id = str(message.from_user.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Телефон", callback_data="device_phone"),
        InlineKeyboardButton(text="💻 Компьютер", callback_data="device_pc"),
    )
    builder.row(
        InlineKeyboardButton(text="📟 Планшет", callback_data="device_tablet"),
        InlineKeyboardButton(text="⌚ Часы", callback_data="device_watch"),
    )
    
    current = user_devices.get(user_id, "не выбрано")
    
    await message.answer(
        f"📱 <b>ВЫБОР УСТРОЙСТВА</b>\n\n"
        f"Текущее: <b>{current}</b>\n\n"
        "<b>Оптимизация под:</b>\n"
        "• <b>📱 Телефон</b> - компактный формат\n"
        "• <b>💻 Компьютер</b> - полная версия\n"
        "• <b>📟 Планшет</b> - средний формат\n"
        "• <b>⌚ Часы</b> - краткая версия\n\n"
        "<i>Влияет на формат ответов и экспорта</i>",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("export"))
async def export_cmd(message: types.Message):
    """Экспорт в файлы"""
    user_id = str(message.from_user.id)
    last_topic = user_settings.get(f"{user_id}_last_topic", "нет данных")
    
    if last_topic == "нет данных":
        await message.answer(
            "📊 <b>ЭКСПОРТ МАТЕРИАЛА</b>\n\n"
            "Сначала создайте конспект командой или напишите тему.\n"
            "Затем используйте /export для сохранения в файл."
        )
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 PDF", callback_data="export_pdf"),
        InlineKeyboardButton(text="📝 DOCX", callback_data="export_docx"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 TXT", callback_data="export_txt"),
    )
    
    await message.answer(
        f"📊 <b>ЭКСПОРТ КОНСПЕКТА</b>\n\n"
        f"Тема: <b>{last_topic}</b>\n\n"
        "<b>Выберите формат:</b>\n"
        "• <b>📄 PDF</b> - для печати и чтения\n"
        "• <b>📝 DOCX</b> - для редактирования\n"
        "• <b>📋 TXT</b> - простой текст\n\n"
        "<i>Файлы будут сгенерированы и отправлены</i>",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("ai"))
async def ai_cmd(message: types.Message):
    """AI-генерация"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📚 Конспект", callback_data="ai_conspect"),
        InlineKeyboardButton(text="📄 Реферат", callback_data="ai_referat"),
    )
    builder.row(
        InlineKeyboardButton(text="🎤 Презентация", callback_data="ai_presentation"),
        InlineKeyboardButton(text="✍️ Эссе", callback_data="ai_essay"),
    )
    
    await message.answer(
        "🤖 <b>AI-ГЕНЕРАЦИЯ МАТЕРИАЛА</b>\n\n"
        "<b>Выберите тип материала:</b>\n"
        "• <b>📚 Конспект</b> - структурированные заметки\n"
        "• <b>📄 Реферат</b> - научная работа\n"
        "• <b>🎤 Презентация</b> - план выступления\n"
        "• <b>✍️ Эссе</b> - развернутое сочинение\n\n"
        "<i>После выбора напишите тему</i>",
        reply_markup=builder.as_markup()
    )

# ============ 9. ОБРАБОТКА CALLBACK ============
@dp.callback_query(F.data.startswith("device_"))
async def device_callback(callback: types.CallbackQuery):
    """Обработка выбора устройства"""
    user_id = str(callback.from_user.id)
    device_type = callback.data.replace("device_", "")
    
    device_names = {
        "phone": "📱 Телефон",
        "pc": "💻 Компьютер",
        "tablet": "📟 Планшет",
        "watch": "⌚ Часы"
    }
    
    device_name = device_names.get(device_type, "Неизвестно")
    user_devices[user_id] = device_name
    
    await callback.message.edit_text(
        f"✅ <b>УСТРОЙСТВО ВЫБРАНО</b>\n\n"
        f"Теперь используется: <b>{device_name}</b>\n\n"
        f"<i>Все материалы будут оптимизированы для этого устройства</i>"
    )
    await callback.answer(f"Устройство: {device_name}")

@dp.callback_query(F.data.startswith("export_"))
async def export_callback(callback: types.CallbackQuery):
    """Обработка экспорта"""
    user_id = str(callback.from_user.id)
    export_type = callback.data.replace("export_", "")
    last_topic = user_settings.get(f"{user_id}_last_topic", "Общая тема")
    last_content = user_settings.get(f"{user_id}_last_content", "Контент не найден")
    device_type = user_devices.get(user_id, "phone")
    
    if not PDF_DOCX_AVAILABLE and export_type in ["pdf", "docx"]:
        await callback.message.answer(
            "❌ <b>Экспорт недоступен</b>\n\n"
            "Библиотеки для генерации PDF/DOCX не установлены.\n"
            "Используйте TXT формат."
        )
        await callback.answer()
        return
    
    await callback.message.answer("🔄 <b>Генерирую файл...</b>")
    
    try:
        if export_type == "pdf":
            buffer = generate_pdf(last_topic, last_content, device_type)
            filename = f"конспект_{last_topic[:20]}.pdf"
            await bot.send_document(
                chat_id=callback.from_user.id,
                document=types.BufferedInputFile(buffer.getvalue(), filename=filename),
                caption=f"📄 <b>PDF конспект:</b> {last_topic}"
            )
            
        elif export_type == "docx":
            buffer = generate_docx(last_topic, last_content, device_type)
            filename = f"конспект_{last_topic[:20]}.docx"
            await bot.send_document(
                chat_id=callback.from_user.id,
                document=types.BufferedInputFile(buffer.getvalue(), filename=filename),
                caption=f"📝 <b>DOCX конспект:</b> {last_topic}"
            )
            
        elif export_type == "txt":
            content = f"Конспект: {last_topic}\n\n{last_content}"
            await bot.send_document(
                chat_id=callback.from_user.id,
                document=
