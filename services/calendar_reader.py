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
    # I services/calendar_reader.py
    for event in events:
        # Kolla dateTime först, annars date (för heldagar)
        start = event["start"].get("dateTime") or event["start"].get("date")
        slut = event["end"].get("dateTime") or event["end"].get("date")
        
        slots.append({
            "titel": event.get("summary", "Ingen titel"),
            "start": start,
            "slut": slut
        })
    
    return slots