#!/bin/python
# Frontend application
# TODO: Реализовать базовый функционал бота
# TODO: Реализовать функционал обращения к API backend
# TODO: Реализовать хранение данных о конматах и привязку датчиков к комнатах.

from telegram import  Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Функция иницирует работу с ботом и генерирует меню.
    """
    replay_keyboard = [['Получить данные']]
    reply_markup = ReplyKeyboardMarkup(replay_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Меню : ",
        reply_markup=reply_markup
    )

async def handle_message(update, context):
    if update.message.text == "Получить данные":
        inline_keyboard = [
            [InlineKeyboardButton("Температура во всех комнатах", callback_data="get_current_temperature")],
            [InlineKeyboardButton("Список датчиков", callback_data="get_sensors")]
            ]

def main():
    bot = Application.builder().token("7582204566:AAFnW1tqqAUXKsdKI3kSmTMQgrOgNcerXq4").build()
    bot.add_handler(CommandHandler("start", start))
    bot.run_polling()

if __name__ == "__main__":
    main()

