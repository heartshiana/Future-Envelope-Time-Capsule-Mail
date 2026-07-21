# Future Envelope ✉

A time-capsule mail app. Write a letter — with a photobooth-style **photo strip** and a note to your future self — seal it, and it gets delivered on whatever date you choose. Send it to someone else, or mark it private and mail it to yourself.

## Features

- **Schedule delivery** for any future date/time, with quick presets (1 hour, tomorrow, 1 week, 1 month, 1 year).
- **📸 Photo strip** — attach a handful of photos (a selfie, a photobooth scan, a snapshot of today) and they're arranged into a vertical filmstrip, just like a real photobooth strip, shown alongside your note when the letter arrives.
- **📝 Note to your future self** — the letter body, front and center.
- **Private letters** — send a message straight back to your own inbox instead of someone else's.
- **Encryption at rest** — optionally encrypt the letter body (AES via `cryptography`'s Fernet) until it's decrypted for display.
- **Other file attachments** — up to 8 files total (photos + documents combined), 10 MB each.
- **Pre-send reminders** — get an email a configurable number of hours before a letter goes out.
- **Live countdowns** on the dashboard and letter page.

## How to Use

1. Extract/clone this folder.
2. **Windows:** double-click `run_windows.bat`
   **Mac/Linux:** `bash run_unix.sh`
   (First run creates a virtual environment and installs dependencies; subsequent runs just start the app.)
3. Open **http://127.0.0.1:5000** in your browser and create an account.

The app runs fully offline out of the box — no email server needed. Letters still get "delivered" (their status flips to *sent*) on schedule; without SMTP configured, delivery just isn't actually emailed out, so you can use and test everything locally.

### Optional: real email delivery

Set these environment variables before starting the app to have letters and reminders sent for real:

| Variable        | Purpose                              |
|-----------------|---------------------------------------|
| `SECRET_KEY`    | Session/encryption key — set this to something random and stable in production. |
| `MAIL_SERVER`   | SMTP host, e.g. `smtp.gmail.com`      |
| `MAIL_PORT`     | SMTP port, default `587`              |
| `MAIL_USERNAME` | SMTP account username                 |
| `MAIL_PASSWORD` | SMTP account password / app password  |
| `MAIL_USE_TLS`  | `true` (default) or `false`           |

## Project Structure

```
app.py            # Flask app factory + entry point, background scheduler
routes.py         # All routes (auth, compose, edit, view, profile, attachments, API)
models.py         # User / Email / Attachment SQLAlchemy models
scheduler.py       # Background job: sends due letters + pre-send reminders
encryption.py     # Fernet-based encryption for letter bodies
extensions.py     # Shared Flask-SQLAlchemy / Flask-Login instances
templates/        # Jinja2 templates
static/css, static/js  # Stylesheet + client-side behavior (photo strip, countdowns, etc.)
```

## Author
Heart Shiana Ursua

<img width="1364" height="703" alt="1" src="https://github.com/user-attachments/assets/d4a85ba1-1bbf-486b-8791-beb8e44471da" />
<img width="1365" height="701" alt="2" src="https://github.com/user-attachments/assets/93f09ef9-ff55-4ef4-bd9f-2328a0c1aff9" />
<img width="1365" height="683" alt="3" src="https://github.com/user-attachments/assets/0d26fcb7-51b1-4628-9e47-f8cabf45e225" />
<img width="1365" height="697" alt="4" src="https://github.com/user-attachments/assets/df39bd87-c23f-425f-a0b5-e6722dc25b75" />
