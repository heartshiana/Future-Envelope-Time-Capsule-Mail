"""
scheduler.py — Background email delivery (v2)
Imports db and models lazily inside app context to avoid circular imports.
"""
import smtplib, ssl, logging
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base      import MIMEBase
from email                import encoders
from datetime             import datetime, timedelta

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def check_and_send(app):
    with app.app_context():
        from models import Email
        from extensions import db
        now = datetime.utcnow()
        due = Email.query.filter(
            Email.status.in_(['scheduled', 'notified']),
            Email.scheduled_at <= now,
            Email.retry_count < MAX_RETRIES
        ).all()

        for email in due:
            ok, err = _send_email(app, email)
            if ok:
                email.status  = 'sent'
                email.sent_at = datetime.utcnow()
                logger.info(f"✅ #{email.id} sent to {email.recipient}")
            else:
                email.retry_count  += 1
                email.error_message = str(err)
                if email.retry_count >= MAX_RETRIES:
                    email.status = 'failed'
                    logger.error(f"❌ #{email.id} failed: {err}")
        db.session.commit()


def check_notifications(app):
    with app.app_context():
        from models import Email, User
        from extensions import db
        now = datetime.utcnow()
        candidates = (Email.query.join(User, Email.user_id == User.id)
                      .filter(Email.status == 'scheduled',
                              Email.notification_sent == False,
                              User.notify_before_hours > 0).all())
        for email in candidates:
            user = email.owner
            if email.scheduled_at <= now + timedelta(hours=user.notify_before_hours):
                ok, err = _send_notification(app, email, user)
                if ok:
                    email.notification_sent = True
                    email.status = 'notified'
        db.session.commit()


def _send_email(app, rec):
    cfg      = app.config
    username = cfg.get('MAIL_USERNAME', '')
    password = cfg.get('MAIL_PASSWORD', '')
    if not username or not password:
        return True, None  # dev mode

    body = rec.body
    if rec.is_encrypted:
        try:
            from encryption import decrypt_body
            body = decrypt_body(app, body)
        except Exception as e:
            return False, f"Decrypt error: {e}"

    atts = list(rec.attachments)
    if atts:
        msg      = MIMEMultipart('mixed')
        alt_part = MIMEMultipart('alternative')
    else:
        msg      = MIMEMultipart('alternative')
        alt_part = msg

    msg['Subject'] = rec.subject
    msg['From']    = username
    msg['To']      = rec.recipient
    alt_part.attach(MIMEText(body, 'plain', 'utf-8'))
    alt_part.attach(MIMEText(_html_wrap(rec, body), 'html', 'utf-8'))

    if atts:
        msg.attach(alt_part)
        for a in atts:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(a.data)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', 'attachment', filename=a.filename)
            msg.attach(p)

    return _smtp(app, username, rec.recipient, msg)


def _send_notification(app, rec, user):
    cfg      = app.config
    username = cfg.get('MAIL_USERNAME', '')
    password = cfg.get('MAIL_PASSWORD', '')
    if not username or not password:
        return True, None

    delta    = rec.scheduled_at - datetime.utcnow()
    hrs      = int(delta.total_seconds() / 3600)
    mins     = int((delta.total_seconds() % 3600) / 60)
    time_str = f"{hrs}h {mins}m" if hrs else f"{mins} minutes"
    when     = rec.scheduled_at.strftime('%B %d, %Y at %H:%M UTC')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'⏰ Reminder: "{rec.subject}" sends in {time_str}'
    msg['From']    = username
    msg['To']      = user.email
    msg.attach(MIMEText(f'Your email "{rec.subject}" sends in {time_str} ({when}).', 'plain'))
    return _smtp(app, username, user.email, msg)


def _smtp(app, sender, recipient, msg):
    cfg = app.config
    try:
        ctx = ssl.create_default_context()
        if cfg.get('MAIL_USE_TLS', True):
            with smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT'], timeout=30) as s:
                s.ehlo(); s.starttls(context=ctx)
                s.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
                s.sendmail(sender, recipient, msg.as_string())
        else:
            with smtplib.SMTP_SSL(cfg['MAIL_SERVER'], cfg['MAIL_PORT'], context=ctx, timeout=30) as s:
                s.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
                s.sendmail(sender, recipient, msg.as_string())
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Auth error: {e}"
    except Exception as e:
        return False, str(e)


def _html_wrap(rec, body_text):
    body_html = body_text.replace('\n', '<br>')
    when      = rec.scheduled_at.strftime('%B %d, %Y at %H:%M UTC')
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f9f4ec;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px;">
<table width="600" cellpadding="0" cellspacing="0"
       style="background:#fff;border:1px solid #e0d5c5;border-radius:8px;overflow:hidden;">
  <tr><td style="background:#2c1810;padding:24px 32px;color:#f9f4ec;text-align:center;">
    <p style="margin:0;font-size:24px;letter-spacing:2px;">✉ FUTURE ENVELOPE</p>
    <p style="margin:4px 0 0;font-size:12px;opacity:0.7;">Delivered from your past self</p>
  </td></tr>
  <tr><td style="padding:32px;">
    <p style="margin:0 0 24px;color:#8a7560;font-size:13px;font-style:italic;">
      Originally scheduled for {when}</p>
    <div style="font-size:16px;line-height:1.7;color:#3a2e1e;">{body_html}</div>
  </td></tr>
  <tr><td style="background:#f9f4ec;padding:16px 32px;text-align:center;border-top:1px solid #e0d5c5;">
    <p style="margin:0;font-size:12px;color:#a09080;">
      Sent via Future Envelope · Time-capsule messages for the soul</p>
  </td></tr>
</table></td></tr></table></body></html>"""
