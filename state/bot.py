from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import os
import logging
from telegram import Update
import asyncio
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    await update.message.reply_text("Hey Welcome!!")


async def bot_tele(text):
    # Create application
    application = (
        Application.builder().token(os.getenv('TOKEN')).build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

    # # Start application
    # await application.bot.set_webhook(url=os.getenv('webhook'))
    # await application.update_queue.put(
    #     Update.de_json(data=text, bot=application.bot)
    # )
    # async with application:
    #     await application.start()
    #     await application.stop()

# call the tele fun dev only
if __name__ == '__main__':
    asyncio.run(bot_tele("fake"))