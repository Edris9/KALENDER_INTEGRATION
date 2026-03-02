from flask import Blueprint, redirect, session, request
from services.google_auth import create_flow

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    flow = create_flow()
    auth_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    flow = create_flow()
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    return redirect("/availability")