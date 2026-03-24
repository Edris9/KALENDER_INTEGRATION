from flask import Blueprint, request, jsonify
from services.google.supabase_client import supabase
from services.microsoft.ms_auth import refresh_ms_token
import requests as req

ms_webhook_bp = Blueprint("ms_webhook", __name__)

@ms_webhook_bp.route("/webhook/microsoft", methods=["GET", "POST"])
def ms_webhook():

    # Microsoft skickar en validerings-request första gången
    validation_token = request.args.get("validationToken")
    if validation_token:
        print("MS Webhook validation request received")
        return validation_token, 200, {"Content-Type": "text/plain"}

    print("MS WEBHOOK HIT!")
    print("Body:", request.json)

    notifications = request.json.get("value", [])

    for notification in notifications:
        client_state = notification.get("clientState")
        if client_state != "showcase-secret":
            print("Invalid clientState, skipping")
            continue

        resource = notification.get("resource", "")
        # resource format: "Users/{user-id}/Events/{event-id}"
        event_id = resource.split("/")[-1] if "/" in resource else None

        if not event_id:
            continue

        print(f"Processing MS event_id: {event_id}")

        # Hitta bokning med detta event_id
        booking_result = supabase.table("bookings")\
            .select("*")\
            .eq("event_id", event_id)\
            .eq("provider", "microsoft")\
            .execute()

        if not booking_result.data:
            print(f"No booking found for event_id: {event_id}")
            continue

        booking = booking_result.data[0]

        # Hämta klienten
        client_result = supabase.table("clients")\
            .select("*")\
            .eq("id", booking["client_id"])\
            .execute()

        if not client_result.data:
            continue

        client = client_result.data[0]

        # Förnya token
        access_token = refresh_ms_token(client["refresh_token"]) or client["token"]

        # Hämta event från Microsoft Graph
        try:
            event_response = req.get(
                f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            ).json()

            attendees = event_response.get("attendees", [])
            for attendee in attendees:
                email = attendee.get("emailAddress", {}).get("address", "").lower()
                status = attendee.get("status", {}).get("response", "").lower()

                if email == booking["lead_email"].lower():
                    if status == "accepted":
                        new_status = "confirmed"
                    elif status == "declined":
                        new_status = "cancelled"
                    elif status == "tentativelyAccepted":
                        new_status = "tentative"
                    else:
                        continue

                    supabase.table("bookings").update({
                        "status": new_status
                    }).eq("id", booking["id"]).execute()
                    print(f"Updated MS booking {booking['id']} → {new_status}")

        except Exception as e:
            print(f"ERROR processing MS event: {e}")
            import traceback
            traceback.print_exc()

    return jsonify({}), 202