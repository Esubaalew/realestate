from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    # Removed CallbackQueryHandler
)
import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from state.tools import register_user, is_user_registered, get_user_details, upgrade_user

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    telegram_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name

    if is_user_registered(telegram_id):
        await update.message.reply_text(f"Welcome back, {full_name}! Use /profile to view or edit your profile.")
    else:
        result = register_user(telegram_id, full_name)
        await update.message.reply_text(result["message"])


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            "Could not retrieve your details. Please make sure you're registered using /start."
        )
        return

    user_type = user_details.get("user_type")

    if user_type == 'user':
        await update.message.reply_text(
            "You can only browse or inquire about properties. To add your own property, please upgrade your account by using /upgrade and choosing the Agent or Company option."
        )
    elif user_type in ['agent', 'owner']:
        web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{telegram_id}&r=property"
        await update.message.reply_text(
            "You have permission to add properties! Use the following link to proceed:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Add Property", url=web_app_url)]])
        )
    else:
        await update.message.reply_text("User type not recognized. Please contact support for assistance.")



async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = str(update.message.from_user.id)
    user_details = get_user_details(telegram_id)

    if not user_details:
        await update.message.reply_text(
            "Could not retrieve your details. Please make sure you're registered using /start.")
        return

    user_type = user_details.get("user_type")

    if user_type in ['agent', 'owner']:
        await update.message.reply_text(
            "You are already upgraded to your current account type. Use /profile to manage your account."
        )
    elif user_type == 'user':
        web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{telegram_id}"
        await update.message.reply_text(
            "Account upgrades are irreversible. To upgrade your account, please visit your profile:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Edit Profile", url=web_app_url)]])
        )


# Main bot function
async def bot_tele(text):
    application = Application.builder().token(os.getenv('TOKEN')).build()

    logger.info(f"Bot token: {os.getenv('TOKEN')}")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("addproperty", addproperty))  # Add this line back
    application.add_handler(CommandHandler("upgrade", upgrade))

    webhook_url = os.getenv('webhook')
    logger.info(f"Setting webhook to: {webhook_url}")
    await application.bot.set_webhook(url=webhook_url)

    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )

    async with application:
        await application.start()
        await application.stop()

    logger.info("Bot has started and stopped successfully.")
