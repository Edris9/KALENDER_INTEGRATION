from flask import Blueprint, request
from services.google.supabase_client import supabase
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import ast

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook/google", methods=["GET", "POST"])
def google_webhook():
    print("WEBHOOK HIT!")
    print("Headers:", dict(request.headers))
    print("Body:", request.data)

    # Hämta alla Google-klienter
    clients = supabase.table("clients").select("*").eq("provider", "google").execute()
    print(f"Found {len(clients.data)} Google clients")

    for client in clients.data:
        print(f"Processing client: {client['email']}")
        try:
            scopes = ast.literal_eval(client["scopes"])
            creds = Credentials(
                token=client["token"],
                refresh_token=client["refresh_token"],
                token_uri=client["token_uri"],
                client_id=client["client_id"],
                client_secret=client["client_secret"],
                scopes=scopes
            )
            if creds.expired:
                creds.refresh(Request())

            service = build("calendar", "v3", credentials=creds)

            # Hämta bokningar för denna klient
            bookings = supabase.table("bookings").select("*")\
                .eq("client_id", client["id"])\
                .eq("provider", "google")\
                .not_.is_("event_id", "null")\
                .execute()
            print(f"Found {len(bookings.data)} bookings for {client['email']}")

            for booking in bookings.data:
                print(f"Checking booking: {booking['id']} event_id: {booking['event_id']}")
                event = service.events().get(
                    calendarId="primary",
                    eventId=booking["event_id"]
                ).execute()
                

                attendees = event.get("attendees", [])
                for attendee in attendees:
                    if attendee.get("email") == booking["lead_email"]:
                        response = attendee.get("responseStatus")
                        if response == "accepted":
                            new_status = "confirmed"
                        elif response == "declined":
                            new_status = "cancelled"
                        elif response == "tentative":
                            new_status = "tentative"
                        else:
                            continue

                        supabase.table("bookings").update({
                            "status": new_status
                        }).eq("id", booking["id"]).execute()
                        print(f"Updated booking {booking['id']} → {new_status}")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

    return "", 200