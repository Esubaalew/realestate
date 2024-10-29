from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from state.tools import register_user, is_user_registered, get_user_details, upgrade_user

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    telegram_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name


    if is_user_registered(telegram_id):
        await update.message.reply_text(f"Welcome back, {full_name}! Use /profile to view or edit your profile.")
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
        await update.message.reply_text(
            "Could not retrieve your details. Please make sure you're registered using /start.")
        return

    user_type = user_details.get("user_type")

    if user_type == 'user':
        await update.message.reply_text(
            "You can only browse or inquire about properties. To add your own property, please upgrade your account by using /upgrade and choosing the Agent or Company option."
        )
    elif user_type in ['agent', 'owner']:
        await update.message.reply_text(
            "You have permission to add properties! This feature will be available shortly, so please stay tuned."
        )
    else:
        await update.message.reply_text("User type not recognized. Please contact support for assistance.")


async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to handle user upgrade."""
    telegram_id = str(update.message.from_user.id)


    keyboard = [
        [InlineKeyboardButton("Upgrade to Agent", callback_data='upgrade_agent')],
        [InlineKeyboardButton("Upgrade to Owner", callback_data='upgrade_owner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Choose your new account type to unlock additional features, such as adding properties:",
        reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callback data for upgrading the account."""
    query = update.callback_query
    await query.answer()

    telegram_id = str(query.from_user.id)

    new_user_type = "agent" if query.data == "upgrade_agent" else "owner"


    result = upgrade_user(telegram_id, new_user_type)


    await query.edit_message_text(
        f"{result['message']} You can now use /addproperty to add properties to the platform.")


async def bot_tele(text):
    # Create application
    application = (
        Application.builder().token(os.getenv('TOKEN')).build()
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("addproperty", addproperty))
    application.add_handler(CommandHandler("upgrade", upgrade))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start application
    await application.bot.set_webhook(url=os.getenv('webhook'))
    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )
    async with application:
        await application.start()
        await application.stop()
