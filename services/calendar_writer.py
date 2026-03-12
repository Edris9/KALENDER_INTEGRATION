from googleapiclient.discovery import build

ADMIN_EMAIL = "edris@theshowcase.ai"  # ← din email  

def book_meeting(credentials, titel, start_tid, end_tid, deltagare_email):
    service = build("calendar", "v3", credentials=credentials)
    
    event = {
        "summary": titel,
        "start": {
            "dateTime": start_tid,
            "timeZone": "Europe/Stockholm"
        },
        "end": {
            "dateTime": end_tid,
            "timeZone": "Europe/Stockholm"
        },
        "attendees": [
            {"email": deltagare_email},
            {"email": ADMIN_EMAIL}  # ← Admin får också inbjudan + notis
        ]
    }
    
    event_result = service.events().insert(
        calendarId="primary",
        body=event,
        sendUpdates="all"  # Skickar email till ALLA deltagare
    ).execute()
    
    return event_result.get("htmlLink")