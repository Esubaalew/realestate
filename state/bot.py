from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, \
    PicklePersistence, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
import os
import logging
import requests
from state.tools import register_user, is_user_registered, get_user_details, get_user_properties, get_user_tours, \
    get_property_details, get_user_favorites

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
    username = update.message.from_user.username

    context.user_data['telegram_id'] = telegram_id
    context.user_data['username'] = username

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
        await update.message.reply_text(
            "Could not retrieve your details. Please make sure you're registered using /start.")
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
        await update.message.reply_text(
            "Could not retrieve your details. Please make sure you're registered using /start.")
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
        await update.message.reply_text(
            "Could not retrieve your details. Please make sure you're registered using /start.")
        return

    user_type = user_details.get("user_type")
    profile_token = user_details.get("profile_token")

    if user_type in ['agent', 'owner']:
        await update.message.reply_text(
            "You are already upgraded to your current account type. Use /profile to manage your account.")
    elif user_type == 'user':
        web_app_url = f"https://t.me/RealestateRo_Bot/state?startapp=edit-{profile_token}"
        await update.message.reply_text(
            "Account upgrades are irreversible. To upgrade your account, please visit your profile:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Edit Profile", url=web_app_url)]])
        )


async def request_tour(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    command_parts = update.message.text.split("_")

    if len(command_parts) < 2:
        await update.message.reply_text(
            "Please specify the property ID with the command, like this: /request_tour_<property_id>")
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
    await update.message.reply_text("Thank you! Now, please select a time for the tour.",
                                    reply_markup=ReplyKeyboardRemove())

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
    telegram_id = str(user_data.get('telegram_id'))
    username = user_data.get('username', '')

    data = {
        "property": user_data['property_id'],
        "full_name": user_data['full_name'],
        "phone_number": user_data['phone_number'],
        "tour_date": user_data['tour_date'],
        "tour_time": user_data['tour_time'],
        "telegram_id": telegram_id,  # Add telegram_id to API data
        "username": username  # Add username if available
    }

    try:
        response = requests.post("https://estate.4gmobiles.com/api/tours/", json=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"Failed to submit tour request: {e}")
        if response:
            logger.error(f"Response content: {response.text}")


async def handle_favorite_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()  # Acknowledge the callback
    data = update.callback_query.data

    if data.startswith("make_favorite_"):
        property_id = data.split("_")[2]  # Get the property ID from the callback data
        telegram_id = str(update.callback_query.from_user.id)

        # Call the API to add the property to favorites
        try:
            response = requests.post("https://estate.4gmobiles.com/api/favorites/", json={
                "property": property_id,
                "customer": telegram_id
            })
            response.raise_for_status()  # Raise an error for bad responses

            # Send a separate DM confirmation to the user
            await context.bot.send_message(
                chat_id=telegram_id,
                text="🏡 The property has been added to your favorites!"
            )

        except requests.HTTPError as e:
            logger.error(f"Failed to add property to favorites: {e}")

            # Send a separate DM error message to the user
            await context.bot.send_message(
                chat_id=telegram_id,
                text="❌ Failed to add to favorites. Please try again later."
            )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("The tour scheduling process has been canceled. Use /start to begin again.")
    return ConversationHandler.END


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please follow the instructions to schedule a tour or use /cancel to exit.")


async def list_properties(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List properties associated with the user."""
    telegram_id = str(update.message.from_user.id)
    properties = get_user_properties(telegram_id)

    await  update.message.chat.send_action(ChatAction.TYPING)

    if not properties:
        await update.message.reply_text("🏡 You don't have any properties listed yet! Use /addproperty to add one.")
        return

    response_text = "📝 Here are your properties:\n"
    for i, prop in enumerate(properties[:20], start=1):  # Limit to 20 properties
        response_text += f"{i}. 📍 *{prop['name']}* - Status: *{prop['status']}*\n"

    if len(properties) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 properties are displayed."

    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


async def list_tours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List tours associated with the user."""
    telegram_id = str(update.message.from_user.id)
    tours = get_user_tours(telegram_id)

    await  update.message.chat.send_action(ChatAction.TYPING)

    if not tours:
        await update.message.reply_text(
            "🚶‍♂️ You have no scheduled tours yet! Use /request_tour_<property_id> to schedule one.")
        return

    response_text = "📅 Here are your scheduled tours:\n"

    for i, tour in enumerate(tours[:20], start=1):  # Limit to 20 tours
        # Fetch property details using the property ID
        property_details = get_property_details(tour['property'])

        property_name = property_details.get('name', 'Unknown Property') if property_details else 'Unknown Property'

        response_text += f"{i}. 🏡 Property: *{property_name}* - Date: *{tour['tour_date']}* - Time: *{tour['tour_time']}*\n"

    if len(tours) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 tours are displayed."

    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


async def list_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List favorite properties associated with the user."""
    telegram_id = str(update.message.from_user.id)
    favorites = get_user_favorites(telegram_id)

    await update.message.chat.send_action(ChatAction.TYPING)

    if not favorites:
        await update.message.reply_text("❤️ You have no favorite properties yet! Use the ❤️ button to add some.")
        return

    response_text = "🌟 Your Favorite Properties:\n"

    for i, favorite in enumerate(favorites[:20], start=1):  # Limit to 20 favorites
        # Fetch property details using the property ID
        property_details = get_property_details(favorite['property'])

        property_name = property_details.get('name', 'Unknown Property') if property_details else 'Unknown Property'

        response_text += f"{i}. 🏡 Property: *{property_name}*\n"

    if len(favorites) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 favorites are displayed."

    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


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
    application.add_handler(CommandHandler("list_properties", list_properties))
    application.add_handler(CommandHandler("list_tours", list_tours))
    application.add_handler(CommandHandler("list_favorites", list_favorites))
    application.add_handler(CallbackQueryHandler(handle_favorite_request))

    webhook_url = os.getenv('webhook')
    await application.bot.set_webhook(url=webhook_url)

    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )

    async with application:
        await application.start()
        await application.stop()

    logger.info("Bot has started and stopped successfully.")
