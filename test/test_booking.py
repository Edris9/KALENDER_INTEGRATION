import pytest
import requests
from datetime import datetime, timedelta

# ─── KONFIGURATION ───
BASE_URL = "http://localhost:5000"
SESSION_COOKIE = "eyJpc19hZG1pbiI6dHJ1ZSwic3RhdGUiOiJyNG4yVGhGV3NsdWwweHlCcVNUZjJURHM1NWZpWnIifQ.ab0Zhg.kcvEayQcY3kLgQJwCTeSG1BQjO4"

# Generera unika tider för varje test (ingen krock!)
def get_slot(index):
    base = datetime(2026, 3, 30, 9, 0, 0)  # Måndag 30 Mars
    start = base + timedelta(hours=index)
    end = start + timedelta(hours=1)
    return (
        start.strftime("%Y-%m-%dT%H:%M:%S+01:00"),
        end.strftime("%Y-%m-%dT%H:%M:%S+01:00")
    )

TEST_CASES = [
    {"name": "Google (showcase) → Outlook (edris1010)", "client_id": "0cbbf500-8277-4ba6-a575-b5de1bc7668a", "lead_email": "edriskohestani1010@outlook.com"},
    {"name": "Outlook (edris1010) → Google (showcase)", "client_id": "d1f0626b-efcc-416c-a3eb-169e0bfe6659", "lead_email": "edris@theshowcase.ai"},
    {"name": "Google (showcase) → Gmail (edris1010)",   "client_id": "0cbbf500-8277-4ba6-a575-b5de1bc7668a", "lead_email": "edriskohestani1010@gmail.com"},
    {"name": "Gmail (edris1010) → Google (showcase)",   "client_id": "d069b7b3-7299-4b88-af6f-1a904b6a3b69", "lead_email": "edris@theshowcase.ai"},
    {"name": "Outlook (edris1010) → Outlook (school)",  "client_id": "d1f0626b-efcc-416c-a3eb-169e0bfe6659", "lead_email": "edris.kohestani@student.nbi-handelsakademin.se"},
    {"name": "Outlook (edris1010) → Gmail (edris1010)", "client_id": "d1f0626b-efcc-416c-a3eb-169e0bfe6659", "lead_email": "edriskohestani1010@gmail.com"},
    {"name": "Gmail (edris1010) → Outlook (edris1010)", "client_id": "d069b7b3-7299-4b88-af6f-1a904b6a3b69", "lead_email": "edriskohestani1010@outlook.com"},
]

# Räknare
email_counter = {
    "edris@theshowcase.ai": 0,
    "edriskohestani1010@gmail.com": 0,
    "edriskohestani1010@outlook.com": 0,
    "edris.kohestani@student.nbi-handelsakademin.se": 0
}

def count_emails(lead_email, client_email):
    """Räknar förväntade emails per bokning"""
    
    # Resend bekräftelse till klient
    email_counter[client_email] += 1
    print(f"   📧 Resend bekräftelse → {client_email}")

    # Resend bekräftelse + kalender inbjudan till lead
    email_counter[lead_email] += 1
    print(f"   📧 Resend bekräftelse → {lead_email}")
    
    email_counter[lead_email] += 1
    print(f"   📨 Kalender inbjudan → {lead_email}  ⭐ VIKTIG!")

    # När lead accepterar → klient får acceptans-notis
    email_counter[client_email] += 1
    print(f"   ✅ Acceptans-notis (när lead accepterar) → {client_email}  ⭐ VIKTIG!")

# Mappa client_id till email
CLIENT_EMAILS = {
    "0cbbf500-8277-4ba6-a575-b5de1bc7668a": "edris@theshowcase.ai",
    "d069b7b3-7299-4b88-af6f-1a904b6a3b69": "edriskohestani1010@gmail.com",
    "d1f0626b-efcc-416c-a3eb-169e0bfe6659": "edriskohestani1010@outlook.com"
}

@pytest.mark.parametrize("case,index", [(c, i) for i, c in enumerate(TEST_CASES)], ids=[c["name"] for c in TEST_CASES])
def test_booking(case, index):
    start, end = get_slot(index)
    client_email = CLIENT_EMAILS[case["client_id"]]

    print(f"\n🔖 Test: {case['name']}")
    print(f"   ⏰ Tid: {start} → {end}")

    response = requests.post(
        f"{BASE_URL}/admin/book/{case['client_id']}",
        json={
            "title": f"Test: {case['name']}",
            "start_tid": start,
            "slut_tid": end,
            "email": case["lead_email"]
        },
        cookies={"session": SESSION_COOKIE}
    )

    data = response.json()
    assert response.status_code == 200
    assert data.get("Message") == "Meeting booked!"

    count_emails(case["lead_email"], client_email)

def verify_invitation(credentials, lead_email, start_tid):
    """Kollar att lead fick kalender inbjudan"""
    from googleapiclient.discovery import build
    service = build("calendar", "v3", credentials=credentials)
    
    events = service.events().list(
        calendarId="primary",
        timeMin=start_tid,
        maxResults=5
    ).execute()
    
    for event in events.get("items", []):
        attendees = event.get("attendees", [])
        for a in attendees:
            if a["email"] == lead_email:
                print(f"   📨 Inbjudan bekräftad → {lead_email} (status: {a.get('responseStatus')})")
                return True
    
    print(f"   ❌ Ingen inbjudan hittad för → {lead_email}")
    return False

