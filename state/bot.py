from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from state.tools import register_user, is_user_registered, get_user_details

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    telegram_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name


    if is_user_registered(telegram_id):
        await update.message.reply_text(f"Welcome back, {full_name}!")
    else:

        result = register_user(telegram_id, full_name)


        if result["success"]:
            await update.message.reply_text(result["message"])
        else:
            await update.message.reply_text(result["message"])


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Profile command to generate a link to edit user profile."""
    telegram_id = str(update.message.from_user.id)


    web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{telegram_id}"

    await update.message.reply_text(
        "You can edit your profile using the following link (click to open):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Edit Profile", url=web_app_url)]])
    )


async def addproperty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add property command to check if the user can add properties."""
    telegram_id = str(update.message.from_user.id)


    user_details = get_user_details(telegram_id)

    if not user_details:
        await update.message.reply_text("Could not retrieve your details. Please make sure you're registered.")
        return

    user_type = user_details.get("user_type")


    if user_type == 'user':
        await update.message.reply_text(
            "You can only buy or sell properties. To add your own property, please upgrade your account to either Agent or Company."
        )
    elif user_type in ['agent', 'company']:
        await update.message.reply_text(
            "You can add properties soon. This feature will be available shortly!"
        )
    else:
        await update.message.reply_text("User type not recognized. Please contact support.")


async def bot_tele(text):
    # Create application
    application = (
        Application.builder().token(os.getenv('TOKEN')).build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("addproperty", addproperty))

    # Start application
    await application.bot.set_webhook(url=os.getenv('webhook'))
    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )
    async with application:
        await application.start()
        await application.stop()
