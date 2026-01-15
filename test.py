import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Токены берём из переменных окружения
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ====== Функция для ответа ИИ ======
async def ai_reply(text: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Отвечай полными законченными предложениями."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return f"Ошибка API: {response.status_code} {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Ошибка запроса: {e}"


# ====== Команды ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Привет! 👋\n\n"
        "Я бот средней школы №2 города Тараз!\n\n"
        "Я могу:\n"
        "• Ответить на твои вопросы (ИИ)\n"
        "• Принимать фото и видео\n"
        "• Давать информацию о школе\n\n"
        "Напиши мне что-нибудь!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔹 Доступные команды:\n\n"
        "/start - Начать работу\n"
        "/help - Справка\n"
        "/buttons - Меню кнопок\n"
    )
    await update.message.reply_text(help_text)

async def button_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Расписание", callback_data='schedule')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contacts')],
        [InlineKeyboardButton("ℹ️ Информация", callback_data='info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выбери раздел:', reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    responses = {
        'schedule': '📚 Расписание уроков пока в разработке',
        'contacts': '📞 Телефон: +7 (XXX) XXX-XX-XX\nАдрес: г. Тараз, ул. ...',
        'info': 'ℹ️ Средняя школа №2 города Тараз'
    }
    response = responses.get(query.data, f'Выбрано: {query.data}')
    await query.edit_message_text(response)

# ====== Обработка сообщений ======
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    ai_text = await ai_reply(user_text)
    await update.message.reply_text(ai_text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Фото получено! Спасибо.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎥 Видео получено! Спасибо.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 Документ получен! Спасибо.")

# ====== Запуск ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("buttons", button_test))
    app.add_handler(CallbackQueryHandler(button_click))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
