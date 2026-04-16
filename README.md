# ✉ Future Envelope

> *Write to the future. Let time be the courier.*

A full-stack Flask web app to compose emails today and deliver them at any future time.

---

## 🚀 Quick Start (Windows with Anaconda)

> **Important:** Do NOT install into your Anaconda base environment — it has an older SQLAlchemy that conflicts. Use the isolated venv approach below.

### Option A — Double-click (easiest)
1. Extract the zip to a folder (e.g. `D:\Projects\future_envelope`)
2. Double-click **`run_windows.bat`**
3. Open **http://127.0.0.1:5000** in your browser

That's it. The script creates a fresh `venv`, installs dependencies into it (completely isolated from Anaconda), and launches the app.

### Option B — Manual steps in Command Prompt

```cmd
cd "D:\Projects\future_envelope"

REM Create a clean virtual environment (isolated from Anaconda)
python -m venv venv

REM Activate it
venv\Scripts\activate

REM Install dependencies (now isolated — no Anaconda conflicts)
pip install -r requirements.txt

REM Run
python app.py
```

Open **http://127.0.0.1:5000** — the SQLite database is created automatically.

### Mac / Linux

```bash
cd /path/to/future_envelope
bash run_unix.sh
```

---

## ⚙️ Email Configuration (Optional)

Without SMTP credentials the app runs in **dev mode** — emails are marked sent in the database but not actually dispatched. To send real emails, set environment variables before running:

**Windows (Command Prompt):**
```cmd
set MAIL_USERNAME=your@gmail.com
set MAIL_PASSWORD=your_app_password
python app.py
```

**Mac/Linux:**
```bash
export MAIL_USERNAME=your@gmail.com
export MAIL_PASSWORD=your_app_password
python app.py
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords → Generate a 16-character password. Use that instead of your real Gmail password.

---

## 🏗 Project Structure

```
future_envelope/
├── app.py              # Flask factory + dual APScheduler jobs
├── models.py           # User, Email, Attachment (SQLAlchemy)
├── routes.py           # All HTTP routes + JSON API
├── scheduler.py        # Background delivery + notifications
├── encryption.py       # Fernet AES-128 body encryption
├── requirements.txt    # Dependencies (flexible version ranges)
├── run_windows.bat     # One-click Windows launcher
├── run_unix.sh         # One-click Mac/Linux launcher
├── README.md
├── instance/           # SQLite database auto-created here
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── login.html / signup.html
    ├── dashboard.html
    ├── compose.html
    ├── edit.html
    ├── view_email.html
    └── profile.html
```

---

## ✨ Features

| Feature | Details |
|---|---|
| **Auth** | Sign up / login / logout, hashed passwords |
| **Compose** | Subject, body, future delivery datetime |
| **Quick presets** | 1 hour / tomorrow / 1 week / 1 month / 1 year |
| **Private mode** | Letter-to-self (forced to your own address) |
| **Encryption** | AES-128 body encryption at rest (Fernet) |
| **Attachments** | Up to 3 files × 10 MB stored in the database |
| **Notifications** | Pre-send reminder email (configurable: 1h–1 week before) |
| **Dashboard** | Live countdowns, edit/delete before send |
| **Retry logic** | Failed sends retried up to 3× automatically |
| **Profile page** | Timezone, notification prefs, password change |

---

## ⚙️ How Scheduling Works

APScheduler runs two background threads inside the Flask process:

```
Every 60 seconds:
  check_and_send()      → find emails where scheduled_at <= NOW → send via SMTP
  check_notifications() → find emails within reminder window    → send reminder
```

No cron jobs or external workers needed — everything starts with `python app.py`.

---

## 🔒 Security

| Concern | Approach |
|---|---|
| Passwords | PBKDF2-SHA256 via Werkzeug |
| Sessions | Signed with `SECRET_KEY` |
| Ownership | Every DB query filters by `user_id == current_user.id` |
| Body encryption | Fernet (AES-128-CBC + HMAC-SHA256), key derived from SECRET_KEY |
| SMTP credentials | Environment variables only — never hardcoded |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| Flask | Web framework |
| Flask-SQLAlchemy | Database ORM |
| Flask-Login | Session management |
| Werkzeug | Password hashing, WSGI utilities |
| APScheduler | Background scheduler |
| SQLAlchemy | Database layer |
| cryptography | Fernet encryption for email bodies |

---

## 🐛 Troubleshooting

**`TypeError: Can't replace canonical symbol`**  
→ SQLAlchemy version conflict with Anaconda. Use `venv` as described above — do NOT install into the base conda environment.

**`ModuleNotFoundError: No module named 'flask'`**  
→ Your venv is not activated. Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux) first.

**Emails not sending**  
→ Check that `MAIL_USERNAME` and `MAIL_PASSWORD` are set. For Gmail, use an App Password (not your real password). Verify 2FA is enabled on your Google account.
