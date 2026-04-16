"""
models.py — SQLAlchemy models
Imports db from extensions.py (never from app.py) to avoid circular imports.
"""
from extensions import db      # ← same instance app.py uses
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id                  = db.Column(db.Integer, primary_key=True)
    email               = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name        = db.Column(db.String(100), nullable=False)
    password_hash       = db.Column(db.String(255), nullable=False)
    timezone            = db.Column(db.String(64), default='UTC')
    notify_before_hours = db.Column(db.Integer, default=24)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    emails = db.relationship('Email', backref='owner', lazy='dynamic',
                             cascade='all, delete-orphan')

    def set_password(self, plaintext):
        self.password_hash = generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return check_password_hash(self.password_hash, plaintext)

    def __repr__(self):
        return f'<User {self.email}>'


class Email(db.Model):
    __tablename__ = 'emails'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient         = db.Column(db.String(255), nullable=False)
    subject           = db.Column(db.String(500), nullable=False)
    body              = db.Column(db.Text, nullable=False)
    scheduled_at      = db.Column(db.DateTime, nullable=False, index=True)
    sent_at           = db.Column(db.DateTime, nullable=True)
    status            = db.Column(db.String(20), default='scheduled', nullable=False)
    is_private        = db.Column(db.Boolean, default=False)
    is_encrypted      = db.Column(db.Boolean, default=False)
    notification_sent = db.Column(db.Boolean, default=False)
    retry_count       = db.Column(db.Integer, default=0)
    error_message     = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = db.relationship('Attachment', backref='email', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def seconds_until_send(self):
        return (self.scheduled_at - datetime.utcnow()).total_seconds()

    def to_dict(self):
        return {
            'id':           self.id,
            'recipient':    self.recipient,
            'subject':      self.subject,
            'scheduled_at': self.scheduled_at.isoformat(),
            'status':       self.status,
            'is_private':   self.is_private,
            'is_encrypted': self.is_encrypted,
            'seconds_left': self.seconds_until_send(),
            'attachments':  self.attachments.count(),
        }

    def __repr__(self):
        return f'<Email {self.id} to={self.recipient} status={self.status}>'


class Attachment(db.Model):
    __tablename__ = 'attachments'

    id         = db.Column(db.Integer, primary_key=True)
    email_id   = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False, index=True)
    filename   = db.Column(db.String(255), nullable=False)
    mime_type  = db.Column(db.String(100), nullable=False)
    data       = db.Column(db.LargeBinary, nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def size_human(self):
        n = self.size_bytes
        for unit in ('B', 'KB', 'MB', 'GB'):
            if n < 1024:
                return f'{n:.1f} {unit}'
            n /= 1024
        return f'{n:.1f} TB'
