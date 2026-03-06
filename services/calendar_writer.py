from googleapiclient.discovery import build

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
            {"email": deltagare_email}
        ]
    }
    
    event_result = service.events().insert(
        calendarId="primary",
        body=event,
        sendUpdates="all"
    ).execute()
    
    return event_result.get("htmlLink")