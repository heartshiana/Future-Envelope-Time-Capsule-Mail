"""
app.py — Future Envelope entry point.
Creates the Flask app, wires up extensions/blueprints, and (when run directly)
starts the background scheduler that sends due letters and pre-send reminders.
"""
import os

from flask import Flask

from extensions import db, login_manager
from routes import main as main_blueprint

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'future_envelope.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER', '')
    app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_USE_TLS']  = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


def _start_scheduler(flask_app):
    from apscheduler.schedulers.background import BackgroundScheduler
    from scheduler import check_and_send, check_notifications

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(lambda: check_and_send(flask_app), 'interval', seconds=60, id='send_job')
    sched.add_job(lambda: check_notifications(flask_app), 'interval', seconds=60, id='notify_job')
    sched.start()


if __name__ == '__main__':
    # Avoid starting two schedulers under the debug reloader's parent process.
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _start_scheduler(app)
    app.run(debug=True)
