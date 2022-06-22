import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    filters,
    MessageHandler,
    Application,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
)
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
USEDESK_TOKEN = os.environ.get("USEDESK_TOKEN")
PORT = int(os.environ.get("PORT", "8443"))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

status_list = {
    1: "Открыт",
    2: "Выполнен",
    3: "Закрыт",
    4: "Удален",
    5: "На удержании",
    6: "В ожидании",
    7: "Спам",
    8: "Новый",
    9: "Рассылка",
    10: "Объединен",
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

(
    INITIAL,
    NAME,
    MAIL,
    THEME,
    JOB,
    COOPERATE,
    PRE_STATUS,
    STATUS,
    OTHER,
    NEW_TICKET,
    HELPFULL,
    BYE,
) = range(12)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
        Привет​​! Напишите все вопросы, а мы ответим на каждый из них ❤️️
        Это может занять от пары минут до нескольких часов, но если мы не застанем вас тут,
        ответ найдет вас в почте.
        """,
    )

    return INITIAL


async def initial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"Представьтесь пожалуйста")

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input_name = update.message.text
    context.user_data["name"] = input_name
    await update.message.reply_text(f"Привет, {input_name}! Укажи свой e-mail.")

    return MAIL


async def mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    theme_keyboard = [
        ["Хочу у Вас работать", "Хочу предложить сотрудничество"],
        ["Хочу узнать статус своего обращения", "У меня другой вопрос"],
    ]
    input_mail = update.message.text
    context.user_data["mail"] = input_mail
    await update.message.reply_text(
        f"""Почта {input_mail} будет использоваться для обратной связи с тобой.
        Выбери тему обращения.""",
        reply_markup=ReplyKeyboardMarkup(
            theme_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Выбери тему",
        ),
    )

    return THEME


async def job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client_name = context.user_data["name"]
    await update.message.reply_text(
        f"""Дорогой, {client_name}! Наши вакансии регулярно обновляются и публикуются на официальном сайте https://blackcaviar.games/ в разделе "Вакансии". Вы, также, можете направить Ваше резюме нам на почту job@blackcaviar.games.
                                        Благодарю за интерес, проявленный к нашей компании.😉"""
    )

    return HELPFULL


async def cooperate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client_name = context.user_data["name"]
    await update.message.reply_text(
        f"""Дорогой, {client_name}! По вопросам сотрудничества Вы можете написать нам на почту info@blackcaviar.games.
                                        Благодарю за интерес, проявленный к нашей компании.😉"""
    )

    return HELPFULL


async def pre_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        f"""Введите пожалуйста номер Вашего обращения (он указан в письме)"""
    )

    return STATUS


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_ticket = update.message.text
    req = requests.get(
        f"https://api.usedesk.ru/ticket?api_token={USEDESK_TOKEN}&ticket_id={input_ticket}"
    )
    resp = req.json()
    print(resp)
    try:
        t_status = resp["ticket"]["status_id"]
        result = status_list[t_status]
        status_result = f"Текущий статус обращения №{input_ticket}: {result}."
    except KeyError:
        status_result = "Вы ввели неверный номер обращения. Пожалуйста, попробуйте ещё."
        return PRE_STATUS
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_result)

    return HELPFULL


async def other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"""Опишите пожалуйста суть Вашего обращения""")

    return NEW_TICKET


async def helpfull(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        f"""Мой ответ помог Вам?""",
        reply_markup=ReplyKeyboardMarkup(
            help_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Выбери вариант",
        ),
    )

    return BYE


async def bye(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        """Был рад Вам помочь!
            Если у Вас возникнут еще какие-либо вопросы, пожалуйста свяжитесь с нами в любое удобное для Вас время. Спасибо за обращение.
            До свидания.""",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Пока пока. Буду рад снова поболтать", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INITIAL: [],
            NAME: [MessageHandler(filters.TEXT, name)],
            MAIL: [MessageHandler(filters.TEXT, mail)],
            THEME: [
                MessageHandler(filters.Regex("^(работать)$"), job),
                MessageHandler(filters.Regex("^(сотрудничество)$"), cooperate),
                MessageHandler(filters.Regex("^(статус)$"), pre_status),
                MessageHandler(filters.Regex("^(другой)$"), other),
            ],
            JOB: [],
            COOPERATE: [],
            PRE_STATUS: [],
            STATUS: [MessageHandler(filters.TEXT, status)],
            OTHER: [MessageHandler(filters.TEXT, other)],
            NEW_TICKET: [],
            HELPFULL: [
                MessageHandler(filters.Regex("^(да)$"), bye),
                MessageHandler(filters.Regex("^(нет)$"), other),
            ],
            BYE: [],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    start_handler = CommandHandler("start", start)
    status_handler = CommandHandler("status", status)

    application.add_handler(start_handler)
    application.add_handler(status_handler)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}",
    )

    application.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}")
