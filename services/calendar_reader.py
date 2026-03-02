from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

def get_availability(credentials):
    service = build("calendar", "v3", credentials=credentials)
    
    now = datetime.now(timezone.utc)
    ten_days_later = (now + timedelta(days=10)).isoformat()
    now = now.isoformat()
    
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=ten_days_later,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    
    slots = []
    for event in events:
        slots.append({
            "titel": event.get("summary", "Ingen titel"),
            "start": event["start"].get("dateTime"),
            "slut": event["end"].get("dateTime")
        })
    
    return slots