import telebot
import os
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот для записи на экскурсии.")

bot.polling(non_stop=True)

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

'

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === НАСТРОЙКИ ===
TOKEN = '8090740734:AAFzBHkb-yKm-PiJRy_gf01DSOA4zH0UHy4
ADMIN_CHAT_ID = 1674618499  # ID админа Telegram (узнаешь через @userinfobot)
SPREADSHEET_NAME = 'Экскурсии'
CREDENTIALS_FILE = 'credentials.json'

# === ДАННЫЕ ===
excursions = {
    "Групповые": {
        "Старый город": ["2025-05-20", "2025-05-25"],
        "Исторический центр": ["2025-05-22", "2025-05-30"]
    },
    "Индивидуальные": {
        "Ночная прогулка": ["2025-05-21", "2025-05-27"],
        "Фотосессия в парке": ["2025-05-23", "2025-05-28"]
    }
}

user_data = {}


# === GOOGLE SHEETS ===
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet


# === ОБРАБОТЧИКИ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Групповые", callback_data="group")],
        [InlineKeyboardButton("Индивидуальные", callback_data="individual")],
        [InlineKeyboardButton("Связаться с админом", url="https://t.me/GoWithPolinaBredberry_bot")]
    ]
    await update.message.reply_text("Привет! Выбери тип экскурсии:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = "Групповые" if query.data == "group" else "Индивидуальные"
    user_data[query.from_user.id] = {"type": choice}

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"route|{name}")]
        for name in excursions[choice].keys()
    ]
    await query.edit_message_text(f"Выбери маршрут ({choice}):", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_route_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    route = query.data.split("|")[1]
    user_data[query.from_user.id]["route"] = route
    tour_type = user_data[query.from_user.id]["type"]

    dates = excursions[tour_type][route]
    keyboard = [
        [InlineKeyboardButton(date, callback_data=f"date|{date}")]
        for date in dates
    ]
    await query.edit_message_text(f"Выбери дату для '{route}':", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    date = query.data.split("|")[1]
    data = user_data[query.from_user.id]
    data["date"] = date

    # Сохраняем в таблицу
    sheet = get_sheet()
    user = query.from_user
    sheet.append_row([
        user.full_name,
        user.username or "",
        data["type"],
        data["route"],
        data["date"]
    ])

    # Уведомление администратору
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Новая запись!\n\nИмя: {user.full_name}\n@{user.username or 'нет'}\nТип: {data['type']}\nМаршрут: {data['route']}\nДата: {data['date']}"
    )

    keyboard = [[InlineKeyboardButton("Отменить запись", callback_data="cancel")]]
    await query.edit_message_text(
        f"Ты записан на экскурсию '{data['route']}' ({data['type']})\nДата: {data['date']}\n\nМы свяжемся с тобой для подтверждения!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_data.pop(query.from_user.id, None)
    await query.edit_message_text("Твоя запись отменена. Если хочешь записаться снова — нажми /start.")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Чтобы записаться на экскурсию — нажми /start.\n\nДля связи с администратором — @ТВОЙ_ЮЗЕРНЕЙМ")


# === MAIN ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CallbackQueryHandler(handle_type_choice, pattern="^(group|individual)$"))
    app.add_handler(CallbackQueryHandler(handle_route_choice, pattern="^route\|"))
    app.add_handler(CallbackQueryHandler(handle_date_choice, pattern="^date\|"))
    app.add_handler(CallbackQueryHandler(handle_cancel, pattern="^cancel$"))
    app.run_polling()


if __name__ == '__main__':
    main()
