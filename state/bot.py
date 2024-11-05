from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, PicklePersistence, CallbackQueryHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
import logging
import requests
from state.tools import register_user, is_user_registered, get_user_details

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize persistence
persistence = PicklePersistence(filepath='bot_dat')

# Define states for the conversation flow
FULL_NAME, PHONE_NUMBER, TOUR_DATE, TOUR_TIME = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command with optional deep-linking for tour requests."""
    telegram_id = str(update.message.from_user.id)
    full_name = update.message.from_user.full_name

    args = context.args
    if args and args[0].startswith("request_tour_"):
        property_id = args[0].split("_")[2]
        context.user_data['property_id'] = property_id
        await update.message.reply_text("Please provide your full name to start scheduling the tour.")
        return FULL_NAME

    if is_user_registered(telegram_id):
        user_details = get_user_details(telegram_id)
        if user_details:
            profile_token = user_details.get("profile_token")
            await update.message.reply_text(f"Welcome back, {full_name}! Use /profile to view or edit your profile.")
        else:
            await update.message.reply_text("Could not retrieve your details. Please try again later.")
    else:
        result = register_user(telegram_id, full_name)
        await update.message.reply_text(result["message"])

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = str(update.message.from_user.id)
    user_details = get_user_details(telegram_id)

    if not user_details:
        await update.message.reply_text("Could not retrieve your details. Please make sure you're registered using /start.")
        return

    profile_token = user_details.get("profile_token")
    web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{profile_token}"

    await update.message.reply_text(
        "You can edit your profile using the following link (click to open):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Edit Profile", url=web_app_url)]])
    )

async def addproperty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add property command to check if the user can add properties."""
    telegram_id = str(update.message.from_user.id)
    user_details = get_user_details(telegram_id)

    if not user_details:
        await update.message.reply_text("Could not retrieve your details. Please make sure you're registered using /start.")
        return

    user_type = user_details.get("user_type")
    profile_token = user_details.get("profile_token")

    if user_type == 'user':
        await update.message.reply_text(
            "You can only browse or inquire about properties. To add your own property, please upgrade your account by using /upgrade and choosing the Agent or Company option."
        )
    elif user_type in ['agent', 'owner']:
        web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{profile_token}"
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
        await update.message.reply_text("Could not retrieve your details. Please make sure you're registered using /start.")
        return

    user_type = user_details.get("user_type")
    profile_token = user_details.get("profile_token")

    if user_type in ['agent', 'owner']:
        await update.message.reply_text("You are already upgraded to your current account type. Use /profile to manage your account.")
    elif user_type == 'user':
        web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{profile_token}"
        await update.message.reply_text(
            "Account upgrades are irreversible. To upgrade your account, please visit your profile:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Edit Profile", url=web_app_url)]])
        )

async def request_tour(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    command_parts = update.message.text.split("_")

    if len(command_parts) < 2:
        await update.message.reply_text("Please specify the property ID with the command, like this: /request_tour_<property_id>")
        return ConversationHandler.END

    property_id = command_parts[1]
    context.user_data['property_id'] = property_id

    await update.message.reply_text("Please provide your full name.")
    return FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Thanks! Now, please provide your phone number.")
    return PHONE_NUMBER

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone_number'] = update.message.text

    days_keyboard = [
        [KeyboardButton("Monday"), KeyboardButton("Tuesday")],
        [KeyboardButton("Wednesday"), KeyboardButton("Thursday")],
        [KeyboardButton("Friday"), KeyboardButton("Saturday")],
        [KeyboardButton("Sunday")]
    ]
    await update.message.reply_text(
        "Great! Please select a date (day of the week) for your tour.",
        reply_markup=ReplyKeyboardMarkup(days_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TOUR_DATE

async def get_tour_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tour_date = update.message.text
    if tour_date not in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        await update.message.reply_text("Invalid selection. Please select a valid day of the week.")
        return TOUR_DATE

    context.user_data['tour_date'] = tour_date

    time_buttons = [
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 11)]
    ]
    await update.message.reply_text(
        "Finally, at what time (1-10) would you like to schedule the tour?",
        reply_markup=InlineKeyboardMarkup(time_buttons)
    )
    return TOUR_TIME

async def get_tour_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()  # Acknowledge the callback

    tour_time = update.callback_query.data
    try:
        tour_time = int(tour_time)
        if not 1 <= tour_time <= 10:
            raise ValueError
    except ValueError:
        await update.callback_query.answer("Invalid time. Please select a valid time from the options provided.")
        return TOUR_TIME

    context.user_data['tour_time'] = tour_time
    register_tour_details(context.user_data)
    await update.callback_query.edit_message_text("Your tour request has been submitted!")
    return ConversationHandler.END

def register_tour_details(user_data: dict):
    global response
    data = {
        "property": user_data['property_id'],
        "full_name": user_data['full_name'],
        "phone_number": user_data['phone_number'],
        "tour_date": user_data['tour_date'],
        "tour_time": user_data['tour_time'],
    }
    try:
        response = requests.post("https://estate.4gmobiles.com/api/tours/", json=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"Failed to submit tour request: {e}")
        logger.error(f"Response content: {response.text}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("The tour scheduling process has been canceled. Use /start to begin again.")
    return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please follow the instructions to schedule a tour or use /cancel to exit.")

async def bot_tele(text):
    application = Application.builder().token(os.getenv('TOKEN')).persistence(persistence).build()

    tour_request_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^/request_tour_(\d+)$'), request_tour),
            CommandHandler("start", start)
        ],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)],
            TOUR_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tour_date)],
            TOUR_TIME: [CallbackQueryHandler(get_tour_time)]  # Handle callbacks for tour time
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.COMMAND, fallback)],
        persistent=True,
        name="tour_request_handler"
    )

    application.add_handler(tour_request_handler)
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("addproperty", addproperty))
    application.add_handler(CommandHandler("upgrade", upgrade))

    webhook_url = os.getenv('webhook')
    await application.bot.set_webhook(url=webhook_url)

    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )

    async with application:
        await application.start()
        await application.stop()

    logger.info("Bot has started and stopped successfully.")
