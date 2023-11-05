"""Provides the app package for the Social Insecurity application. The package contains the Flask app and all of the extensions and routes."""

from pathlib import Path
from typing import cast

#import sentry_sdk

from flask import Flask

from app.config import Config
from app.database import SQLite3

from flask_bcrypt import Bcrypt

"""
sentry_sdk.init(
    dsn=YOUR_DSN_URL_HERE,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)
"""

# Instantiate and configure the app
app = Flask(__name__)
app.config.from_object(Config)

# Instantiate the sqlite database extension
sqlite = SQLite3(app, schema="schema.sql")

# Initialize Flask-Bcrypt
flask_bcrypt = Bcrypt(app)

from flask_wtf.csrf import CSRFProtect

from jinja2 import select_autoescape

app.jinja_env.autoescape = select_autoescape(
    enabled_extensions=('html', 'j2'),
    default_for_string=True,
    default=True
)

# CSRF protection using WTForms
csrf = CSRFProtect(app)

# Create the instance and upload folder if they do not exist
with app.app_context():
    instance_path = Path(app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True, exist_ok=True)
    upload_path = instance_path / cast(str, app.config["UPLOADS_FOLDER_PATH"])
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

# Import the routes after the app is configured
from app import routes  # noqa: E402,F401
