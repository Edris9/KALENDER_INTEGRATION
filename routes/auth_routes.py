import os
import json
import hashlib
import base64
import secrets
from flask import Blueprint, redirect, session, request
from google_auth_oauthlib.flow import Flow
from config.settings import SCOPES, REDIRECT_URI
import requests as req

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"    

auth_bp = Blueprint("auth", __name__)

# In-memory storage istället för filer
verifier_store = {}

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
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    
    # Spara i minnet istället för fil
    verifier_store[state] = code_verifier
    
    session["state"] = state
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    flow = create_flow()
    state = request.args.get("state")
    
    # Hämta från minnet och radera
    code_verifier = verifier_store.pop(state, "")
    
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
    
    # Hämta användarens email från Google
    
    user_info = req.get(
    "https://openidconnect.googleapis.com/v1/userinfo",
    headers={"Authorization": f"Bearer {credentials.token}"}
        ).json()
    print("User info:", user_info)
    email = user_info.get("email")
    name = user_info.get("name")
    
    # Spara i Supabase
    from services.google.supabase_client import supabase

    existing = supabase.table("clients").select("*").eq("email", email).execute()
    
    if existing.data:
        supabase.table("clients").update({
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": str(list(credentials.scopes))
        }).eq("email", email).execute()
    else:
        supabase.table("clients").insert({
            "name": name,
            "email": email,
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": str(list(credentials.scopes))
        }).execute()
    
    return redirect("/")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")