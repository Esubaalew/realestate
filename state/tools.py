from typing import Any, List
import requests

API_URL = "https://estate.4gmobiles.com/api/customers/"
TOUR_URL = "https://estate.4gmobiles.com/api/tours/"
PROPERTY_URL = "https://estate.4gmobiles.com/api/properties/"


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


def get_property_details(property_id: int) -> Any | None:
    """Fetch property details by property ID."""
    response = requests.get(f"{PROPERTY_URL}{property_id}/")
    if response.status_code == 200:
        return response.json()
    return None


def upgrade_user(telegram_id: str, new_user_type: str) -> dict:
    """Upgrade the user's account to 'agent' or 'owner'."""
    url = f"{API_URL}{telegram_id}/"
    data = {
        "user_type": new_user_type
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.patch(url, json=data, headers=headers)

    if response.status_code == 200:
        return {"success": True, "message": "Your account has been upgraded successfully."}
    elif response.status_code == 400:
        return {"success": False, "message": "Bad request. Please ensure the data is valid."}
    else:
        return {"success": False, "message": f"Failed to upgrade account. Status code: {response.status_code}"}


def get_user_properties(telegram_id: str) -> List[dict]:
    """Fetch properties associated with a specific user by Telegram ID."""
    response = requests.get(f"{API_URL}{telegram_id}/properties/")
    if response.status_code == 200:
        return response.json()
    return []


def get_user_tours(telegram_id: str) -> List[dict]:
    """Fetch tours associated with a specific user by Telegram ID."""
    response = requests.get(f"{TOUR_URL}telegram/{telegram_id}/")
    if response.status_code == 200:
        return response.json()
    return []
