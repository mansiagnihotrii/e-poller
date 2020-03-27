import os

from flask import Flask, session, render_template, redirect, request, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import login_required

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    if len(user) != 0:
        return render_template("index.html",user=user)
    else:
       return redirect("/login")

@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("index.html")
    else:
        row = db.execute("SELECT * FROM users WHERE username = :username", {'username': request.form.get("username")}).fetchall()
        if len(row) != 1  or not check_password_hash(row[0]["password"], request.form.get("password")):
            flash("Invalid username/password")
            return render_template("index.html")
        session["user_id"] = row[0]["user_id"]
        user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
        return render_template("user.html",user=user)

@app.route("/register", methods=['GET', 'POST'])
def register():
    session.clear()
    if request.method == "POST":
        if not request.form.get("firstname"):
            return render_template("register.html", message = "FirstName Missing")
        if not request.form.get("lastname"):
            return render_template("register.html", message="LastName Missing")
        if not request.form.get("username"):
            return render_template("register.html", message = "Username Missing")
        if not request.form.get("password"):
            return render_template("register.html", message="Password Missing")
        if request.form.get("password") !=  request.form.get("confirmation"):
            return render_template("register.html", message="Password do not match")
        row = db.execute("SELECT * FROM users WHERE username = :username", {'username': request.form.get("username")}).fetchall()
        if len(row) != 0:
            return render_template("register.html", message = "Username Already Exist")
        else:
            key = db.execute("INSERT INTO users (firstname, lastname, username, password) VALUES(:firstname, :lastname, :username, :password)",
                  {'firstname': request.form.get("firstname"), 'lastname': request.form.get("lastname"), 'username': request.form.get("username").lower(),
                   'password': generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)})
        row = db.execute("SELECT * FROM users WHERE username = :username", {'username': request.form.get("username")}).fetchall()
        session["user_id"] = row[0]["user_id"]
        db.commit()
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():

    flash('We hope to see you again!')
    session.clear()
    return redirect("/")

'''
#CHANGE PASSWORD


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    if request.method == "GET":
        return render_template("password.html", user=user)
    else:
        if not request.form.get("old"):
            return render_template("password.html", message="Missing Old Password", user=user)
        elif not request.form.get("password"):
            return render_template("password.html", message="Missing new password", user=user)
        elif request.form.get("confirmation") != request.form.get("password"):
            return render_template("password.html", message="Password don't Match", user=user)
        rows = db.execute("SELECT * FROM users WHERE user_id = :user_id", {'user_id':session["user_id"]}).fetchall()
        if not check_password_hash(rows[0]["password"], request.form.get("old")):
            return render_template("password.html", message="Wrong old Password", user=user)

        else:
            db.execute("UPDATE users SET password = :hash WHERE user_id = :user_id",
                       {'user_id':session["user_id"],
                       'hash':generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)})
            db.commit()
        flash("Password Changed")
        return redirect(url_for('index'))
        

#POLLS

@app.route('/polls', methods=['GET'])
def polls():
    return render_template('polls.html')

'''
