from flask import Blueprint, render_template, request, session, redirect, jsonify
from google.oauth2.credentials import Credentials
from services.calendar_reader import get_availability
from services.calendar_writer import book_meeting
from services.Supabase_Client import supabase
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
    
    credentials = Credentials(
        token=client["token"],
        refresh_token=client["refresh_token"],
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=scopes
    )
    
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
    
    credentials = Credentials(
        token=client["token"],
        refresh_token=client["refresh_token"],
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=scopes
    )
    
    data = request.json
    link = book_meeting(
        credentials,
        titel=data["title"],
        start_tid=data["start_tid"],
        end_tid=data["slut_tid"],
        deltagare_email=data["email"]
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