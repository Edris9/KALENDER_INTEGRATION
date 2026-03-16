import os
from flask import Blueprint, redirect, request, session, jsonify
from services.microsoft.ms_auth import get_auth_url, get_token_from_code
from services.microsoft.ms_calendar_reader import get_ms_availability
from services.microsoft.ms_calendar_writer import book_ms_meeting
from services.google.supabase_client import supabase
from utils.time_utils import get_free_slots
import requests as req

ms_bp = Blueprint("microsoft", __name__)

@ms_bp.route("/microsoft/login")
def ms_login():
    auth_url = get_auth_url()
    return redirect(auth_url)

@ms_bp.route("/microsoft/callback")
def ms_callback():
    code = request.args.get("code")
    
    if not code:
        return "Error: No code received", 400
    
    result = get_token_from_code(code)
    
    if "error" in result:
        return f"Error: {result['error_description']}", 400
    
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    
    # Hämta användarinfo från Microsoft
    user_info = req.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    name = user_info.get("displayName")
    
    # Spara i session
    session["ms_credentials"] = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    
    # Spara i Supabase
    existing = supabase.table("clients").select("*").eq("email", email).execute()
    
    if existing.data:
        supabase.table("clients").update({
            "token": access_token,
            "refresh_token": refresh_token,
            "provider": "microsoft"
        }).eq("email", email).execute()
    else:
        supabase.table("clients").insert({
            "name": name,
            "email": email,
            "token": access_token,
            "refresh_token": refresh_token,
            "provider": "microsoft"
        }).execute()
    
    return redirect("/")

@ms_bp.route("/microsoft/availability")
def ms_availability():
    if "ms_credentials" not in session:
        return redirect("/microsoft/login")
    
    access_token = session["ms_credentials"]["access_token"]
    events = get_ms_availability(access_token)
    free_slots = get_free_slots(events)
    
    return jsonify({
        "Busy_slots": events,
        "Free_slots": free_slots
    })

@ms_bp.route("/microsoft/book", methods=["POST"])
def ms_book():
    if "ms_credentials" not in session:
        return redirect("/microsoft/login")
    
    data = request.json
    access_token = session["ms_credentials"]["access_token"]
    
    link = book_ms_meeting(
        access_token,
        titel=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        deltagare_email=data["email"]
    )
    
    return jsonify({
        "Message": "Meeting booked!",
        "Calendar_link": link
    })

@ms_bp.route("/microsoft/logout")
def ms_logout():
    session.pop("ms_credentials", None)
    return redirect("/")