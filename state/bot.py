from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, \
    PicklePersistence, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
import os
import logging
import requests
from state.tools import register_user, is_user_registered, get_user_details, get_user_properties, get_user_tours, \
    get_property_details, get_user_favorites, get_non_user_accounts, get_confirmed_user_properties

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
            await update.message.reply_text(f"Welcome back, {full_name}! Here are some quick options:",
                                            reply_markup=get_main_menu())
        else:
            await update.message.reply_text("Could not retrieve your details. Please try again later.")
    else:
        result = register_user(telegram_id, full_name)
        await update.message.reply_text(result["message"])
        await update.message.reply_text("You’re registered! Here are some quick options:", reply_markup=get_main_menu())


def get_main_menu():
    """Generate the main menu inline keyboard with descriptive emojis."""
    buttons = [
        [InlineKeyboardButton("➕ Add Property 🏡", callback_data="add_property")],
        [InlineKeyboardButton("✨ Upgrade Account ⭐", callback_data="upgrade_account")],
        [InlineKeyboardButton("👤 View Profile 🔍", callback_data="view_profile")],
        [InlineKeyboardButton("📋 List Properties 📂", callback_data="list_properties")],
        [InlineKeyboardButton("❤️ List Favorites 💾", callback_data="list_favorites")],
        [InlineKeyboardButton("📅 List Tours 🗓️", callback_data="list_tours")],
        [InlineKeyboardButton("💬 Live Agent 📞", callback_data="live_agent")],
        [InlineKeyboardButton("🌐 Change Language 🌍", callback_data="change_language")],
    ]

    # Arrange buttons in two columns (except the last row)
    formatted_buttons = []
    for i in range(0, len(buttons) - 1, 2):
        formatted_buttons.append(buttons[i] + buttons[i + 1])
    if len(buttons) % 2 == 1:
        formatted_buttons.append(buttons[-1])

    return InlineKeyboardMarkup(formatted_buttons)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Profile command to handle user profile viewing and editing."""

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log and retrieve user details
    logger.info(f"Profile command triggered for user {telegram_id}")
    user_details = get_user_details(telegram_id)

    if not user_details:
        message = (
            "Could not retrieve your details. Please make sure you're registered using /start."
        )
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Generate the profile edit link
    profile_token = user_details.get("profile_token")
    web_app_url = f"https://t.me/mana_etbot/state?startapp=edit-{profile_token}"
    message = (
        "You can edit your profile using the following link (click to open):"
    )
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Edit Profile", url=web_app_url)]]
    )

    # Send the response based on the source of the update
    if update.callback_query:
        await query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def addproperty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add property command to check if the user can add properties."""
    # Determine the source of the update
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log and retrieve user details
    logger.info(f"addproperty triggered for user {telegram_id}")
    user_details = get_user_details(telegram_id)

    if not user_details:
        message = (
            "Could not retrieve your details. Please make sure you're registered using /start."
        )
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Check user type and profile token
    user_type = user_details.get("user_type")
    profile_token = user_details.get("profile_token")

    if user_type == 'user':
        message = (
            "You can only browse or inquire about properties. To add your own property, "
            "please upgrade your account by using /upgrade and choosing the Agent or Company option."
        )
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)

    elif user_type in ['agent', 'owner']:
        web_app_url = f"https://t.me/mana_etbot/state?startapp=edit-{profile_token}"
        message = (
            "You have permission to add properties! Use the following link to proceed:"
        )
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Add Property", url=web_app_url)]]
        )
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)

    else:
        message = "User type not recognized. Please contact support for assistance."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)


async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Upgrade account command to handle user upgrades and profile management."""

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log and retrieve user details
    logger.info(f"Upgrade triggered for user {telegram_id}")
    user_details = get_user_details(telegram_id)

    if not user_details:
        message = (
            "Could not retrieve your details. Please make sure you're registered using /start."
        )
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Check user type and profile token
    user_type = user_details.get("user_type")
    profile_token = user_details.get("profile_token")

    if user_type in ['agent', 'owner']:
        message = "You are already upgraded to your current account type. Use /profile to manage your account."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)

    elif user_type == 'user':
        web_app_url = f"https://t.me/mana_etbot/state?startapp=edit-{profile_token}"
        message = (
            "Account upgrades are irreversible. To upgrade your account, please visit your profile:"
        )
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Edit Profile", url=web_app_url)]]
        )
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)

    else:
        message = "User type not recognized. Please contact support for assistance."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)


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
    await update.callback_query.answer()
    data = update.callback_query.data

    if data.startswith("make_favorite_"):
        property_id = int(data.split("_")[2])
        telegram_id = str(update.callback_query.from_user.id)

        # Fetch user favorites
        favorites = get_user_favorites(telegram_id)
        logger.info(f"User's favorites for {telegram_id}: {favorites}")

        # Retrieve property details
        property_details = get_property_details(property_id)
        property_name = property_details.get('name', 'Unknown Property') if property_details else 'Unknown Property'

        # Check if the property is already in favorites and get the favorite_id
        favorite_id = None
        for favorite in favorites:
            if favorite['property'] == property_id:
                favorite_id = favorite['id']  # Retrieve the favorite model ID
                break

        # If the property is already a favorite, delete it
        if favorite_id:
            try:
                response = requests.delete(f"https://estate.4gmobiles.com/api/favorites/{favorite_id}/")
                response.raise_for_status()

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=f"❌ The property *{property_name}* has been removed from your favorites."
                )

            except requests.HTTPError as e:
                logger.error(f"Failed to remove property from favorites: {e}")
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text="❌ Failed to remove from favorites. Please try again later."
                )

        # If the property is not a favorite, add it
        else:
            try:
                response = requests.post("https://estate.4gmobiles.com/api/favorites/", json={
                    "property": property_id,
                    "customer": telegram_id
                })
                response.raise_for_status()

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=f"🏡 The property *{property_name}* has been added to your favorites!"
                )

            except requests.HTTPError as e:
                logger.error(f"Failed to add property to favorites: {e}")
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

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log the action
    logger.info(f"List properties triggered for user {telegram_id}")
    properties = get_user_properties(telegram_id)

    # Simulate typing action
    if update.callback_query:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    else:
        await update.message.chat.send_action(ChatAction.TYPING)

    if not properties:
        message = "🏡 You don't have any properties listed yet! Use /addproperty to add one."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Prepare response with a maximum of 20 properties
    response_text = "📝 Here are your properties:\n"
    for i, prop in enumerate(properties[:20], start=1):  # Limit to 20 properties
        response_text += f"{i}. 📍 *{prop['name']}* - Status: *{prop['status']}*\n"

    if len(properties) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 properties are displayed."

    # Send the response based on the source of the update
    if update.callback_query:
        await query.edit_message_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


async def list_tours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List tours associated with the user."""

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log the action
    logger.info(f"List tours triggered for user {telegram_id}")

    # Simulate typing action
    if update.callback_query:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    else:
        await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch the list of scheduled tours for the user
    tours = get_user_tours(telegram_id)

    if not tours:
        message = "🚶‍♂️ You have no scheduled tours yet! Use /request_tour_<property_id> to schedule one."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Prepare the response with a maximum of 20 tours
    response_text = "📅 Here are your scheduled tours:\n"

    for i, tour in enumerate(tours[:20], start=1):  # Limit to 20 tours
        # Fetch property details using the property ID
        property_details = get_property_details(tour['property'])
        property_name = property_details.get('name', 'Unknown Property') if property_details else 'Unknown Property'

        response_text += (
            f"{i}. 🏡 Property: *{property_name}* - Date: *{tour['tour_date']}* - Time: *{tour['tour_time']}*\n"
        )

    if len(tours) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 tours are displayed."

    # Send the response based on the source of the update
    if update.callback_query:
        await query.edit_message_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


async def list_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List favorite properties associated with the user."""

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log the action
    logger.info(f"List favorites triggered for user {telegram_id}")

    # Simulate typing action
    if update.callback_query:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    else:
        await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch the list of favorite properties for the user
    favorites = get_user_favorites(telegram_id)

    if not favorites:
        message = "❤️ You have no favorite properties yet! Use the ❤️ button to add some."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Prepare the response with a maximum of 20 favorites
    response_text = "🌟 Your Favorite Properties:\n"

    for i, favorite in enumerate(favorites[:20], start=1):  # Limit to 20 favorites
        # Fetch property details using the property ID
        property_details = get_property_details(favorite['property'])
        property_name = property_details.get('name', 'Unknown Property') if property_details else 'Unknown Property'

        response_text += f"{i}. 🏡 Property: *{property_name}*\n"

    if len(favorites) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 favorites are displayed."

    # Send the response based on the source of the update
    if update.callback_query:
        await query.edit_message_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all registered users with user type 'agent' or 'owner' and their confirmed property count."""

    # Determine the source of the update (callback query or message)
    if update.callback_query:
        query = update.callback_query
        telegram_id = str(query.from_user.id)
        await query.answer()  # Acknowledge the callback query
    else:
        telegram_id = str(update.message.from_user.id)

    # Log the action
    logger.info(f"List users triggered for user {telegram_id}")

    # Simulate typing action
    if update.callback_query:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    else:
        await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch the list of non-user accounts (agents and owners)
    users = get_non_user_accounts()
    if not users:
        message = "There are no registered agents or owners."
        if update.callback_query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    # Prepare response with a maximum of 20 users
    response_text = "👥 *Registered Agents and Owners:*\n\n"
    for i, user in enumerate(users[:20], start=1):  # Limit to 20 users
        confirmed_properties = get_confirmed_user_properties(user['telegram_id'])
        property_count = len(confirmed_properties)

        # Include emojis for user type
        user_type_icon = "👤" if user["user_type"] == "agent" else "🏢"

        response_text += (
            f"{i}. {user_type_icon} *{user['full_name']}* - Type: *{user['user_type'].capitalize()}*\n"
            f"   🔑 Confirmed Properties: {property_count}\n"
        )

    if len(users) > 20:
        response_text += "\n🔍 *Note:* Only the first 20 users are displayed."

    # Send the response based on the source of the update
    if update.callback_query:
        await query.edit_message_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)


# Define available languages
LANGUAGES = ["Amharic", "English"]


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /changelang command to allow users to choose a language."""
    # Use the same keyboard (ReplyKeyboardMarkup) for both callback queries and messages
    keyboard = [[LANGUAGES[0], LANGUAGES[1]]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if update.callback_query:
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query

        # Send the same keyboard as a new message or edit the existing message
        await query.edit_message_text(
            "Please choose a language:", reply_markup=reply_markup
        )
    else:
        # Send the keyboard in response to a command or message
        await update.message.reply_text(
            "Please choose a language:", reply_markup=reply_markup
        )


async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the user's language selection."""
    user_choice = None

    if update.callback_query:
        # Extract the user's language choice from callback query data (if used)
        query = update.callback_query
        await query.answer()
        user_choice = query.data.replace("lang_", "")  # Extract language choice

    elif update.message:
        # Extract the user's language choice from the message text
        user_choice = update.message.text

    # Handle the user's choice
    if user_choice in LANGUAGES:
        # Confirm the selection and remove the keyboard
        await update.message.reply_text(
            f"You have chosen {user_choice}.", reply_markup=ReplyKeyboardRemove()
        )
    else:
        # Invalid choice: Re-prompt the user with the same keyboard
        await update.message.reply_text(
            "Invalid choice. Please select a language using the buttons below."
        )
        await change_language(update, context)


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    data = query.data

    # Log which button was clicked and the user's Telegram ID
    telegram_id = query.from_user.id
    logger.info(f"User {telegram_id} clicked on button: {data}")

    # Route based on the prefix of the callback data
    if data.startswith("make_favorite_"):
        logger.info(f"Handling 'Make Favorite' for user {telegram_id}")
        await handle_favorite_request(update, context)
    elif data == "add_property":
        logger.info(f"Handling 'Add Property' for user {telegram_id}")
        await addproperty(update, context)
    elif data == "upgrade_account":
        logger.info(f"Handling 'Upgrade Account' for user {telegram_id}")
        await upgrade(update, context)
    elif data == "view_profile":
        logger.info(f"Handling 'View Profile' for user {telegram_id}")
        await profile(update, context)
    elif data == "list_properties":
        logger.info(f"Handling 'List Properties' for user {telegram_id}")
        await list_properties(update, context)
    elif data == "list_favorites":
        logger.info(f"Handling 'List Favorites' for user {telegram_id}")
        await list_favorites(update, context)
    elif data == "list_tours":
        logger.info(f"Handling 'List Tours' for user {telegram_id}")
        await list_tours(update, context)
    elif data == "change_language":
        logger.info(f"Handling 'Change Language' for user {telegram_id}")
        await change_language(update, context)
    else:
        logger.warning(f"Unknown action {data} received from user {telegram_id}")
        await query.edit_message_text("Unknown action. Please try again.")


async def bot_tele(text):
    application = Application.builder().token(os.getenv('TOKEN')).persistence(persistence).build()

    tour_request_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r'^/request_tour_(\d+)$'), request_tour),
            CommandHandler("start", start),
            CallbackQueryHandler(handle_main_menu)

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
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_choice))
    application.add_handler(CommandHandler("changelang", change_language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_choice))

    webhook_url = os.getenv('webhook')
    await application.bot.set_webhook(url=webhook_url)

    await application.update_queue.put(
        Update.de_json(data=text, bot=application.bot)
    )

    async with application:
        await application.start()
        await application.stop()

    logger.info("Bot has started and stopped successfully.")
