import os
import msal

MS_CLIENT_ID = os.environ.get("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET")
MS_TENANT_ID = os.environ.get("MS_TENANT_ID")
MS_REDIRECT_URI = os.environ.get("MS_REDIRECT_URI", "http://localhost:5000/microsoft/callback")

SCOPES = [
    "Calendars.Read",
    "Calendars.ReadWrite",
    "User.Read"
]

def create_msal_app():
    return msal.ConfidentialClientApplication(
        MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/common",
        client_credential=MS_CLIENT_SECRET
    )

def get_auth_url():
    app = create_msal_app()
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=MS_REDIRECT_URI
    )

def get_token_from_code(code):
    app = create_msal_app()
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=MS_REDIRECT_URI
    )
    return result