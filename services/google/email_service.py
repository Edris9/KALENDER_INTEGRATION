import os
import resend
from datetime import datetime
import base64

FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "noreply@theshowcase.ai")
FROM_NAME = os.environ.get("RESEND_FROM_NAME", "Showcase")
FROM = f"{FROM_NAME} <{FROM_EMAIL}>"


def get_resend():
    resend.api_key = os.environ.get("RESEND_API_KEY")
    return resend

def format_time(dt_str):
    dt = datetime.fromisoformat(dt_str.replace('+01:00', ''))
    return dt.strftime("%A %d %B %Y"), dt.strftime("%H:%M")

def load_template(lead_name, lead_email, meeting_title, start_tid, end_tid, calendar_link="", client_name="", client_email=""):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "..", "..", "templates", "emails", "email_template.html")
    logo_path = os.path.join(base_dir, "..", "..", "templates", "emails", "theshowcaseai_logo.jpg")
    brain_path = os.path.join(base_dir, "..", "..", "templates", "emails", "imag.png")
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    with open(brain_path, "rb") as f:
        brain_b64 = base64.b64encode(f.read()).decode()
    
    html = html.replace("{{LOGO_URL}}", f"data:image/jpeg;base64,{logo_b64}")
    html = html.replace("{{BRAIN_URL}}", f"data:image/png;base64,{brain_b64}")
    
    date_str, start_time = format_time(start_tid)
    _, end_time = format_time(end_tid)
    
    html = html.replace("{{LEAD_NAME}}", lead_name)
    html = html.replace("{{LEAD_EMAIL}}", lead_email)
    html = html.replace("{{MEETING_TITLE}}", meeting_title)
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{TIME_START}}", start_time)
    html = html.replace("{{TIME_END}}", end_time)
    html = html.replace("{{CALENDAR_LINK}}", calendar_link or "#")
    html = html.replace("{{ORGANISER_NAME}}", client_name)
    html = html.replace("{{ORGANISER_EMAIL}}", client_email)
        
    return html

def send_booking_confirmation_lead(lead_email, lead_name, meeting_title, start_tid, end_tid, calendar_link="", client_name="", client_email=""):
    r = get_resend()
    html = load_template(lead_name, lead_email, meeting_title, start_tid, end_tid, calendar_link, client_name, client_email)
    r.Emails.send({
        "from": FROM,
        "to": lead_email,
        "subject": f"Meeting Confirmed: {meeting_title}",
        "html": html
    })

def send_booking_confirmation_client(client_email, client_name, meeting_title, start_tid, end_tid, calendar_link="", lead_name="", lead_email=""):
    r = get_resend()
    html = load_template(lead_name, lead_email, meeting_title, start_tid, end_tid, calendar_link, client_name, client_email)
    r.Emails.send({
        "from": FROM,
        "to": client_email,
        "subject": f"New Meeting Booked: {meeting_title}",
        "html": html
    })