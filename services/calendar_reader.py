from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta

def get_availability(credentials):
    service = build("calendar", "v3", credentials=credentials)
    
    now = datetime.now(timezone.utc)
    ten_days_later = (now + timedelta(days=10)).isoformat()
    now_iso = now.isoformat()
    
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now_iso,
        timeMax=ten_days_later,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    
    slots = []
    for event in events:
        start = event["start"].get("dateTime") or event["start"].get("date")
        end = event["end"].get("dateTime") or event["end"].get("date")
        
        # Filtrera bort händelser utan tid (heldag/fleråriga)
        if "T" not in str(start):
            continue
        
        slots.append({
            "titel": event.get("summary", "No title"),
            "Start": start,
            "End": end
        })
    
    return slots