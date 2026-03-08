import os
import json
import hashlib
import base64
import secrets
from flask import Blueprint, redirect, session, request
from google_auth_oauthlib.flow import Flow
from config.settings import SCOPES, REDIRECT_URI

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

auth_bp = Blueprint("auth", __name__)

def create_flow():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    if credentials_json:
        client_config = json.loads(credentials_json)
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    else:
        from config.settings import CLIENT_SECRETS_FILE
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    return flow

def generate_code_verifier():
    return secrets.token_urlsafe(64)

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

@auth_bp.route("/login")
def login():
    flow = create_flow()
    
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    session["code_verifier"] = code_verifier
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    session["state"] = state
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    flow = create_flow()
    code_verifier = session.get("code_verifier", "")
    
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=code_verifier
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
    return redirect("/")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")