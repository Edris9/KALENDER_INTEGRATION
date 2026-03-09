from flask import Blueprint, render_template, request, session, redirect, jsonify
from google.oauth2.credentials import Credentials
from services.calendar_reader import get_availability
from services.calendar_writer import book_meeting
from utils.time_utils import get_free_slots

admin_bp = Blueprint("admin", __name__)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "showcase123"

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect("/admin")
        else:
            return render_template("admin_login.html", error="Wrong username or password!")
    
    return render_template("admin_login.html")

@admin_bp.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return redirect("/admin/login")
    return render_template("admin.html")

@admin_bp.route("/admin/clients")
def get_clients():
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Tillfälligt — senare hämtar vi från Supabase
    clients = []
    if "credentials" in session:
        clients = [{
            "id": "current",
            "name": "Test Client",
            "email": "test@example.com"
        }]
    
    return jsonify({"clients": clients})

@admin_bp.route("/admin/availability/<client_id>")
def client_availability(client_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    credentials = Credentials(**session["credentials"])
    events = get_availability(credentials)
    free_slots = get_free_slots(events)
    
    return jsonify({
        "Free_slots": free_slots
    })

@admin_bp.route("/admin/book/<client_id>", methods=["POST"])
def admin_book(client_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
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

@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect("/admin/login")