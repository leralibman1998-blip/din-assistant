import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

conversation_histories = {}

SYSTEM_PROMPT = """Ты — личный AI-ассистент Валерии. Твоё имя — Дин.

О Валерии:
- Живёт и работает во Вроцлаве, Польша
- Владеет бьюти-коворкингом: сдаёт кабинеты и рабочие места мастерам красоты от 1 часа до длительной аренды
- Перепродаёт гранит с Украины — ищет клиентов в Польше и Европе
- Ищет идеи для онлайн-заработка и новых бизнесов
- Занимается своим здоровьем
- Много переводит: русский, польский, украинский, английский

Твои задачи:
1. ЛИЧНЫЙ АССИСТЕНТ: Напоминания, задачи, планирование дня, поддержка
2. БЬЮТИ-КОВОРКИНГ: Помогаешь с клиентами, отвечаешь на вопросы об аренде, условиях, ценах
3. INSTAGRAM: Общаешься с клиентами на их языке (RU/PL/UA/EN). Пишешь посты, caption, stories
4. ГРАНИТ: Помогаешь искать клиентов, писать коммерческие предложения
5. МАРКЕТИНГ: Эксперт в таргетированной рекламе Meta и Google Ads. Придумываешь креативные идеи
6. ПЕРЕВОДЫ: Русский, польский, украинский, английский
7. ИДЕИ: Генерируешь идеи для бизнеса и онлайн-заработка
8. ЗДОРОВЬЕ: Поддерживаешь здоровые привычки

Стиль: обращайся на ТЫ, тепло и дружески, конкретно и по делу.
Текущее время: {datetime}"""


async def call_claude(messages, system):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": "claude-opus-4-5",
        "max_tokens": 1500,
        "system": system,
        "messages": messages
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=body)
        data = response.json()
        return data["content"][0]["text"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text(
        "Привет, Валерия! 👋 Я Дин — твой личный ассистент.\n\n"
        "Помогу с:\n"
        "💎 Бьюти-коворкингом и клиентами\n"
        "🪨 Продажами гранита\n"
        "🎯 Маркетингом и рекламой\n"
        "📝 Постами для Instagram\n"
        "🌍 Переводами RU/PL/UA/EN\n"
        "📅 Напоминаниями\n"
        "💡 Идеями для бизнеса\n\n"
        "Пиши всё что нужно! 🚀"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversation_histories[user_id]) > 20:
        conversation_histories[user_id] = conversation_histories[user_id][-20:]

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        system = SYSTEM_PROMPT.format(datetime=datetime.now().strftime("%d.%m.%Y %H:%M"))
        reply = await call_claude(conversation_histories[user_id], system)

        conversation_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Упс, что-то пошло не так 😅 Попробуй ещё раз!")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text("История очищена! 🔄")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

 
