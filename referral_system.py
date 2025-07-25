import json
import uuid
import os

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def generate_referral_code():
    return str(uuid.uuid4())[:8]  # short and unique

def register_user(email, referral_code=None):
    users = load_users()

    # Check if user already exists
    for user in users.values():
        if user['email'] == email:
            return user, False  # existing user

    user_id = str(uuid.uuid4())
    user_referral_code = generate_referral_code()

    referred_by = None
    if referral_code:
        for uid, user in users.items():
            if user["referral_code"] == referral_code:
                referred_by = uid
                break

    users[user_id] = {
        "email": email,
        "referral_code": user_referral_code,
        "referred_by": referred_by
    }

    save_users(users)
    return users[user_id], True

def get_user_by_referral_code(code):
    users = load_users()
    for uid, user in users.items():
        if user["referral_code"] == code:
            return uid, user
    return None, None

def get_referrals(user_id):
    users = load_users()
    return [
        user for uid, user in users.items()
        if user.get("referred_by") == user_id
    ]
