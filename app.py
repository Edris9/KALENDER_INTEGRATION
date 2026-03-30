from dotenv import load_dotenv
load_dotenv()
from flask import Flask, session, redirect, render_template
from routes.auth_routes import auth_bp
from routes.calendar_routes import calendar_bp
from routes.admin_routes import admin_bp
from routes.google_webhook import webhook_bp
from routes.microsoft_routes import ms_bp
from routes.ms_webhook import ms_webhook_bp
from apscheduler.schedulers.background import BackgroundScheduler
from services.google.supabase_client import supabase
from services.google.email_service import send_reminder_email
from datetime import datetime, timezone
import os
from zoneinfo import ZoneInfo
from services.google.email_service import send_reminder_email, send_pending_reminder_email

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__)
app.secret_key = "super_hemlig_nyckel_123"

app.register_blueprint(admin_bp)

app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return '''
    <script>
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
        window.location.href = "/";
    </script>
    '''

# ── APScheduler ──────────────────────────────────────────────
def check_1h_reminders():
    CET = ZoneInfo("Europe/Stockholm")
    now = datetime.now(CET)
    print(f"⏰ check_1h_reminders() kördes — now: {now}")
    
    bookings = supabase.table("bookings").select("*").eq("status", "confirmed").execute().data
    print(f"📋 Hittade {len(bookings)} confirmed bokningar")

    for b in bookings:
        try:
            start = datetime.fromisoformat(b["start_time"])
            if start.tzinfo is None:
                start = start.replace(tzinfo=CET)
            
            diff_hours = (start - now).total_seconds() / 3600
            print(f"🔍 {b['id'][:8]}... | diff_hours: {diff_hours:.2f} | reminder_1h_sent: {b['reminder_1h_sent']}")

            if not b["reminder_1h_sent"] and 0 < diff_hours <= 1:
                print(f"📧 Skickar 1h påminnelse till {b['lead_email']}")
                send_reminder_email(b, reminder_type="1h")
                supabase.table("bookings").update({"reminder_1h_sent": True}).eq("id", b["id"]).execute()
                print(f"✅ Skickad!")

        except Exception as e:
            print(f"Reminder error for booking {b['id']}: {e}")

def check_24h_reminders():
    CET = ZoneInfo("Europe/Stockholm")
    now = datetime.now(CET)
    print(f"⏰ check_24h_reminders() kördes — now: {now}")

    bookings = supabase.table("bookings").select("*").eq("status", "pending").execute().data
    print(f"📋 Hittade {len(bookings)} pending bokningar")

    for b in bookings:
        try:
            start = datetime.fromisoformat(b["start_time"])
            if start.tzinfo is None:
                start = start.replace(tzinfo=CET)

            booked_at = datetime.fromisoformat(b["booked_at"])
            if booked_at.tzinfo is None:
                booked_at = booked_at.replace(tzinfo=CET)

            diff_hours = (start - now).total_seconds() / 3600
            hours_since_booking = (now - booked_at).total_seconds() / 3600
            print(f"🔍 {b['id'][:8]}... | diff_hours: {diff_hours:.2f} | hours_since_booking: {hours_since_booking:.2f} | reminder_24h_sent: {b['reminder_24h_sent']}")

            if not b["reminder_24h_sent"] and hours_since_booking >= 24 and diff_hours > 0:
                print(f"📧 Skickar 24h påminnelse till {b['lead_email']}")
                send_pending_reminder_email(b)
                supabase.table("bookings").update({"reminder_24h_sent": True}).eq("id", b["id"]).execute()
                print(f"✅ Skickad!")

        except Exception as e:
            print(f"❌ Error: {e}")

@app.route("/test-1h-reminder")
def test_1h_reminder():
    check_1h_reminders()
    return "✅ 1h reminder kördes — kolla emailen!"

@app.route("/test-24h-reminder")
def test_24h_reminder():
    check_24h_reminders()
    return "✅ 24h reminder kördes — kolla emailen!"

scheduler = BackgroundScheduler()
scheduler.add_job(check_1h_reminders, "interval", minutes=1)
scheduler.add_job(check_24h_reminders, "interval", minutes=1)
scheduler.start()

# Registrera routes
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(ms_bp)
app.register_blueprint(ms_webhook_bp)
app.secret_key = "showcase_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.register_blueprint(webhook_bp)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)