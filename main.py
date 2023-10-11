import os
import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler,  ConversationHandler, CallbackContext#, Filters,

# Состояния для конечного автомата
SEARCH, SHOW_DOCUMENT = range(2)

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Привет! Я бот-справочник. Чтобы найти документ, просто отправь мне запрос."
    )
    return SEARCH

# Функция для поиска документов в базе данных
def search_document(update: Update, context: CallbackContext) -> int:
    user_query = update.message.text

    # Подключение к базе данных
    conn = psycopg2.connect(
        database="bot_db",
        user="postgres",
        password="insanexxx",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    # Выполнение поискового запроса
    cursor.execute("SELECT title, link, description FROM documents WHERE title ILIKE %s", ('%' + user_query + '%',))
    results = cursor.fetchall()

    # Закрытие соединения с базой данных
    cursor.close()
    conn.close()

    if not results:
        update.message.reply_text("Извините, ничего не найдено. Попробуйте другой запрос.")
        return SEARCH

    context.user_data['results'] = results
    update.message.reply_text("Результаты поиска:")
    for idx, (title, link, description) in enumerate(results, start=1):
        update.message.reply_text(f"{idx}. {title}\nСсылка: {link}\nОписание: {description}")

    return SHOW_DOCUMENT

# Функция для отображения выбранного документа
def show_document(update: Update, context: CallbackContext) -> int:
    user_choice = update.message.text

    if not user_choice.isdigit():
        update.message.reply_text("Пожалуйста, выберите номер документа из списка.")
        return SHOW_DOCUMENT

    choice_idx = int(user_choice) - 1
    results = context.user_data.get('results')

    if 0 <= choice_idx < len(results):
        title, link, description = results[choice_idx]
        update.message.reply_text(f"Вы выбрали документ:\n{title}\nСсылка: {link}\nОписание: {description}")
    else:
        update.message.reply_text("Пожалуйста, выберите номер из списка.")
        return SHOW_DOCUMENT

    return ConversationHandler.END

def main():
    updater = Updater(token="6517102404:AAETbqsbT1iZS238o3fVCpacTVYRfkadXQ0", use_context=True)
    dispatcher = updater.dispatcher

    # Создание конечного автомата для управления разговором
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEARCH: [MessageHandler(Filters.text & ~Filters.command, search_document)],
            SHOW_DOCUMENT: [MessageHandler(Filters.text & ~Filters.command, show_document)],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
