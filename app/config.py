"""Provides the configuration for the Social Insecurity application.

This file is used to set the configuration for the application.

Example:
    from flask import Flask
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # Use the configuration
    secret_key = app.config["SECRET_KEY"]
"""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "4a63fa17bc96f499045b9826eab190788305905802ceb5df4439d327963e00ab"
    SQLITE3_DATABASE_PATH = "sqlite3.db"  # Path relative to the Flask instance folder
    UPLOADS_FOLDER_PATH = "uploads"  # Path relative to the Flask instance folder
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}  # Only files with these extentions can be uploaded
    WTF_CSRF_ENABLED = True  # We are using WTForms for protection against CSRF
