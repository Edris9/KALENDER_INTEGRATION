import os
from flask import Blueprint, redirect, session, request
from google_auth_oauthlib.flow import Flow
from config.settings import CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    session["state"] = state
    
    
    session["code_verifier"] = flow.code_verifier 
    
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    if "state" not in session:
        return "Session state saknas. Gå via /login först."

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(
        authorization_response=request.url,
        # Kontrollera att den hämtar från sessionen
        code_verifier=session.get("code_verifier")
    )
    
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes)
    }
    return redirect("/availability")