from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime




# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///recovery.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Go to home page
@app.route("/")
def index():
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")
    return render_template("index.html", posts=posts)

# Go to Forum
@app.route("/forum")
def forum():
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")

    return render_template("forum.html",  posts=posts)

# Add new post
@app.route("/post", methods=["POST"])
def post():

    post = request.form.get("post")
    temp = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
    username = temp[0]["username"]
    date = datetime.datetime.now()
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")

    if post :
        temp = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
        username = temp[0]["username"]
        db.execute("INSERT INTO posts (user_id, user, post, date) VALUES(?, ?, ?, ?)", session["user_id"], username, post, date)
        posts = db.execute("SELECT * FROM posts ORDER BY date DESC")

        return render_template("forum.html", posts=posts)

    if not request.form.get("post"):
        return render_template("forum.html", posts=posts, post_error="field is empty")

# Search existing posts
@app.route("/search", methods=["POST"])
def search():
    search = request.form.get("search")
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")

    if request.method == "POST":

        if search:
            posts = db.execute("SELECT * FROM posts WHERE post LIKE ? ORDER BY date DESC", '%' + search + '%')

            return render_template("forum.html", posts=posts)

        else:
            return render_template("forum.html", posts=posts, search_error="field is empty")

# Show thread
@app.route("/thread", methods=["GET", "POST"])
def thread():
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")
    replies = db.execute("SELECT * FROM replies ORDER BY date DESC")

    if request.method == "POST":

        id = request.form.get("id")

        if id:
            posts = db.execute("SELECT * FROM posts WHERE id = ?", id)
            replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY date DESC", id)
            return render_template("thread.html", posts=posts, replies=replies)

    else:
        return render_template("forum.html", posts=posts)


# Delete a post
@app.route("/delete", methods=["POST"])
def delete():
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")
    id = request.form.get("id")

    db.execute("DELETE FROM posts WHERE id = ?", id)
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")

    return render_template("forum.html", posts=posts)


# Reply to a post
@app.route("/reply", methods=["POST"])
def reply():
    date = datetime.datetime.now()
    id = request.form.get("id")
    temp = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
    user = temp[0]["username"]
    reply = request.form.get("reply")
    posts = db.execute("SELECT * FROM posts WHERE id = ?", id)
    replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY date DESC", id)

    if request.form.get("reply"):
        db.execute("INSERT INTO replies (post_id, user_id, user, reply, date) VALUES(?, ?, ?, ?, ?)", id, session["user_id"], user, reply, date)
        posts = db.execute("SELECT * FROM posts WHERE id = ?", id)
        replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY date DESC", id)

        return render_template("thread.html", posts=posts, replies=replies)

    else:
        return render_template("thread.html", posts=posts, replies=replies, apple="field is empty")


# Delete a reply
@app.route("/unreply", methods=["POST"])
def unreply():
    reply_id = request.form.get("reply_id")
    post_id = request.form.get("post_id")
    posts = db.execute("SELECT * FROM posts WHERE id = ?", post_id)
    replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY date DESC", post_id)

    db.execute("DELETE FROM replies WHERE id = ?", reply_id)
    replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY date DESC", post_id)

    return render_template("thread.html", posts=posts, replies=replies)




# Go to About page
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")
    # Forget any user_id
    session.clear()
    #error = request.form.get("error")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error="You must enter a username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="You must enter a password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return render_template("login.html", error="Incorrect username")

        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error="Incorrect password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("forum.html", posts=posts)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    posts = db.execute("SELECT * FROM posts ORDER BY date DESC")
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username field not blank
        if not request.form.get("username"):
            return render_template("register.html", error="You must enter a username")

        # Ensure username doesn't already exist
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username is not taken
        if len(rows) > 0:
            return render_template("register.html", error="Username taken")

        # Ensure password field not blank
        if not request.form.get("password"):
            return render_template("register.html", error="You must enter a password")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("register.html", error="You must re-type password")

        # Ensure password and confirmation match
        elif confirmation != password:
            return render_template("register.html", error="Password cofirmation does not match")

        hash = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        # remember which user has logged in
        session["user_id"] = username

        return render_template("forum.html", posts=posts)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """change password"""
    user_id = session["user_id"]
    temp = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
    username = temp[0]["username"]
    newpassword = request.form.get("newpassword")
    newconfirmation = request.form.get("newconfirmation")
    user_posts = db.execute("SELECT * FROM posts WHERE user = ? ORDER BY date DESC", username)
    upper_user = username.upper()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure password field not blank
        if not request.form.get("newpassword"):
            return render_template("profile.html", user_posts=user_posts, error="You must enter a new password")

        # Ensure confirmation was submitted
        elif not request.form.get("newconfirmation"):
            return render_template("profile.html", user_posts=user_posts, error="You must re-type password")

        # Ensure password and confirmation match
        elif newconfirmation != newpassword:
            return render_template("register.html", user_posts=user_posts, error="Password cofirmation does not match")

        newhash = generate_password_hash(newpassword)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", newhash, user_id)

        return render_template("profile.html", username=upper_user, user_posts=user_posts)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("profile.html", username=upper_user, user_posts=user_posts)

