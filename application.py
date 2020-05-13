import os

from flask import Flask, session, render_template, redirect, request, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
#jinja_env = Environment(extensions=['jinja2.ext.loopcontrols'])
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


#FETCH USER_ID
def userid(user_id):
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': user_id}).fetchall()
    return user


#FUNCTION TO VOTE FOR POLL
def voteforpoll(pollid,option):
    db.execute("INSERT INTO votes (pollid,user_id,option) VALUES(:pollid,:user_id,:option)",
                        {'pollid':pollid, 'user_id':int(session["user_id"]), 'option':option})
    db.commit()


#CHECK WHETHER POLL IS ACTIVE OR NOT
def checkpoll():
    listt=db.execute("SELECT DISTINCT pollid FROM votes WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    check=[x[0] for x in listt]
    return check


#RETURN POLL RESULT
def result(pollid):
    #FETCH TOTAL VOTES RECIEVED BY EACH OPTION FOR GIVEN POLL
    list1=db.execute("SELECT COUNT(option)AS result FROM votes WHERE pollid=:pollid GROUP BY option ORDER BY option ASC",{'pollid':pollid}).fetchall()
    #FETCH TOTAL VOTES RECEIVED BY GIVEN POLL
    list2=db.execute("SELECT COUNT(option)AS total_votes FROM votes WHERE pollid=:pollid ",{'pollid':pollid}).fetchall()
    print_result=[x[0] for x in list1]
    print_totalvotes=[x[0] for x in list2]
    list3=[]
    #CALCULATE VOTES PERCENTAGE
    for x in print_result:
        ans=int((x/print_totalvotes[0])*100)
        list3.append(ans)
    #IF NO VOTE IS GIVEN TO ANY OPTION
    for x in range(0,2):
        list3.append(0)
    return list3



#HOME PAGE
@app.route("/")
@login_required
def index():
    session.clear()
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
        session["firstname"]=row[0]["firstname"]
        return redirect("/dashboard")

#USER'S DASHBOARD
@app.route("/dashboard")
def dashboard():
    poll_total=db.execute("SELECT COUNT(*) FROM poll ").scalar()
    poll_total_user=db.execute("SELECT COUNT(*)FROM poll WHERE user_id=:userid",{'userid':int(session["user_id"])}).scalar()
    poll_ongoing=db.execute("SELECT COUNT(*) FROM poll WHERE ended =0 AND user_id=:userid",{'userid':int(session["user_id"])}).scalar()
    poll_ended=poll_total_user-poll_ongoing
    return render_template("user.html",user=session["firstname"],poll_total=poll_total,poll_total_user=poll_total_user,poll_ongoing=poll_ongoing,poll_ended=poll_ended)



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
        session["firstname"]=row[0]["firstname"]
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



#CREATE POLL
@app.route('/polls', methods=['GET','POST'])
def polls():
    poll_detail=db.execute("SELECT COUNT(*) FROM poll ").scalar()

    db.execute("INSERT INTO poll (pollid,question, option1,option2,option3,option4,user_id) VALUES(:pollid,:question, :option1,:option2,:option3,:option4,:user_id)",
                  {'pollid':poll_detail+1, 'question': request.form.get("question"), 'option1': request.form.get("option1"), 'option2': request.form.get("option2"),
                   'option3': request.form.get("option3"),'option4': request.form.get("option4"),'user_id':int(session["user_id"])})
    db.commit()

    return redirect("/pollscreated/ongoing")



#CHECK OUT CREATED POLLS
@app.route('/pollscreated/ongoing',methods=['GET','POST'])
def ongoingpolls():
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended =0 ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    pollid=request.form.get("pollid")
    check=checkpoll()
    if request.method=='POST':
        if 'end' in request.form:
            db.execute("UPDATE poll SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.commit()
            return redirect("/pollscreated/ongoing")
        elif 'voteforpoll' in request.form:
            vote=request.form.get("vote")
            voteforpoll(pollid,vote)
        elif 'result' in request.form:
            print_result=result(pollid)
            return render_template("/pollscreated.html",user=session["firstname"],totalpolls=totalpolls,check=check,print_result=print_result)
    return render_template("/pollscreated.html",user=session["firstname"],totalpolls=totalpolls,check=check)

#CHECK OUT ENDED POLLS
@app.route('/pollscreated/ended',methods=['GET','POST'])
def endedpolls():
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended =1 ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    if request.method=='POST':
        pollid=request.form.get("pollid")
        print_result=result(pollid)
        return render_template("/pollended.html",user=session["firstname"],totalpolls=totalpolls,print_result=print_result)
    return render_template("/pollended.html",user=session["firstname"],totalpolls=totalpolls)


#VOTE FOR OTHER POLLS
@app.route('/polltovote',methods=['GET','POST'])
def polltovote():
    if request.method == 'GET':
        return redirect("/dashboard")
    else:
        pollid=request.form.get("pollid")
        totalpolls = db.execute("SELECT * FROM poll WHERE pollid=:pollid",{'pollid':pollid}).fetchall()
        if totalpolls[0]["user_id"]!= int(session["user_id"]):
            hide=0
        else:
            hide=1
        vote=request.form.get("vote")
        if totalpolls != 0:
            if 'voteforpoll' in request.form:
                voteforpoll(pollid,vote)
            elif 'result' in request.form:
                print_result=result(pollid)
                return render_template("/polltovote.html",user=session["firstname"],totalpolls=totalpolls,print_result=print_result)
            check=checkpoll()
            return render_template("polltovote.html", totalpolls=totalpolls, user=session["firstname"],hide=hide,check=check,end=int(totalpolls[0]["ended"]))
        else:
            return render_template("polltovote.html",message="Not found",user=session["firstname"],hide=hide)

