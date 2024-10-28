from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import os
import logging
from telegram import Update
from state.tools import register_user, is_user_registered

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    telegram_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name

    # Check if user is already registered
    if is_user_registered(telegram_id):
        await update.message.reply_text(f"Welcome back, {full_name}!")
    else:
        # Call the registration function
        result = register_user(telegram_id, full_name)

        # Send response based on registration outcome
        if result["success"]:
            await update.message.reply_text(result["message"])
        else:
            await update.message.reply_text(result["message"])



async def bot_tele(text):
    # Create application
    application = (
        Application.builder().token(os.getenv('TOKEN')).build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))

    # Start application
    await application.bot.set_webhook(url=os.getenv('webhook'))
    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )
    async with application:
        await application.start()
        await application.stop()
