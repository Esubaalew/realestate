from typing import Any
import requests

API_URL = "https://estate.4gmobiles.com/api/customers/"

def register_user(telegram_id: str, full_name: str) -> dict:
    """Register a new user with the Telegram bot."""
    data = {
        "telegram_id": telegram_id,
        "full_name": full_name,
    }
    response = requests.post(API_URL, data=data)
    if response.status_code == 201:
        return {"success": True, "message": f"Welcome, {full_name}!"}
    return {"success": False, "message": "Registration failed. Please try again later."}
def is_user_registered(telegram_id: str) -> bool:
    """Check if the user is already registered."""
    response = requests.get(f"{API_URL}{telegram_id}/")
    return response.status_code == 200

def get_user_details(telegram_id: str) -> Any | None:
    """Fetch user details by Telegram ID."""
    response = requests.get(f"{API_URL}{telegram_id}/")
    if response.status_code == 200:
        return response.json()
    return None
