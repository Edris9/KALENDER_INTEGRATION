import requests
from datetime import datetime, timedelta

def get_ms_availability(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    now = datetime.utcnow()
    end = now + timedelta(days=10)
    
    url = (
        f"https://graph.microsoft.com/v1.0/me/calendarView"
        f"?startDateTime={now.strftime('%Y-%m-%dT%H:%M:%S')}"
        f"&endDateTime={end.strftime('%Y-%m-%dT%H:%M:%S')}"
    )
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    events = []
    for event in data.get("value", []):
        if event.get("isAllDay"):
            continue
        events.append({
            "Start": (datetime.fromisoformat(event["start"]["dateTime"][:19]) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "End": (datetime.fromisoformat(event["end"]["dateTime"][:19]) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return events