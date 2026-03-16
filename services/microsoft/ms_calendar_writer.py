import requests

def book_ms_meeting(access_token, titel, start_tid, end_tid, deltagare_email, client_email=""):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    event = {
        "subject": titel,
        "start": {
            "dateTime": start_tid,
            "timeZone": "Europe/Stockholm"
        },
        "end": {
            "dateTime": end_tid,
            "timeZone": "Europe/Stockholm"
        },
        "attendees": [
            {
                "emailAddress": {"address": deltagare_email},
                "type": "required"
            },
            {
                "emailAddress": {"address": client_email},
                "type": "required"
            }
        ],
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }
    
    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/events",
        headers=headers,
        json=event
    )
    
    data = response.json()
    return data.get("webLink")