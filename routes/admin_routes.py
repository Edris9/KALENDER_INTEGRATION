from flask import Blueprint, render_template, request, session, redirect, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from services.calendar_reader import get_availability
from services.calendar_writer import book_meeting
from services.supabase_client import supabase
from utils.time_utils import get_free_slots
from services.email_service import send_booking_confirmation_lead, send_booking_confirmation_client

admin_bp = Blueprint("admin", __name__)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "showcase123"

def refresh_credentials(client):
    """Förnyar token automatiskt om den gått ut"""
    import ast
    scopes = ast.literal_eval(client["scopes"])
    
    credentials = Credentials(
        token=client["token"],
        refresh_token=client["refresh_token"],
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=scopes
    )
    
    # Förnya om token gått ut
    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
        # Spara nya token i Supabase
        supabase.table("clients").update({
            "token": credentials.token
        }).eq("id", client["id"]).execute()
    
    return credentials

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
    
    result = supabase.table("clients").select("id, name, email, connected_at").execute()
    
    return jsonify({"clients": result.data})

@admin_bp.route("/admin/availability/<client_id>")
def client_availability(client_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    result = supabase.table("clients").select("*").eq("id", client_id).execute()
    
    if not result.data:
        return jsonify({"error": "Client not found"}), 404
    
    client = result.data[0]
    
    import ast
    scopes = ast.literal_eval(client["scopes"])
    
    credentials = refresh_credentials(client)
    
    events = get_availability(credentials)
    free_slots = get_free_slots(events)
    
    return jsonify({"Free_slots": free_slots})

@admin_bp.route("/admin/book/<client_id>", methods=["POST"])
def admin_book(client_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    result = supabase.table("clients").select("*").eq("id", client_id).execute()
    
    if not result.data:
        return jsonify({"error": "Client not found"}), 404
    
    client = result.data[0]
    
    import ast
    scopes = ast.literal_eval(client["scopes"])
    
    credentials = refresh_credentials(client)
    
    data = request.json
    link = book_meeting(
        credentials,
        titel=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        deltagare_email=data["email"],
        client_email=client["email"]
    )
    lead_name = data.get("title", "").replace("Meeting with ", "")

    send_booking_confirmation_lead(
        lead_email=data["email"],
        lead_name=lead_name,
        meeting_title=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        calendar_link=link,
        client_name=client["name"],      
        client_email=client["email"] 
    )

    send_booking_confirmation_client(
        client_email=client["email"],
        client_name=client["name"],
        meeting_title=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        calendar_link=link
    )
    
    # Uppdatera total_meetings
    supabase.table("clients").update({
        "total_meetings": client["total_meetings"] + 1
    }).eq("id", client_id).execute()
    
    return jsonify({
        "Message": "Meeting booked!",
        "Calendar_link": link
    })

@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect("/admin/login")