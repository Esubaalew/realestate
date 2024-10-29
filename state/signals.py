import os
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer


@receiver(post_save, sender=Customer)
def user_type_upgrade(sender, instance, created, **kwargs):
    if not created:
        if instance.user_type in ['agent', 'owner']:
            send_telegram_message(instance.telegram_id, instance.user_type)


def send_telegram_message(telegram_id, user_type):
    token = os.getenv('TOKEN')
    chat_id = telegram_id
    message = f"Your account has been upgraded to the new user type: {user_type}. You can use /addproperty to add propeties now. This action is irreversible."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
