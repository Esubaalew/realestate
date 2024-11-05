import os
import requests
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer, Property, Tour
import telegram
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@receiver(post_save, sender=Customer)
def user_type_upgrade(sender, instance, created, **kwargs):
    if not created and instance.user_type in ['agent', 'owner']:
        send_telegram_message(instance.telegram_id, instance.user_type)

def send_telegram_message(telegram_id, user_type):
    token = os.getenv('TOKEN')
    message = (
        f"✨ Your account has been upgraded to the new user type: *{user_type}*.\n\n"
        "You can now use the /addproperty command to list properties.\n"
        "This action is *irreversible*."
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': ParseMode.MARKDOWN,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

@receiver(post_save, sender=Property)
def post_property_to_telegram(sender, instance, **kwargs):
    if instance.status == "confirmed":
        bot_token = os.getenv("TOKEN")
        bot = telegram.Bot(token=bot_token)

        owner = instance.owner
        confirmed_properties_count = Property.objects.filter(owner=owner, status="confirmed").count()
        verified_status = "Verified Client ✅" if owner.is_verified else "Unverified Client ❌"

        message = (
            f"🏠 *Property Name:* {instance.name}\n"
            f"📍 *Location:* {instance.city}, {instance.region}\n"
            f"🗺️ *Google Map Link:* {instance.google_map_link}\n"
            f"📏 *Total Area:* {instance.total_area} sqm\n"
            f"💵 *Selling Price:* ${instance.selling_price}\n"
            f"💲 *Average Price per sqm:* ${instance.average_price_per_square_meter}\n"
            f"🏢 *Type:* {instance.get_type_property_display()}\n"
            f"🏘️ *Usage:* {instance.get_usage_display()}\n"
            f"🛌 *Bedrooms:* {instance.bedrooms}\n"
            f"🛁 *Bathrooms:* {instance.bathrooms}\n"
            f"🍳 *Kitchens:* {instance.kitchens}\n"
            f"🌡️ *Heating Type:* {instance.heating_type}\n"
            f"❄️ *Cooling:* {instance.cooling}\n"
            f"🏙️ *Subcity/Zone:* {instance.subcity_zone}, Woreda {instance.woreda}\n"
            f"🏗️ *Built Date:* {instance.built_date}\n"
            f"🌄 *Balconies:* {instance.number_of_balconies}\n"
            f"📜 *Description:* {instance.own_description}\n"
            f"🔗 *Additional Media:* {instance.link_to_video_or_image}\n"
            f"\n*Owner Details:*\n"
            f"{verified_status}\n"
            f"🔢 *Confirmed Properties Owned:* {confirmed_properties_count}\n"
            f"\n---\n"
            f"Contact us for more details or view on the map!\n"
        )

        keyboard = [[InlineKeyboardButton("Request Tour", url=f"https://t.me/RealestateRo_Bot?start=request_tour_{instance.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        async_to_sync(bot.send_message)(
            chat_id="@realestatechan",
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

@receiver(post_save, sender=Tour)
def notify_admin_on_tour_request(sender, instance, created, **kwargs):
    """Send a notification to the admin when a new tour request is created."""
    if created:
        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        bot_token = os.getenv("TOKEN")
        bot = telegram.Bot(token=bot_token)

        # Get tour and property details
        property_details = (
            f"🏠 *Property Name:* {instance.property.name}\n"
            f"📍 *Location:* {instance.property.city}, {instance.property.region}\n"
            f"🔢 *Property ID:* {instance.property.id}\n"
            f"🗺️ *Google Map Link:* {instance.property.google_map_link}\n"
        )
        request_details = (
            f"👤 *Requested By:* {instance.full_name}\n"
            f"📞 *Contact Number:* {instance.phone_number}\n"
            f"📅 *Requested Date:* {instance.tour_date}\n"
            f"⏰ *Requested Time:* {instance.tour_time}\n"
        )

        message = (
            f"🚨 *New Tour Request Notification*\n\n"
            f"{property_details}\n"
            f"{request_details}\n"
            "Please review and manage this request accordingly."
        )

        try:
            async_to_sync(bot.send_message)(
                chat_id=admin_chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
            )
        except telegram.error.TelegramError as e:
            print(f"Failed to send admin notification: {e}")
