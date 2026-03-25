# AGENT.md — Showcase Kalender-Integration

## Vad är projektet?
Showcase är ett AI-drivet B2B lead generation-bolag. De hittar leads på LinkedIn och bokar säljmöten åt sina klienter. Den här appen löser ett specifikt problem: när en lead säger "ja" — hur vet systemet när klienten är ledig, och hur bokas mötet automatiskt?

Appen är en Calendly-liknande applikation där:
- Klienter kopplar sitt Google eller Microsoft/Outlook Calendar
- Systemet läser klientens lediga tider automatiskt (09:00–17:00, 1h slots, 10 dagar framåt)
- Admin kan boka möten direkt i klientens kalender
- Automatiska branded emails skickas till alla parter via Resend
- Status uppdateras automatiskt via Google/Microsoft webhook när lead accepterar/avböjer

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
| Supabase (PostgreSQL) | Databas — sparar klienters tokens + bokningar |
| Resend | Branded HTML emails (bilder via GitHub raw-URL) |
| APScheduler | Bakgrundsjobb för påminnelse-emails |
| Render | Hosting/deployment |
| GitHub | Versionshantering |

## Projektstruktur
```
KALENDER_INTEGRATION/
├── app.py                          # Startar Flask, registrerar blueprints, laddar .env, startar APScheduler
├── config/
│   └── settings.py                 # SCOPES, REDIRECT_URI, CLIENT_SECRETS_FILE
├── services/
│   ├── google/
│   │   ├── calendar_reader.py      # Hämtar events från Google Calendar
│   │   ├── calendar_writer.py      # Skapar möten — returnerar (htmlLink, event_id)
│   │   ├── email_service.py        # Skickar emails via Resend (bilder via GitHub raw-URL)
│   │   ├── google_auth.py          # create_flow() hjälpfunktion
│   │   └── supabase_client.py      # Koppling till Supabase
│   └── microsoft/
│       ├── ms_auth.py              # MSAL OAuth + refresh_ms_token()
│       ├── ms_calendar_reader.py   # Hämtar events från Microsoft Graph API
│       └── ms_calendar_writer.py   # Skapar möten — returnerar (webLink, event_id)
├── routes/
│   ├── auth_routes.py              # /login, /callback, /logout (Google) + startar webhook watch
│   ├── calendar_routes.py          # /availability, /book (Google klient-sida)
│   ├── admin_routes.py             # /admin, /admin/login, /admin/clients, /admin/book, /admin/bookings
│   ├── microsoft_routes.py         # /microsoft/login, /microsoft/callback + MS subscription
│   ├── google_webhook.py           # /webhook/google — tar emot Google Calendar notiser
│   └── ms_webhook.py               # /webhook/microsoft — tar emot Microsoft Graph notiser
├── middleware/
│   ├── __init__.py
│   └── auth.py                     # admin_required decorator — skyddar alla admin-routes
├── utils/
│   └── time_utils.py               # get_free_slots() — 09-17, 1h slots, 10 dagar
├── templates/
│   ├── index.html                  # Klient-sidan (Google + Microsoft connect)
│   ├── admin/
│   │   ├── admin_login.html        # Admin inloggning
│   │   └── admin.html              # Admin-panelen med sidebar + tabs + hamburger-meny
│   └── emails/
│       ├── email_template.html     # Branded HTML email template
│       ├── reminder_template.html  # Påminnelse email template (24h + 1h)
│       ├── imag.png                # Brain mascot bild
│       └── theshowcaseai_logo.jpg  # Showcase logga
├── static/
│   ├── css/
│   │   ├── styles.css              # Klient frontend
│   │   ├── admin.css               # Admin frontend (responsive)
│   │   └── admin-login.css         # Admin login
│   └── js/
│       ├── script.js               # Klient frontend
│       ├── admin.js                # Admin frontend (kalender-grid, tabs, auto-refresh, state restore)
│       └── admin-login.js          # Admin login
├── models/
│   └── booking.py                  # Bokningsmodell (validering)
├── .env                            # Miljövariabler (EJ på GitHub!)
├── credentials.json                # Google OAuth credentials (EJ på GitHub!)
├── requirements.txt
└── Procfile                        # web: gunicorn app:app
```

## Användare & Flöden

### Klient
1. Går till startsidan `/`
2. Klickar "Connect Google Calendar" eller "Connect Microsoft Calendar"
3. Loggar in via OAuth
4. Token sparas i Supabase → Google/Microsoft webhook watch startas automatiskt
5. Admin kan nu boka möten åt klienten

### Admin
1. Går till `/admin/login` → loggar in med användarnamn + lösenord
2. Ser alla anslutna klienter i sidebar (sticky, hamburger-meny på mobil)
3. Väljer klient → månadskalender-grid visas
4. Klickar på dag → lediga slots visas i panel till höger
5. Väljer slot → bokningsformulär visas under kalendern
6. Bokar möte → emails skickas automatiskt till lead + klient
7. Status sätts till `pending` → ändras automatiskt via webhook när lead svarar

### Webhook-flöde (Google)
1. Klient loggar in → `service.events().watch()` registreras hos Google
2. Lead accepterar/avböjer → Google POST:ar till `/webhook/google`
3. App hämtar event → kollar `attendees[].responseStatus`
4. Supabase uppdateras: `pending` → `confirmed` / `cancelled` / `tentative`

### Webhook-flöde (Microsoft)
1. Klient loggar in → subscription registreras via bakgrundstråd (3s delay) hos Microsoft Graph
2. Lead accepterar/avböjer → Microsoft POST:ar till `/webhook/microsoft`
3. App hämtar event → kollar `attendees[].status.response`
4. Supabase uppdateras: `pending` → `confirmed` / `cancelled` / `tentative`

### Påminnelse-flöde (APScheduler)
1. APScheduler kör ett jobb var 5:e minut i bakgrunden
2. Kollar alla bokningar där `status = confirmed` + mötet är om < 1h + `reminder_1h_sent = false` → skickar påminnelse-email + sätter `reminder_1h_sent = true`
3. Kollar alla bokningar där `status = pending` + mötet är om < 24h + `reminder_24h_sent = false` → skickar påminnelse-email + sätter `reminder_24h_sent = true`
4. Påminnelser visas i Reminders-taben i admin-panelen

## Databas — Supabase

> ⚠️ **Supabase-migration:** Nuvarande Supabase-projekt tillhör Edris privata konto.
> När Aviv skapar företagets Supabase-projekt:
> 1. Exportera data (CSV eller pg_dump)
> 2. Återskapa tabellerna i nya projektet
> 3. Importera datan
> 4. Byt ut `SUPABASE_URL` + `SUPABASE_KEY` i `.env` på Render
> Ingen kod behöver ändras.

**Nuvarande projekt:** nyhxkzjcxhljtzrwujde.supabase.co

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

### Tabell: `bookings`
| Kolumn | Typ | Förklaring |
|--------|-----|-----------|
| id | UUID | Primary key (gen_random_uuid()) |
| client_id | UUID | FK → clients.id |
| lead_name | TEXT | Leadens namn |
| lead_email | TEXT | Leadens email |
| meeting_title | TEXT | Mötets titel |
| start_time | TIMESTAMP | Starttid |
| end_time | TIMESTAMP | Sluttid |
| provider | TEXT | "google" eller "microsoft" |
| calendar_link | TEXT | Länk till mötet i kalendern |
| event_id | TEXT | Google/Microsoft event ID (för webhook-matchning) |
| status | TEXT | pending / confirmed / cancelled / tentative |
| booked_at | TIMESTAMP | Default: now() |
| is_read | BOOLEAN | Default: false — för notification badge |
| reminder_24h_sent | BOOLEAN | Default: false — skickas om pending + mötet är om < 24h |
| reminder_1h_sent | BOOLEAN | Default: false — skickas om confirmed + mötet är om < 1h |

## Admin-panel Features
- **Sidebar** — alla klienter i fast sidebar till vänster (width: 300px), hamburger-meny på mobil
- **Månadskalender** — grid-vy med navigation, helger röda, idag grön, dagar med slots har blå punkt
- **Slots-panel** — visas till höger om kalendern (stacked under på mobil)
- **Bokningsformulär** — visas under kalendern när slot väljs, auto-scroll
- **Tabs** — Calendar, Meeting History, Status, Reminders, Statistics, Cancellation, Reschedule, No-show, CRM Export
- **Tab hamburger-meny** — tabs kollapsar till dropdown på mobil
- **Notification badge** — röd siffra på Meeting History-taben för olästa bokningar
- **Auto-refresh** — Meeting History + badge uppdateras automatiskt var 10:e sekund
- **Status-badges** — 🟠 pending, 🟢 confirmed, 🔴 cancelled
- **State restore** — URL hash sparar vald klient + tab vid page refresh
- **Bokningar filtreras per klient** — `/admin/bookings?client_id=...`
- **Responsiv design** — fungerar på mobil och liten skärm

### Reminders-tab kolumner
| Kolumn | Förklaring |
|--------|-----------|
| **Lead** | Leadens namn + email |
| **Klient** | Vilken klient mötet tillhör |
| **Mötestid** | När mötet är |
| **24h påminnelse** | ✅ Skickad / ⏳ Väntar / ➖ Ej aktuell |
| **1h påminnelse** | ✅ Skickad / ⏳ Väntar / ➖ Ej aktuell |

> Status visas ej här — finns redan i Meeting History-taben.

## Miljövariabler (.env)
```
# Google OAuth
GOOGLE_CREDENTIALS=<hela credentials.json som JSON-sträng>
REDIRECT_URI=https://kalender-integration-1.onrender.com/callback

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
MS_REDIRECT_URI=https://kalender-integration-1.onrender.com/microsoft/callback
```

## URL-struktur
| URL | Metod | Vad |
|-----|-------|-----|
| / | GET | Klient startsida |
| /login | GET | Google OAuth start |
| /callback | GET | Google OAuth callback + startar webhook watch |
| /logout | GET | Klient loggar ut |
| /availability | GET | API — lediga tider (JSON) |
| /book | POST | API — boka möte |
| /microsoft/login | GET | Microsoft OAuth start |
| /microsoft/callback | GET | Microsoft OAuth callback + startar MS subscription |
| /webhook/google | POST | Google Calendar webhook notiser |
| /webhook/microsoft | POST | Microsoft Graph webhook notiser |
| /admin/login | GET/POST | Admin inloggning |
| /admin | GET | Admin panel |
| /admin/clients | GET | API — alla klienter (JSON) |
| /admin/availability/<id> | GET | API — klientens lediga tider |
| /admin/book/<id> | POST | API — boka i klientens kalender |
| /admin/bookings | GET | API — bokningar (filtrerbart per client_id) |
| /admin/bookings/mark-read | POST | Markera bokningar som lästa |
| /admin/unread-bookings | GET | Antal olästa bokningar |
| /admin/reminders | GET | API — påminnelsestatus per bokning |
| /admin/logout | GET | Admin loggar ut |

## Viktiga regler & konventioner

### Säkerhet
- `.env` och `credentials.json` ska ALDRIG pushas till GitHub
- Båda ska finnas i `.gitignore`
- På Render sätts alla miljövariabler manuellt i Dashboard
- Alla admin-routes skyddas av `@admin_required` middleware från `middleware/auth.py`

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
- Påminnelse-template finns i `templates/emails/reminder_template.html`
- Bilder laddas via GitHub raw-URL — INTE base64 (blockeras av email-klienter)
- Kalender-länk är provider-specifik: Google → calendar.google.com, Microsoft → outlook.office.com
- Knapp-text i email: "View in Calendar →" (generisk, fungerar för alla providers)

### Påminnelse-logik
- APScheduler kör var 5:e minut
- `confirmed` + mötet är om < 1h + `reminder_1h_sent = false` → skicka + sätt true
- `pending` + mötet är om < 24h + `reminder_24h_sent = false` → skicka + sätt true
- Flaggorna `reminder_24h_sent` + `reminder_1h_sent` i `bookings` förhindrar dubbel-emails

### Webhook-konventioner
- Google watch registreras i `/callback` vid varje klient-inloggning
- Microsoft subscription registreras i `/microsoft/callback` via bakgrundstråd (3s delay)
- Watch/subscription gäller i 7 dagar (Google) / 2 dagar (Microsoft) — klienten måste logga in igen för förnyelse
- Email-jämförelse görs alltid case-insensitive: `email.lower() == booking_email.lower()`
- `event_id` sparas alltid i `bookings` vid bokning för webhook-matchning
- `responseStatus` från Google/Microsoft API returnerar alltid på engelska oavsett användarens språkinställning
- Multilingual fallback finns i webhook-logiken som extra säkerhet

### Datetime-format
- Google: `2026-03-17T09:00:00+01:00`
- Microsoft: returnerar UTC → lägg till +1h för CET i `ms_calendar_reader.py`
- `time_utils.py` förväntar sig: `2026-03-17 09:00:00` (mellanslag, med sekunder)

### Static-filer
- CSS: `static/css/` — refereras via `url_for('static', filename='css/admin.css')`
- JS: `static/js/` — refereras via `url_for('static', filename='js/admin.js')`

### Frontend-konventioner
- Bokningsknappen återställs alltid (`btn.innerText = 'Confirm Booking'`, `btn.disabled = false`) både i `.then()` och `.catch()` för att undvika att knappen fastnar i "Booking..."-läge
- `restoreState()` rensar trasig URL hash med `window.location.hash = ''` i catch-blocket

## Kända buggar & lösningar
| Bugg | Lösning |
|------|---------|
| Email-bilder visas inte | Använd GitHub raw-URL istället för base64 |
| Webhook når inte appen | Klienten måste logga in igen för att registrera watch/subscription |
| Status uppdateras inte | lead_email jämförs case-insensitive med `.lower()` |
| event_id är null | Returnera tuple `(htmlLink, id)` från calendar_writer/ms_calendar_writer |
| Render "No open HTTP ports" | Lägg till `host="0.0.0.0"` i `app.run()` + kontrollera Procfile |
| MS subscription timeout | Använd `threading.Timer(3.0, ...)` för att registrera subscription i bakgrunden |
| Bokningsknapp fastnar i "Booking..." | Återställ knapp i både `.then()` och `.catch()` i `adminBookMeeting()` |
| Trasig state vid page refresh | Rensa URL hash i `restoreState()` catch-blocket |

## Projektstatus
| Fas | Status |
|-----|--------|
| Fas 1 — Google Calendar grundläggande | ✅ Klar |
| Fas 2 — Admin panel + Supabase + Emails | ✅ Klar |
| Microsoft/Outlook Calendar integration | ✅ Klar |
| Mappstruktur refaktorering | ✅ Klar |
| Middleware (admin_required decorator) | ✅ Klar |
| Static-filer omstrukturerade (css/ js/) | ✅ Klar |
| Månadskalender-grid i admin | ✅ Klar |
| Sidebar med klienter (sticky + hamburger) | ✅ Klar |
| Tab-system med hamburger på mobil | ✅ Klar |
| Notification badge för nya bokningar | ✅ Klar |
| Auto-refresh Meeting History (10s) | ✅ Klar |
| Booking status (pending/confirmed/cancelled) | ✅ Klar |
| Google Calendar webhook (auto-status) | ✅ Klar |
| Microsoft Graph webhook (auto-status) | ✅ Klar |
| event_id sparas vid bokning | ✅ Klar |
| Email bilder via GitHub raw-URL | ✅ Klar |
| Responsiv design (mobil) | ✅ Klar |
| State restore vid page refresh (URL hash) | ✅ Klar |
| Bokningar filtrerade per klient | ✅ Klar |
| Bokningsknapp bug fixad | ✅ Klar |
| Google App verifiering (publik) | ⏳ Väntar på Aviv |
| Supabase migration till företagskonto | ⏳ Väntar på Aviv |
| constants.py | ⏳ Pausad |
| tests/-mapp | ⏳ Pausad |
| **Reminders-tab (nästa prioritet)** | 🔜 Nästa steg |
| Fas 3 — Påminnelse-emails (APScheduler) | 🔜 Nästa steg |
| Fas 4 — Gmail ton-inlärning | 🔜 Framtid |
| Avboknings/ombokningsflöde | 🔜 Framtid |
| No-show tracking | 🔜 Framtid |
| CRM-export (CSV/Notion/HubSpot) | 🔜 Framtid |
| Statistik-tab | 🔜 Framtid |

## Nästa steg — Reminders
Bygga påminnelse-funktionalitet i denna ordning:
1. **Supabase** — lägg till `reminder_24h_sent` + `reminder_1h_sent` i `bookings`-tabellen
2. **APScheduler** — bakgrundsjobb i `app.py` som kör var 5:e minut
3. **Email** — påminnelse-mall (`reminder_template.html`) via Resend
4. **Frontend** — Reminders-taben i `admin.html` + `admin.js`
5. **API** — `/admin/reminders` endpoint i `admin_routes.py`

## Deployment
- **Hosting:** Render (https://kalender-integration-1.onrender.com)
- **Start command:** `gunicorn app:app` (Procfile)
- **Port:** Render använder port 10000, `host="0.0.0.0"` krävs i `app.run()`
- **GitHub repo:** https://github.com/Edris9/KALENDER_INTEGRATION
- **Branches:** `main` (production), `dev_frontend` (development)
- Render deployas automatiskt vid push till `main`

## Teamet
- **Aviv Farhi** — Grundare/Chef på Showcase
- **Edris Kohestani** — Utvecklare, onboarding-projekt