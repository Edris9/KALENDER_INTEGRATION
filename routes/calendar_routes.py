from flask import Blueprint, session, jsonify, request, redirect
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from services.google.calendar_reader import get_availability
from services.google.calendar_writer import book_meeting
from utils.time_utils import get_free_slots

calendar_bp = Blueprint("calendar", __name__)

@calendar_bp.route("/availability")
def availability():
    if "credentials" not in session:
        return redirect("/login")
    
    credentials = Credentials(**session["credentials"])
    
    # Förnya om utgången
    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
        session["credentials"]["token"] = credentials.token  # uppdatera session
    
    events = get_availability(credentials)
    free_slots = get_free_slots(events)
    
    return jsonify({
        "Busy_slots": events,
        "Free_slots": free_slots
    })

@calendar_bp.route("/book", methods=["POST"])
def book():
    if "credentials" not in session:
        return redirect("/login")
    
    data = request.json 
    credentials = Credentials(**session["credentials"])
    
    link = book_meeting(
        credentials,
        titel=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        
        deltagare_email=data["email"]
    )
    
    return jsonify({
        "Message": "Meeting booked!",
        "Calendar_link": link
    })