"""
routes.py — All routes on a Blueprint.
Imports db from extensions.py and models directly (no circular dependency).
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, abort, send_file, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import io

from extensions import db
from models import User, Email, Attachment

main = Blueprint('main', __name__)

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS      = 3

COMMON_TIMEZONES = [
    'UTC','US/Eastern','US/Central','US/Mountain','US/Pacific',
    'Europe/London','Europe/Paris','Europe/Berlin','Asia/Tokyo',
    'Asia/Shanghai','Asia/Kolkata','Asia/Manila','Australia/Sydney',
    'America/Sao_Paulo','Africa/Nairobi',
]


# ── Root ──────────────────────────────────────────────────
@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


# ── Auth ──────────────────────────────────────────────────
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email_addr = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '')
        user = User.query.filter_by(email=email_addr).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember') == 'on')
            return redirect(request.args.get('next') or url_for('main.dashboard'))
        flash('Invalid email or password.', 'error')

    return render_template('login.html')


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        email_addr = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '')
        confirm    = request.form.get('confirm_password', '')

        errors = []
        if not name:                                          errors.append('Display name is required.')
        if not email_addr or '@' not in email_addr:           errors.append('A valid email is required.')
        if len(password) < 6:                                 errors.append('Password must be at least 6 characters.')
        if password != confirm:                               errors.append('Passwords do not match.')
        if User.query.filter_by(email=email_addr).first():   errors.append('Email already registered.')

        if errors:
            for e in errors: flash(e, 'error')
        else:
            user = User(email=email_addr, display_name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Welcome to Future Envelope! ✉', 'success')
            return redirect(url_for('main.dashboard'))

    return render_template('signup.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


# ── Dashboard ─────────────────────────────────────────────
@main.route('/dashboard')
@login_required
def dashboard():
    scheduled = (current_user.emails
                 .filter(Email.status.in_(['scheduled', 'notified']))
                 .order_by(Email.scheduled_at.asc()).all())
    sent = (current_user.emails
            .filter(Email.status.in_(['sent', 'failed']))
            .order_by(Email.sent_at.desc()).limit(50).all())
    return render_template('dashboard.html', scheduled=scheduled,
                           sent=sent, now=datetime.utcnow())


# ── Compose ───────────────────────────────────────────────
@main.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    if request.method == 'POST':
        recipient     = request.form.get('recipient', '').strip()
        subject       = request.form.get('subject', '').strip()
        body          = request.form.get('body', '').strip()
        scheduled_str = request.form.get('scheduled_at', '').strip()
        is_private    = request.form.get('is_private') == 'on'
        is_encrypted  = request.form.get('is_encrypted') == 'on'

        if is_private:
            recipient = current_user.email

        if is_encrypted and body:
            try:
                from encryption import encrypt_body
                body = encrypt_body(current_app._get_current_object(), body)
            except RuntimeError as e:
                flash(str(e), 'error')
                return render_template('compose.html', prefill=request.form, now=datetime.utcnow())

        errors = []
        if not is_private and (not recipient or '@' not in recipient):
            errors.append('A valid recipient email is required.')
        if not subject: errors.append('Subject is required.')
        if not body:    errors.append('Message body is required.')

        scheduled_dt = None
        if not scheduled_str:
            errors.append('Please choose a delivery date and time.')
        else:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_str)
                if scheduled_dt <= datetime.utcnow():
                    errors.append('Delivery time must be in the future.')
            except ValueError:
                errors.append('Invalid date/time format.')

        if errors:
            for e in errors: flash(e, 'error')
            return render_template('compose.html', prefill=request.form, now=datetime.utcnow())

        email = Email(
            user_id=current_user.id, recipient=recipient, subject=subject,
            body=body, scheduled_at=scheduled_dt,
            is_private=is_private, is_encrypted=is_encrypted
        )
        db.session.add(email)
        db.session.flush()

        for f in request.files.getlist('attachments'):
            if not f or not f.filename: continue
            data = f.read()
            if len(data) > MAX_ATTACHMENT_BYTES:
                flash(f'{f.filename} exceeds 10 MB limit.', 'error'); continue
            if email.attachments.count() >= MAX_ATTACHMENTS:
                flash(f'Max {MAX_ATTACHMENTS} attachments allowed.', 'error'); break
            db.session.add(Attachment(
                email_id=email.id, filename=f.filename,
                mime_type=f.mimetype or 'application/octet-stream',
                data=data, size_bytes=len(data)
            ))

        db.session.commit()
        flash('✉ Your message has been sealed and scheduled!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('compose.html', prefill={}, now=datetime.utcnow())


# ── Edit ──────────────────────────────────────────────────
@main.route('/edit/<int:email_id>', methods=['GET', 'POST'])
@login_required
def edit_email(email_id):
    email = Email.query.get_or_404(email_id)
    if email.user_id != current_user.id: abort(403)
    if email.status not in ('scheduled', 'notified'):
        flash('Only pending emails can be edited.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email.recipient  = request.form.get('recipient', email.recipient).strip()
        email.subject    = request.form.get('subject', email.subject).strip()
        email.body       = request.form.get('body', email.body).strip()
        email.is_private = request.form.get('is_private') == 'on'
        if email.is_private:
            email.recipient = current_user.email

        s = request.form.get('scheduled_at', '').strip()
        if s:
            try:
                dt = datetime.fromisoformat(s)
                if dt <= datetime.utcnow():
                    flash('Delivery time must be in the future.', 'error')
                else:
                    email.scheduled_at = dt
            except ValueError:
                flash('Invalid date/time format.', 'error')

        db.session.commit()
        flash('✏️ Email updated.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit.html', email=email)


# ── Delete ────────────────────────────────────────────────
@main.route('/delete/<int:email_id>', methods=['POST'])
@login_required
def delete_email(email_id):
    email = Email.query.get_or_404(email_id)
    if email.user_id != current_user.id: abort(403)
    if email.status not in ('scheduled', 'notified'):
        flash('Only pending emails can be deleted.', 'error')
    else:
        db.session.delete(email)
        db.session.commit()
        flash('🗑 Email deleted.', 'info')
    return redirect(url_for('main.dashboard'))


# ── View ──────────────────────────────────────────────────
@main.route('/email/<int:email_id>')
@login_required
def view_email(email_id):
    email = Email.query.get_or_404(email_id)
    if email.user_id != current_user.id: abort(403)

    display_body = email.body
    if email.is_encrypted:
        try:
            from encryption import decrypt_body
            display_body = decrypt_body(current_app._get_current_object(), email.body)
        except Exception:
            display_body = '[Could not decrypt message — check your SECRET_KEY]'

    return render_template('view_email.html', email=email,
                           display_body=display_body, now=datetime.utcnow())


# ── Profile ───────────────────────────────────────────────
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('display_name', '').strip()
        if name: current_user.display_name = name

        tz = request.form.get('timezone', 'UTC')
        if tz in COMMON_TIMEZONES: current_user.timezone = tz

        try:
            current_user.notify_before_hours = max(0, min(
                int(request.form.get('notify_before_hours', 24)), 720))
        except ValueError:
            pass

        new_pass = request.form.get('new_password', '')
        if new_pass:
            if not current_user.check_password(request.form.get('current_password', '')):
                flash('Current password is incorrect.', 'error')
            elif len(new_pass) < 6:
                flash('New password must be at least 6 characters.', 'error')
            elif new_pass != request.form.get('confirm_password', ''):
                flash('Passwords do not match.', 'error')
            else:
                current_user.set_password(new_pass)
                flash('Password updated.', 'success')

        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('main.profile'))

    stats = {
        'total':     current_user.emails.count(),
        'scheduled': current_user.emails.filter(Email.status.in_(['scheduled','notified'])).count(),
        'sent':      current_user.emails.filter_by(status='sent').count(),
        'failed':    current_user.emails.filter_by(status='failed').count(),
    }
    return render_template('profile.html', timezones=COMMON_TIMEZONES, stats=stats)


# ── Attachments ───────────────────────────────────────────
@main.route('/attachment/<int:att_id>')
@login_required
def download_attachment(att_id):
    att = Attachment.query.get_or_404(att_id)
    if att.email.user_id != current_user.id: abort(403)
    return send_file(io.BytesIO(att.data), download_name=att.filename,
                     as_attachment=True, mimetype=att.mime_type)


@main.route('/delete-attachment/<int:att_id>', methods=['POST'])
@login_required
def delete_attachment(att_id):
    att = Attachment.query.get_or_404(att_id)
    if att.email.user_id != current_user.id: abort(403)
    email_id = att.email_id
    db.session.delete(att)
    db.session.commit()
    flash('Attachment removed.', 'info')
    return redirect(url_for('main.edit_email', email_id=email_id))


# ── JSON API ──────────────────────────────────────────────
@main.route('/api/emails')
@login_required
def api_emails():
    scheduled = current_user.emails.filter(
        Email.status.in_(['scheduled', 'notified'])).all()
    return jsonify([e.to_dict() for e in scheduled])
