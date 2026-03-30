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
    
    html = html.replace("{{LOGO_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/theshowcaseai_logo.jpg")
    html = html.replace("{{BRAIN_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/imag.png")
    
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

def load_reminder_template(booking, reminder_type):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "..", "..", "templates", "emails", "reminder_template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    date_str, start_time = format_time(booking.get("start_time", ""))
    _, end_time = format_time(booking.get("end_time", ""))

    reminder_label = "Your meeting is in 1 hour" if reminder_type == "1h" else "Your meeting is tomorrow"

    html = html.replace("{{LOGO_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/theshowcaseai_logo.jpg")
    html = html.replace("{{BRAIN_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/imag.png")
    html = html.replace("{{REMINDER_LABEL}}", reminder_label)
    html = html.replace("{{MEETING_TITLE}}", booking.get("meeting_title", ""))
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{TIME_START}}", start_time)
    html = html.replace("{{TIME_END}}", end_time)
    html = html.replace("{{LEAD_NAME}}", booking.get("lead_name", ""))
    html = html.replace("{{LEAD_EMAIL}}", booking.get("lead_email", ""))
    html = html.replace("{{CALENDAR_LINK}}", booking.get("calendar_link", "") or "#")

    return html

def send_reminder_email(booking, reminder_type="24h"):
    r = get_resend()
    html = load_reminder_template(booking, reminder_type)

    if reminder_type == "1h":
        subject = f"Reminder: Your meeting starts in 1 hour — {booking.get('meeting_title', '')}"
    else:
        subject = f"Reminder: Your meeting is tomorrow — {booking.get('meeting_title', '')}"

    r.Emails.send({"from": FROM, "to": booking.get("lead_email"), "subject": subject, "html": html})

    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if admin_email:
        r.Emails.send({"from": FROM, "to": admin_email, "subject": subject, "html": html})

def load_pending_reminder_template(booking):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "..", "..", "templates", "emails", "pending_reminder_template.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    date_str, start_time = format_time(booking.get("start_time", ""))
    _, end_time = format_time(booking.get("end_time", ""))

    html = html.replace("{{LOGO_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/theshowcaseai_logo.jpg")
    html = html.replace("{{BRAIN_URL}}", "https://raw.githubusercontent.com/Edris9/KALENDER_INTEGRATION/main/templates/emails/imag.png")
    html = html.replace("{{REMINDER_LABEL}}", "You have a pending meeting invitation")
    html = html.replace("{{MEETING_TITLE}}", booking.get("meeting_title", ""))
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{TIME_START}}", start_time)
    html = html.replace("{{TIME_END}}", end_time)
    html = html.replace("{{LEAD_NAME}}", booking.get("lead_name", ""))
    html = html.replace("{{LEAD_EMAIL}}", booking.get("lead_email", ""))
    html = html.replace("{{CALENDAR_LINK}}", booking.get("calendar_link", "") or "#")

    return html

def send_pending_reminder_email(booking):
    r = get_resend()
    html = load_pending_reminder_template(booking)
    subject = f"Reminder: You have a pending meeting invitation — {booking.get('meeting_title', '')}"
    r.Emails.send({"from": FROM, "to": booking.get("lead_email"), "subject": subject, "html": html})