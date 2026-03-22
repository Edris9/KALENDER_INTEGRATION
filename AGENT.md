# AGENT.md — Showcase Kalender-Integration

## Vad är projektet?
Showcase är ett AI-drivet B2B lead generation-bolag. De hittar leads på LinkedIn och bokar säljmöten åt sina klienter. Den här appen löser ett specifikt problem: när en lead säger "ja" — hur vet systemet när klienten är ledig, och hur bokas mötet automatiskt?

Appen är en Calendly-liknande applikation där:
- Klienter kopplar sitt Google eller Microsoft/Outlook Calendar
- Systemet läser klientens lediga tider automatiskt (09:00–17:00, 1h slots, 10 dagar framåt)
- Admin kan boka möten direkt i klientens kalender
- Automatiska branded emails skickas till alla parter via Resend

## Live URL
https://kalender-integration-1.onrender.com

## Tech Stack
| Teknologi | Användning |
|-----------|-----------|
| Python + Flask | Backend/server |
| Google Calendar API | Läsa/skriva Google kalender |
| Google OAuth 2.0 (PKCE) | Klient-inloggning för Google |
| Microsoft Graph API | Läsa/skriva Outlook kalender |
| Microsoft MSAL | Klient-inloggning för Microsoft |
| Supabase (PostgreSQL) | Databas — sparar klienters tokens + möten |
| Resend | Branded HTML emails |
| Render | Hosting/deployment |
| GitHub | Versionshantering |

## Projektstruktur
```
KALENDER_INTEGRATION/
├── app.py                          # Startar Flask, registrerar blueprints, laddar .env
├── config/
│   └── settings.py                 # SCOPES, REDIRECT_URI, CLIENT_SECRETS_FILE
├── services/
│   ├── google/
│   │   ├── calendar_reader.py      # Hämtar events från Google Calendar
│   │   ├── calendar_writer.py      # Skapar möten i Google Calendar
│   │   ├── email_service.py        # Skickar emails via Resend
│   │   ├── google_auth.py          # create_flow() hjälpfunktion
│   │   └── supabase_client.py      # Koppling till Supabase
│   └── microsoft/
│       ├── ms_auth.py              # MSAL OAuth + refresh_ms_token()
│       ├── ms_calendar_reader.py   # Hämtar events från Microsoft Graph API
│       └── ms_calendar_writer.py   # Skapar möten via Microsoft Graph API
├── routes/
│   ├── auth_routes.py              # /login, /callback, /logout (Google)
│   ├── calendar_routes.py          # /availability, /book (Google klient-sida)
│   ├── admin_routes.py             # /admin, /admin/login, /admin/clients, /admin/book
│   └── microsoft_routes.py        # /microsoft/login, /microsoft/callback
├── utils/
│   └── time_utils.py               # get_free_slots() — 09-17, 1h slots, 10 dagar
├── templates/
│   ├── index.html                  # Klient-sidan (Google + Microsoft connect)
│   ├── admin/
│   │   ├── admin_login.html        # Admin inloggning
│   │   └── admin.html              # Admin-panelen
│   └── emails/
│       ├── email_template.html     # Branded HTML email template
│       ├── imag.png                # Brain mascot bild
│       └── theshowcaseai_logo.jpg  # Showcase logga
├── static/
│   ├── styles.css / script.js      # Klient frontend
│   ├── admin.css / admin.js        # Admin frontend
│   └── admin-login.css / admin-login.js
├── models/
│   └── booking.py                  # Bokningsmodell (validering)
├── .env                            # Miljövariabler (EJ på GitHub!)
├── credentials.json                # Google OAuth credentials (EJ på GitHub!)
├── requirements.txt
└── Procfile                        # gunicorn app:app
```

## Användare & Flöden

### Klient
1. Går till startsidan `/`
2. Klickar "Connect Google Calendar" eller "Connect Microsoft Calendar"
3. Loggar in via OAuth
4. Token sparas i Supabase → admin kan nu boka möten åt klienten

### Admin
1. Går till `/admin/login` → loggar in med användarnamn + lösenord
2. Ser alla anslutna klienter från Supabase
3. Väljer klient → ser deras lediga tider
4. Bokar möte → emails skickas automatiskt till lead + klient

## Databas — Supabase
**Projekt:** nyhxkzjcxhljtzrwujde.supabase.co

### Tabell: `clients`

| Kolumn | Typ | Förklaring |
|--------|-----|-----------|
| id | UUID | Primary key (gen_random_uuid()) |
| name | TEXT | Klientens namn |
| email | TEXT | Klientens email (unique) |
| token | TEXT | OAuth access token (går ut ~1h) |
| refresh_token | TEXT | Förnyar access token automatiskt |
| token_uri | TEXT | Google token endpoint |
| client_id | TEXT | OAuth app ID |
| client_secret | TEXT | OAuth app secret |
| scopes | TEXT | Beviljade rättigheter (Google only) |
| is_active | BOOLEAN | Default: true |
| connected_at | TIMESTAMP | Default: now() |
| total_meetings | INTEGER | Default: 0 |
| provider | TEXT | "google" eller "microsoft" (default: "google") |

### Tabell: `meetings` ⏳ (planerad)

| Kolumn | Typ | Förklaring |
|--------|-----|-----------|
| id | UUID | Primary key (gen_random_uuid()) |
| client_id | UUID | FK → clients.id |
| lead_name | TEXT | Leadens namn |
| lead_email | TEXT | Leadens email |
| meeting_title | TEXT | Mötets titel |
| start_tid | TIMESTAMP | Starttid |
| end_tid | TIMESTAMP | Sluttid |
| provider | TEXT | "google" eller "microsoft" |
| calendar_link | TEXT | Länk till mötet i kalendern |
| status | TEXT | confirmed / cancelled / no-show / completed |
| booked_at | TIMESTAMP | Default: now() |

## Miljövariabler (.env)
```
# Google OAuth
GOOGLE_CREDENTIALS=<hela credentials.json som JSON-sträng>
REDIRECT_URI=http://localhost:5000/callback

# Supabase
SUPABASE_URL=https://nyhxkzjcxhljtzrwujde.supabase.co
SUPABASE_KEY=<anon key>

# Resend Email
RESEND_API_KEY=<api key>
RESEND_FROM_EMAIL=noreply@theshowcase.ai
RESEND_FROM_NAME=Showcase
ADMIN_EMAIL=edris@theshowcase.ai

# Microsoft OAuth
MS_CLIENT_ID=<azure client id>
MS_CLIENT_SECRET=<azure client secret>
MS_TENANT_ID=<azure tenant id>
MS_REDIRECT_URI=http://localhost:5000/microsoft/callback
```

## URL-struktur
| URL | Vad |
|-----|-----|
| / | Klient startsida |
| /login | Google OAuth start |
| /callback | Google OAuth callback |
| /logout | Klient loggar ut |
| /availability | API — lediga tider (JSON) |
| /book | API — boka möte (POST) |
| /microsoft/login | Microsoft OAuth start |
| /microsoft/callback | Microsoft OAuth callback |
| /admin/login | Admin inloggning |
| /admin | Admin panel |
| /admin/clients | API — alla klienter (JSON) |
| /admin/availability/<id> | API — klientens lediga tider |
| /admin/book/<id> | API — boka i klientens kalender (POST) |
| /admin/logout | Admin loggar ut |

## Viktiga regler & konventioner

### Säkerhet
- `.env` och `credentials.json` ska ALDRIG pushas till GitHub
- Båda ska finnas i `.gitignore`
- På Render sätts alla miljövariabler manuellt i Dashboard

### Token-hantering
- Google: `refresh_credentials(client)` i `admin_routes.py` förnyar automatiskt
- Microsoft: `refresh_ms_token(refresh_token)` i `ms_auth.py` förnyar automatiskt
- Ny token sparas alltid tillbaka i Supabase

### Provider-logik
- Varje klient har `provider = "google"` eller `provider = "microsoft"` i Supabase
- `admin_routes.py` kollar provider och väljer rätt API automatiskt

### Email-flöde
- Resend skickar branded HTML emails till lead + klient vid bokning
- Google Calendar skickar separat inbjudan via `sendUpdates="all"`
- Email template finns i `templates/emails/email_template.html`
- Platshållare: `{{LEAD_NAME}}`, `{{LEAD_EMAIL}}`, `{{ORGANISER_NAME}}`, `{{ORGANISER_EMAIL}}`, `{{MEETING_TITLE}}`, `{{DATE}}`, `{{TIME_START}}`, `{{TIME_END}}`, `{{CALENDAR_LINK}}`
- Kalender-länken är provider-specifik: Google → calendar.google.com, Microsoft → outlook.office.com

### Datetime-format
- Google: `2026-03-17T09:00:00+01:00`
- Microsoft: returnerar UTC → lägg till +1h för CET i `ms_calendar_reader.py`
- `time_utils.py` förväntar sig: `2026-03-17 09:00:00` (mellanslag, med sekunder)

## Projektstatus
| Fas | Status |
|-----|--------|
| Fas 1 — Google Calendar grundläggande | ✅ Klar |
| Fas 2 — Admin panel + Supabase + Emails | ✅ Klar |
| Microsoft/Outlook Calendar integration | ✅ Klar |
| Mappstruktur refaktorering (templates/emails, templates/admin) | ✅ Klar |
| Google App verifiering (publik) | ⏳ Väntar på Aviv |
| Meetings-tabell i Supabase | ⏳ Pausad |
| Fas 3 — Påminnelse-emails (APScheduler) | 🔜 Framtid |
| Fas 4 — Gmail ton-inlärning | 🔜 Framtid |
| Avboknings/ombokningsflöde | 🔜 Framtid |
| No-show tracking | 🔜 Framtid |
| CRM-export (CSV/Notion/HubSpot) | 🔜 Framtid |

## Deployment
- **Hosting:** Render (https://kalender-integration-1.onrender.com)
- **Start command:** `gunicorn app:app` (Procfile)
- **GitHub repo:** https://github.com/Edris9/TheShowCase.ai
- **Branches:** `main` (production), `dev_edris` (development), `dev_frontend` (frontend)
- Render deployas automatiskt vid push till `main`

## Teamet
- **Aviv Farhi** — Grundare/Chef på Showcase
- **Edris Kohestani** — Utvecklare, onboarding-projekt





Möteshistorik — se alla bokade möten per klient
Status-hantering — confirmed / cancelled / no-show / completed
Påminnelse-emails — APScheduler skickar auto-påminnelse 24h före (du har redan planerat fas 3!)
Statistik i admin — antal möten per klient, konverteringsgrad
Avbokningsflöde — lead klickar länk → mötet markeras cancelled i både DB och kalender
Ombokningsflöde — lead väljer ny tid utan att admin behöver göra något
No-show tracking — markera om lead dök upp eller inte
CRM-export — exportera möten till CSV/Notion/HubSpot