#!/usr/bin/env python3
# test.py — полный рабочий пример для python-telegram-bot 20.7
# Включает: проверки TOKEN, логирование версии PTB, неблокирующий вызов requests через asyncio.to_thread,
# защиту от отсутствия ключей и понятные сообщения в логах для Render.

import os
import asyncio
import logging
import requests
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, __version__ as ptb_version
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Настройка логирования (Render покажет эти логи)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Переменные окружения
TOKEN: Optional[str] = os.getenv("TOKEN")
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

# ====== Неблокирующая функция для вызова внешнего API через requests ======
async def ai_reply(text: str) -> str:
    """
    Асинхронная обёртка для синхронного requests.post, чтобы не блокировать event loop.
    Если GROQ_API_KEY не задан — возвращает уведомление.
    """
    if not GROQ_API_KEY:
        return "ИИ недоступен: не задан GROQ_API_KEY."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Отвечай полными законченными предложениями."},
            {"role": "user", "content": text},
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    def do_request():
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            return resp
        except Exception as e:
            # Возвращаем объект-ошибку в вызывающий поток
            return e

    result = await asyncio.to_thread(do_request)

    if isinstance(result, Exception):
        logger.exception("Ошибка при запросе к Groq API")
        return f"Ошибка запроса к ИИ: {result}"

    response = result
    if response.status_code != 200:
        logger.error("Groq API returned non-200: %s %s", response.status_code, response.text)
        return f"Ошибка API: {response.status_code} {response.text}"

    try:
        data = response.json()
        # Ожидаем структуру: data["choices"][0]["message"]["content"]
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception("Не удалось распарсить ответ Groq API")
        return f"Ошибка обработки ответа ИИ: {e}"


# ====== Хендлеры команд и сообщений ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Расписание", callback_data="schedule")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "Привет! 👋\n\n"
        "Я бот средней школы №2 города Тараз!\n\n"
        "Я могу:\n"
        "• Ответить на твои вопросы (ИИ)\n"
        "• Принимать фото и видео\n"
        "• Давать информацию о школе\n\n"
        "Напиши мне что-нибудь!"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔹 Доступные команды:\n\n"
        "/start - Начать работу\n"
        "/help - Справка\n"
        "/buttons - Меню кнопок\n\n"
        "Просто напиши сообщение — я попробую ответить через ИИ."
    )
    await update.message.reply_text(help_text)


async def button_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Расписание", callback_data="schedule")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери раздел:", reply_markup=reply_markup)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    responses = {
        "schedule": "📚 Расписание уроков пока в разработке",
        "contacts": "📞 Телефон: +7 (XXX) XXX-XX-XX\nАдрес: г. Тараз, ул. ...",
        "info": "ℹ️ Средняя школа №2 города Тараз",
    }
    response = responses.get(query.data, f"Выбрано: {query.data}")
    await query.edit_message_text(response)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text.strip()
    if not user_text:
        await update.message.reply_text("Пустое сообщение — напиши что-нибудь.")
        return

    # Отправляем индикатор, что бот обрабатывает (необязательно)
    try:
        await update.message.chat.send_action(action="typing")
    except Exception:
        pass

    ai_text = await ai_reply(user_text)
    await update.message.reply_text(ai_text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Фото получено! Спасибо.")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎥 Видео получено! Спасибо.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 Документ получен! Спасибо.")


# ====== Запуск приложения ======
def main():
    # Быстрые логи для отладки деплоя
    print("🚀 Deploy check: main() запущен")
    print("Python-telegram-bot version:", ptb_version)
    logger.info("Deploy check: main() started, PTB version: %s", ptb_version)

    # Проверка обязательных переменных окружения
    if not TOKEN:
        logger.error("Переменная окружения TOKEN не задана. Прекращаю запуск.")
        print("❌ Ошибка: переменная окружения TOKEN не задана. Проверьте настройки Render.")
        return

    # Создаём приложение
    try:
        app = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.exception("Ошибка при создании Application")
        print("❌ Ошибка при создании Application:", e)
        return

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("buttons", button_test))
    app.add_handler(CallbackQueryHandler(button_click))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Финальный лог перед запуском
    logger.info("Все хендлеры зарегистрированы. Запускаю polling...")
    print("🤖 Бот запущен и слушает Telegram...")

    # Запуск (блокирующий)
    try:
        app.run_polling()
    except Exception:
        logger.exception("Ошибка во время run_polling()")
        print("❌ Бот завершил работу с ошибкой. Смотри логи.")


if __name__ == "__main__":
    main()
