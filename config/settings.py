import os

CLIENT_SECRETS_FILE = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "email",
    "profile"
]

REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "http://localhost:5000/callback"
)