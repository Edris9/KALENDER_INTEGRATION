from xmlrpc import client
from middleware.auth import admin_required
from flask import Blueprint, render_template, request, session, redirect, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from services.google.calendar_reader import get_availability
from services.google.calendar_writer import book_meeting
from services.google.supabase_client import supabase
from utils.time_utils import get_free_slots
import ast
from services.microsoft.ms_calendar_reader import get_ms_availability
from services.microsoft.ms_auth import refresh_ms_token
from services.google.email_service import send_booking_confirmation_lead, send_booking_confirmation_client

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


@admin_bp.route("/admin/unread-bookings")
@admin_required
def unread_bookings():
    result = supabase.table("bookings").select("id").eq("is_read", False).execute()
    return jsonify({"count": len(result.data)})

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect("/admin")
        else:
            return render_template("admin/admin_login.html", error="Wrong username or password!")
    return render_template("admin/admin_login.html")

@admin_bp.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin/admin.html")

@admin_bp.route("/admin/clients")
@admin_required
def get_clients():
    result = supabase.table("clients").select("id, name, email, connected_at").execute()
    return jsonify({"clients": result.data})

@admin_bp.route("/admin/availability/<client_id>")
@admin_required
def client_availability(client_id):
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    result = supabase.table("clients").select("*").eq("id", client_id).execute()
    
    if not result.data:
        return jsonify({"error": "Client not found"}), 404
    
    client = result.data[0]
    provider = client.get("provider", "google")

    if provider == "microsoft":
        new_token = refresh_ms_token(client["refresh_token"])
        if new_token:
            supabase.table("clients").update({
                "token": new_token
            }).eq("id", client["id"]).execute()
            access_token = new_token
        else:
            access_token = client["token"]
        
        events = get_ms_availability(access_token)
        print("MS EVENTS:", events[:2])  # ← flytta hit!
        free_slots = get_free_slots(events)
        return jsonify({"Free_slots": free_slots})
    
    # Google
    scopes = ast.literal_eval(client["scopes"]) if client["scopes"] else []
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
    provider = client.get("provider", "google")
    data = request.json
    lead_name = data.get("title", "").replace("Meeting with ", "")

    if provider == "microsoft":
        from services.microsoft.ms_calendar_writer import book_ms_meeting
        link, event_id = book_ms_meeting(
            client["token"],
            titel=data["title"],
            start_tid=data["start_tid"],
            end_tid=data["slut_tid"],
            deltagare_email=data["email"],
            client_email=client["email"]
        )
    else:
        credentials = refresh_credentials(client)
        link, event_id = book_meeting(
            credentials,
            titel=data["title"],
            start_tid=data["start_tid"],
            end_tid=data["slut_tid"],
            deltagare_email=data["email"],
            client_email=client["email"]
        )
        print(f"link: {link}, event_id: {event_id}")

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
        calendar_link=link,
        lead_name=lead_name,       
        lead_email=data["email"]    
    )
    
    supabase.table("bookings").insert({
        "client_id": client_id,
        "lead_name": lead_name,
        "lead_email": data["email"],
        "meeting_title": data["title"],
        "start_time": data["start_tid"].replace("+01:00", ""),
        "end_time": data["slut_tid"].replace("+01:00", ""),
        "calendar_link": link,
        "provider": provider,
        "status": "pending",
        "event_id": event_id  # ← lägg till denna
    }).execute()
    
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

@admin_bp.route("/admin/bookings")
@admin_required
def get_bookings():
    client_id = request.args.get("client_id")
    query = supabase.table("bookings").select("*").order("start_time", desc=True)
    if client_id:
        query = query.eq("client_id", client_id)
    result = query.execute()
    return jsonify({"bookings": result.data})

@admin_bp.route("/admin/bookings/mark-read", methods=["POST"])
@admin_required
def mark_bookings_read():
    supabase.table("bookings").update({"is_read": True}).eq("is_read", False).execute()
    return jsonify({"ok": True})


@admin_bp.route("/admin/reminders")
@admin_required
def get_reminders():
    client_id = request.args.get("client_id")
    
    query = supabase.table("bookings").select(
        "lead_name, lead_email, start_time, status, reminder_24h_sent, reminder_1h_sent, client_id"
    )
    if client_id:
        query = query.eq("client_id", client_id)
    
    bookings = query.order("start_time", desc=False).execute().data

    # Hämta klientnamn
    clients = {c["id"]: c["name"] for c in supabase.table("clients").select("id, name").execute().data}

    reminders = []
    for b in bookings:
        reminders.append({
            **b,
            "client_name": clients.get(b["client_id"], "Unknown")
        })

    return jsonify({"reminders": reminders})

@admin_bp.route("/admin/statistics/data")
@admin_required
def statistics_data():
    bookings = supabase.table("bookings").select("*").execute().data
    clients = supabase.table("clients").select("*").execute().data

    # KPIs
    total = len(bookings)
    confirmed = len([b for b in bookings if b["status"] == "confirmed"])
    pending = len([b for b in bookings if b["status"] == "pending"])
    cancelled = len([b for b in bookings if b["status"] == "cancelled"])
    tentative = len([b for b in bookings if b["status"] == "tentative"])
    response_rate = round((confirmed / total * 100), 1) if total > 0 else 0

    # Per klient
    clients_data = []
    for c in clients:
        client_bookings = [b for b in bookings if b["client_id"] == c["id"]]
        clients_data.append({
            "name": c["name"] + " (" + c["email"] + ")",
            "total": len(client_bookings),
            "confirmed": len([b for b in client_bookings if b["status"] == "confirmed"]),
            "cancelled": len([b for b in client_bookings if b["status"] == "cancelled"]),
        })

    # Per månad
    from collections import defaultdict
    monthly = defaultdict(int)
    for b in bookings:
        month = b["start_time"][:7]  # "2026-03"
        monthly[month] += 1
    bookings_per_month = [{"month": k, "count": v} for k, v in sorted(monthly.items())]

    # Populäraste timmar
    hours = defaultdict(int)
    for b in bookings:
        hour = b["start_time"][11:16]  # "09:00"
        hours[hour] += 1
    popular_hours = [{"hour": k, "count": v} for k, v in sorted(hours.items())]

    # Svarsfrekvens per klient
    response_rate_per_client = []
    for c in clients_data:
        rate = round((c["confirmed"] / c["total"] * 100), 1) if c["total"] > 0 else 0
        response_rate_per_client.append({"name": c["name"], "rate": rate})

    return jsonify({
        "total_bookings": total,
        "confirmed": confirmed,
        "pending": pending,
        "cancelled": cancelled,
        "tentative": tentative,
        "response_rate": response_rate,
        "clients": clients_data,
        "bookings_per_month": bookings_per_month,
        "popular_hours": popular_hours,
        "response_rate_per_client": response_rate_per_client
    })