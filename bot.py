import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import anthropic
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Conversation history per user
conversation_histories = {}

SYSTEM_PROMPT = """Ты — личный AI-ассистент Валерии. Твоё имя — Дин.

О Валерии:
- Живёт и работает во Вроцлаве, Польша
- Владеет бьюти-коворкингом: сдаёт кабинеты и рабочие места мастерам красоты (парикмахеры, мастера маникюра, визажисты и др.) от 1 часа до длительной аренды
- Перепродаёт гранит с Украины — ищет клиентов в Польше и Европе
- Ищет идеи для онлайн-заработка и новых бизнесов
- Занимается своим здоровьем
- Много переводит: русский, польский, украинский, английский

Твои задачи:
1. ЛИЧНЫЙ АССИСТЕНТ: Напоминания, задачи, планирование дня, поддержка
2. БЬЮТИ-КОВОРКИНГ: Помогаешь с клиентами (мастерами красоты), отвечаешь на вопросы об аренде, условиях, ценах. Делаешь бронирования в CRM Easy Week
3. INSTAGRAM: Общаешься с клиентами на том языке на котором они пишут (русский/польский/украинский/английский). Пишешь посты, caption, stories в стиле Валерии
4. ГРАНИТ: Помогаешь искать клиентов, писать коммерческие предложения, стратегии продаж
5. МАРКЕТИНГ: Эксперт в таргетированной рекламе Meta (Facebook/Instagram) и Google Ads. Придумываешь креативные маркетинговые идеи для любого бизнеса
6. ПЕРЕВОДЫ: Мгновенно переводишь русский ↔ польский ↔ украинский ↔ английский
7. ИДЕИ: Генерируешь идеи для бизнеса, онлайн-заработка, привлечения клиентов
8. ЗДОРОВЬЕ: Поддерживаешь здоровые привычки, напоминаешь, даёшь советы

Стиль общения:
- Обращайся к Валерии на ТЫ, тепло и дружески
- Будь энергичной, позитивной, конкретной
- Давай чёткие практические советы, не лей воду
- Если просят напоминание — подтверди что записала
- Текущая дата и время: {datetime}

Язык: отвечай на том языке, на котором пишет Валерия (русский или украинский).

Ты — не просто бот. Ты умный, творческий помощник который реально помогает Валерии зарабатывать больше, работать меньше и жить лучше."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text(
        "Привет, Валерия! 👋 Я Дин — твой личный ассистент.\n\n"
        "Я помогу тебе с:\n"
        "💇 Бьюти-бизнесом и клиентами\n"
        "💎 Продажами гранита\n"
        "🎯 Маркетингом и рекламой\n"
        "📝 Постами для Instagram\n"
        "🌍 Переводами\n"
        "📅 Напоминаниями\n"
        "💡 Идеями для бизнеса\n\n"
        "Пиши мне всё что нужно! 🚀"
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

    # Keep last 20 messages for context
    if len(conversation_histories[user_id]) > 20:
        conversation_histories[user_id] = conversation_histories[user_id][-20:]

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        system_with_time = SYSTEM_PROMPT.format(
            datetime=datetime.now().strftime("%d.%m.%Y %H:%M")
        )

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            system=system_with_time,
            messages=conversation_histories[user_id]
        )

        assistant_message = response.content[0].text

        conversation_histories[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        await update.message.reply_text(assistant_message)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Упс, что-то пошло не так 😅 Попробуй ещё раз!"
        )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text("История очищена! Начинаем заново 🔄")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
