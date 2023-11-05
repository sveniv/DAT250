"""Provides all routes for the Social Insecurity application.

This file contains the routes for the application. It is imported by the app package.
It also contains the SQL queries used for communicating with the database.
"""
import sys
import os

from pathlib import Path

from flask import flash, redirect, render_template, send_from_directory, url_for, request

from app import app, sqlite
from app.forms import CommentsForm, FriendsForm, IndexForm, PostForm, ProfileForm

from app.user import User
import flask_login
from flask_login import login_required

from werkzeug.utils import secure_filename


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    """Provides the index page for the application.

    It reads the composite IndexForm and based on which form was submitted,
    it either logs the user in or registers a new user.

    If no form was submitted, it simply renders the index page.
    """
    index_form = IndexForm()
    login_form = index_form.login
    register_form = index_form.register

    if login_form.validate_on_submit() and login_form.submit.data:
        get_user = f"""
            SELECT *
            FROM Users
            WHERE username = ?;
            """
        user = sqlite.query(get_user, True, (login_form.username.data))

        if user is None or user["password"] != login_form.password.data:
            flash("Sorry, invalid login.", category="warning")
        elif user["password"] == login_form.password.data:
            # Store remember me-cookie
            remember_me = True if request.form.get('login-remember_me') else False
            # Log in the user with flask-login
            lm_user = User()
            lm_user.id = str(user["id"])
            flask_login.login_user(lm_user, remember=remember_me)
                
            return redirect(url_for("stream", username=user["username"]))

    elif register_form.validate_on_submit() and register_form.submit.data:
        # Check if the password and confirm password fields are equal
        if register_form.password.data != register_form.confirm_password.data:
            flash("Please type the same password twice", category="warning")
            return render_template("index.html.j2", title="Welcome", form=index_form)
        
        # Check the password length
        if len(register_form.password.data) < 8:
            flash("The password must be at least 8 characters long.", category="warning")
            return render_template("index.html.j2", title="Welcome", form=index_form)
        # Check if the username is already taken
        get_existing_user = f"""
            SELECT id
            FROM Users
            WHERE username = ?;
            """
        existing_user = sqlite.query(get_existing_user, True, register_form.username.data)
        if existing_user is not None:
            flash("Could not register a user with that username.", category="warning")
            return render_template("index.html.j2", title="Welcome", form=index_form)
        
        insert_user = f"""
            INSERT INTO Users (username, first_name, last_name, password)
            VALUES (?, ?, ?, ?);
            """
        sqlite.query(insert_user, False, register_form.username.data, register_form.first_name.data, register_form.last_name.data, register_form.password.data)
        flash("User successfully created!", category="success")
        return redirect(url_for("index"))

    # Send users that already were authenticated to their stream page
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("stream", username=flask_login.current_user.username))

    return render_template("index.html.j2", title="Welcome", form=index_form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """ Log a user out from flask-login
    """
    flask_login.logout_user()
    flash("Logged out", category="message")
    return redirect(url_for("index"))


@app.route("/stream/<string:username>", methods=["GET", "POST"])
@login_required
def stream(username: str):
    """Provides the stream page for the application.

    If a form was submitted, it reads the form data and inserts a new post into the database.

    Otherwise, it reads the username from the URL and displays all posts from the user and their friends.
    """
    # Check if we are logged in as a valid user (authenticaed)
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for("logout"))
    # Check if we are logged in as the correct user (authorized)
    if flask_login.current_user.username != username:
        return 'Access denied'

    post_form = PostForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)
    
    if post_form.validate_on_submit():
        filename = secure_filename(post_form.image.data.filename)
        
        if post_form.image.data:
            folder_path = str(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"])
            filename_base, filename_ext = os.path.splitext(filename)
            
            if filename_ext[1:].lower() not in app.config["ALLOWED_EXTENSIONS"]:
                flash("Image type must be one of " + ', '.join(app.config["ALLOWED_EXTENSIONS"]), category="warning")
                return redirect(url_for("stream", username=username))
            
            count = ""
            while os.path.exists(folder_path + "/" + filename_base + str(count) + filename_ext):
                if count == "":
                    count = 1
                else:
                    count = count + 1
            filename = filename_base + str(count) + filename_ext
            post_form.image.data.save(folder_path + "/" + filename)

        insert_post = f"""
            INSERT INTO Posts (u_id, content, image, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
            """
        sqlite.query(insert_post, False, user["id"], post_form.content.data, filename)
        return redirect(url_for("stream", username=username))

    # Changed OR to AND between friend subqueries to require two-way friendships for posts to show
    get_posts = f"""
         SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id = p.id) AS cc
         FROM Posts AS p JOIN Users AS u ON u.id = p.u_id
         WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id = ?) AND p.u_id IN (SELECT f_id FROM Friends WHERE u_id = ?) OR p.u_id = ?
         ORDER BY p.creation_time DESC;
        """
    posts = sqlite.query(get_posts, False, user["id"], user["id"], user["id"])
    return render_template("stream.html.j2", title="Stream", username=username, form=post_form, posts=posts)


@app.route("/comments/<string:username>/<int:post_id>", methods=["GET", "POST"])
@login_required
def comments(username: str, post_id: int):
    """Provides the comments page for the application.

    If a form was submitted, it reads the form data and inserts a new comment into the database.

    Otherwise, it reads the username and post id from the URL and displays all comments for the post.
    """
    # Check if we are logged in as a valid user (authenticaed)
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for("logout"))
    # Check if we are logged in as the correct user (authorized)
    if flask_login.current_user.username != username:
        return 'Access denied'
    
    comments_form = CommentsForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if comments_form.validate_on_submit():
        insert_comment = f"""
            INSERT INTO Comments (p_id, u_id, comment, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
            """
        sqlite.query(insert_comment, False, post_id, user["id"], comments_form.comment.data)

    get_post = f"""
        SELECT *
        FROM Posts AS p JOIN Users AS u ON p.u_id = u.id
        WHERE p.id = ?;
        """
    get_comments = f"""
        SELECT DISTINCT *
        FROM Comments AS c JOIN Users AS u ON c.u_id = u.id
        WHERE c.p_id=?
        ORDER BY c.creation_time DESC;
        """
    post = sqlite.query(get_post, False, post_id)
    comments = sqlite.query(get_comments, False, post_id)
    return render_template(
        "comments.html.j2", title="Comments", username=username, form=comments_form, post=post, comments=comments
    )


@app.route("/friends/<string:username>", methods=["GET", "POST"])
@login_required
def friends(username: str):
    """Provides the friends page for the application.

    If a form was submitted, it reads the form data and inserts a new friend into the database.

    Otherwise, it reads the username from the URL and displays all friends of the user.
    """
    # Check if we are logged in as a valid user (authenticaed)
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for("logout"))
    # Check if we are logged in as the correct user (authorized)
    if flask_login.current_user.username != username:
        return 'Access denied'
    
    friends_form = FriendsForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if friends_form.validate_on_submit():
        # Get the user info of the friend we want to add
        get_friend = f"""
            SELECT *
            FROM Users
            WHERE username = ?;
            """
        friend = sqlite.query(get_friend, True, friends_form.username.data)
        # Get our current friends
        get_friends = f"""
            SELECT f_id
            FROM Friends
            WHERE u_id = ?;
            """
        friends = sqlite.query(get_friends, False, user["id"])
        # Get the current friends of the friend we want to add
        friend_friends = None
        if friend:
            get_friend_friends = f"""
                SELECT f_id
                FROM Friends
                WHERE u_id = ?;
                """
            friend_friends = sqlite.query(get_friend_friends, False, friend["id"])

        # When this is true the friend-request-sent message will be shown to the user
        friend_request_sent_msg = False
        
        if friend is None:
            # Don't show that this user doesn't exist
            friend_request_sent_msg = True
        elif friend["id"] == user["id"]:
            flash("You cannot be friends with yourself!", category="warning")
        elif friend["id"] in [friend["f_id"] for friend in friends]:
            if user["id"] in [friend["f_id"] for friend in friend_friends]:
                # Only show this message if the friendship is mutual to avoid revealing the existence of users
                flash("You are already friends with this user!", category="warning")
            else:
                # Don't show that this user exists because the friendship isn’t mutual
                friend_request_sent_msg = True
        else:
            insert_friend = f"""
                INSERT INTO Friends (u_id, f_id)
                VALUES (?, ?);
                """
            sqlite.query(insert_friend, False, user["id"], friend["id"])
            friend_request_sent_msg = True
        
        # Show this message regardless if the user exists or not to avoid exposing the existence of users
        if friend_request_sent_msg == True:
            flash("Friend request sent.", category="success")

    # Only select friends that have a mutual friendship with the user
    get_friends = f"""
        SELECT *
        FROM Friends AS f JOIN Users as u ON f.f_id = u.id
        WHERE f.u_id = ? AND f.f_id != ? AND f.f_id IN (SELECT f.u_id FROM Friends AS f WHERE f.f_id = ?);
        """
    friends = sqlite.query(get_friends, False, user["id"], user["id"], user["id"])
    return render_template("friends.html.j2", title="Friends", username=username, friends=friends, form=friends_form)


@app.route("/profile/<string:username>", methods=["GET", "POST"])
@login_required
def profile(username: str):
    """Provides the profile page for the application.

    If a form was submitted, it reads the form data and updates the user's profile in the database.

    Otherwise, it reads the username from the URL and displays the user's profile.
    """
    profile_form = ProfileForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)
    
    # Check if the user exists
    if user is None:
        return redirect(url_for("profile", username=flask_login.current_user.username))
    
    if username != flask_login.current_user.username:
        # Check if the logged in user are a mutual friend with this user (two-way friendship)
        get_mutual_friends = f"""
            SELECT * FROM 
                (SELECT ua.username, fa.u_id, fa.f_id FROM Users AS ua 
                 JOIN Friends AS fa ON ua.id = fa.u_id WHERE ua.username = ?) AS a 
            JOIN 
                (SELECT ub.username, fb.u_id, fb.f_id FROM Users AS ub 
                 JOIN Friends AS fb ON ub.id = fb.u_id WHERE ub.username = ?) AS b 
            ON a.u_id = b.f_id AND b.u_id = a.f_id
        """
        mutual_friends = sqlite.query(get_mutual_friends, True, username, flask_login.current_user.username)
        if mutual_friends is None:
            return redirect(url_for("profile", username=flask_login.current_user.username, message="You are not authorized to view this profile."))

    if profile_form.validate_on_submit():
        # Check if we are logged as the correct user (authorized)
        if username != flask_login.current_user.username:
            flash("You are not authorized to edit this profile.", category="warning")
            return render_template("profile.html.j2", title="Profile", username=username, user=user, form=profile_form)
        
        update_profile = f"""
            UPDATE Users
            SET education=?, employment=?, music=?, movie=?, nationality=?, birthday=? 
            WHERE username=?;
            """
        sqlite.query(update_profile, False, profile_form.education.data, profile_form.employment.data, profile_form.music.data,  profile_form.movie.data, profile_form.nationality.data, profile_form.birthday.data, username)
        return redirect(url_for("profile", username=username))

    return render_template("profile.html.j2", title="Profile", username=username, user=user, form=profile_form)


@app.route("/uploads/<string:filename>")
@login_required
def uploads(filename):
    """Provides an endpoint for serving uploaded files."""
    user_authorized = False
    # Get the owner of the file
    get_owner = f"""
        SELECT u.username FROM Users AS u 
        WHERE u.id IN (SELECT p.u_id FROM Posts AS p WHERE p.image = ?)
    """
    owner = sqlite.query(get_owner, True, filename)
    if owner:
        # Do the user own the file?
        if flask_login.current_user.username == owner["username"]:
            user_authorized = True
        else:
            # Is the user a mutual friend with the owner of the file?
            get_mutual_friends = f"""
                SELECT * FROM 
                    (SELECT ua.username, fa.u_id, fa.f_id FROM Users AS ua 
                        JOIN Friends AS fa ON ua.id = fa.u_id WHERE ua.username = ?) AS a 
                JOIN 
                    (SELECT ub.username, fb.u_id, fb.f_id FROM Users AS ub 
                        JOIN Friends AS fb ON ub.id = fb.u_id WHERE ub.username = ?) AS b 
                ON a.u_id = b.f_id AND b.u_id = a.f_id
            """
            user_authorized = sqlite.query(get_mutual_friends, True, owner["username"], flask_login.current_user.username)
    if user_authorized:
        return send_from_directory(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"], filename)
    else:
        return 'Access denied'
