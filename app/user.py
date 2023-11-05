"""Provides user login management for the Social Insecurity application.
"""
import flask_login
from flask_login import LoginManager
from app import app, sqlite

login_manager = LoginManager(app)

class User(flask_login.UserMixin):
    pass

""" The user_loader callback is used to reload the user object from the user ID stored in the session.
 It should take the str ID of a user, and return the corresponding user object.
 It should return None (not raise an exception) if the ID is not valid. (In that case, 
 the ID will manually be removed from the session and processing will continue.)
"""
@login_manager.user_loader
def user_loader(user_id):
    """Check if user is logged-in on every page load."""
    get_user = f"""
        SELECT *
        FROM Users
        WHERE id = '{user_id}';
        """
    db_user = sqlite.query(get_user, one=True)

    if db_user is not None and str(db_user["id"]) == str(user_id):
        user = User()
        user.id = str(db_user["id"])
        user.username = str(db_user["username"])
        user.first_name = str(db_user["first_name"])
        user.last_name = str(db_user["last_name"])
        user.full_name = str(db_user["first_name"]) + " " + str(db_user["last_name"])
        return user
    else:
        return None
