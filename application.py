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



#HOME PAGE
@app.route("/")
@login_required
def index():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    if len(user) != 0:
        return render_template("index.html",user=user)
    else:
       return redirect("/login")



#LOGIN PAGE
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
        return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    poll_detail=db.execute("SELECT COUNT(*) FROM poll ").scalar()
    return render_template("user.html",user=user,poll_detail=poll_detail)



#REGISTER USER
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



#LOGOUT
@app.route("/logout")
def logout():

    flash('We hope to see you again!')
    session.clear()
    return redirect("/")



#POLLS
@app.route('/polls', methods=['GET','POST'])
def polls():
    poll_detail=db.execute("SELECT COUNT(*) FROM poll ").scalar()
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    db.execute("INSERT INTO poll (pollid,question, option1,option2,option3,option4,user_id) VALUES(:pollid,:question, :option1,:option2,:option3,:option4,:user_id)",
                  {'pollid':poll_detail+1, 'question': request.form.get("question"), 'option1': request.form.get("option1"), 'option2': request.form.get("option2"),
                   'option3': request.form.get("option3"),'option4': request.form.get("option4"),'user_id':int(session["user_id"])})
    db.commit()

    return redirect("/pollscreated")



#VOTE for created polls
@app.route('/pollscreated',methods=['GET','POST'])
def pollscreated():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    pollid=request.form.get("pollidd")
    if request.method=='POST':
        vote=request.form.get("vote")
        db.execute("INSERT INTO votes (pollid,user_id,option,voted) VALUES(:pollid,:user_id,:option,:voted)",
                    {'pollid':pollid, 'user_id':int(session["user_id"]),'option':vote,'voted':1})
        db.commit()
    check=db.execute("SELECT * FROM votes WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    return render_template("/pollscreated.html",user=user,totalpolls=totalpolls,check=check)

