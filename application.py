import os

from flask import Flask, session, render_template, redirect, request, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required


epoller= Flask(__name__)


# CHECK FOR ENVIRONMENT VARIABLES
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# CONFIGURE SESSION TO USE FILESYSTEM
epoller.config["SESSION_PERMANENT"] = False
epoller.config["SESSION_TYPE"] = "filesystem"
Session(epoller)

# SET UP DATABASE
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#FUNCTION TO INSERT VOTE INTO DATABASE
def voteforpoll(pollid,option):
    db.execute("INSERT INTO votes (pollid,user_id,option) VALUES(:pollid,:user_id,:option)",
                        {'pollid':pollid, 'user_id':int(session["user_id"]), 'option':option})
    db.commit()


#FUNCTION TO CHECK WHETHER USER ALREADY VOTED OR NOT
def checkpoll():
    listt=db.execute("SELECT DISTINCT pollid FROM votes WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    check=[x[0] for x in listt]
    return check


#FUNCTION TO RETURN RESULT OF A POLL
def result(pollid):
    result_dict = {'1':0 , '2':0 , '3':0 , '4':0}
    #LIST1 CONTAINS VOTES EACH OPTION RECEIVED
    list1=db.execute("SELECT COUNT(option) AS result, option FROM votes WHERE pollid=:pollid GROUP BY option ORDER BY option ASC",{'pollid':pollid}).fetchall()
    #LIST2 CONTAINS TOTAL NUMBER OF VOTES SUBMITTED
    list2=db.execute("SELECT COUNT(option)AS total_votes FROM votes WHERE pollid=:pollid ",{'pollid':pollid}).fetchall()
    #CALCULATE PERCENTAGE OF VOTES EACH OPTION RECEIVED AND STORE IN THE RESULT
    for item in range(len(list1)):
        result_dict[list1[item]["option"]] = round((list1[item]["result"]/list2[0]["total_votes"])*100,2)
    return list(result_dict.values())


#HOME PAGE
@epoller.route("/")
@login_required
def index():
    user = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    if len(user) != 0:
        return render_template("index.html",user=user)
    else:
       return redirect("/login")



#LOGIN PAGE
@epoller.route("/login", methods=['GET', 'POST'])
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


#DASHBOARD
@epoller.route("/dashboard")
@login_required
def dashboard():
    poll_total=db.execute("SELECT COUNT(*) FROM poll ").scalar() #TOTAL POLLS CREATED
    poll_total_user=db.execute("SELECT COUNT(*)FROM poll WHERE user_id=:userid",{'userid':int(session["user_id"])}).scalar() #TOTAL POLLS CREATED BY CURRENT USER
    poll_ongoing=db.execute("SELECT COUNT(*) FROM poll WHERE ended =0 AND user_id=:userid",{'userid':int(session["user_id"])}).scalar() #TOTAL ONGOING POLLS
    poll_ended=poll_total_user-poll_ongoing #TOTAL ENDED POLLS
    return render_template("user.html",user=session["firstname"],poll_total=poll_total,poll_total_user=poll_total_user,poll_ongoing=poll_ongoing,poll_ended=poll_ended)



#REGISTER USER
@epoller.route("/register", methods=['GET', 'POST'])
def register():
    session.clear()
    if request.method == "POST":
        if not request.form.get("firstname"):
            return render_template("register.html", message = "FirstName Missing")
        if not request.form.get("lastname"):
            return render_template("register.html", message="LastName Missing")
        if not request.form.get("username"):
            return render_template("register.html", message = "Username Missing")
        if not request.form.get("email"):
            return render_template("register.html", message="Email Missing")
        if not request.form.get("aadhar"):
            return render_template("register.html", message="Aadhar ID Missing")
        if not request.form.get("password"):
            return render_template("register.html", message="Password Missing")
        if request.form.get("password") !=  request.form.get("confirmation"):
            return render_template("register.html", message="Password do not match")
        row = db.execute("SELECT * FROM users WHERE username = :username", {'username': request.form.get("username")}).fetchall()
        if len(row) != 0:
            return render_template("register.html", message = "Username Already Exist")
        else:
            key = db.execute("INSERT INTO users (firstname, lastname, username, email,password) VALUES(:firstname, :lastname, :username, :email, :password)",
                  {'firstname': request.form.get("firstname"), 'lastname': request.form.get("lastname"), 'username': request.form.get("username"), 'email':request.form.get("email"),
                   'password': generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)})
        row = db.execute("SELECT * FROM users WHERE username = :username", {'username': request.form.get("username")}).fetchall()
        session["user_id"] = row[0]["user_id"]
        session["firstname"]=row[0]["firstname"]
        db.commit()
        return redirect("/")
    else:
        return render_template("register.html")



#LOGOUT
@epoller.route("/logout")
@login_required
def logout():
    flash('We hope to see you again!')
    session.clear()
    return redirect("/")


#PROFILE
@epoller.route("/profile",methods=['GET','POST'])
@login_required
def profile():
    details = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    if request.method == "GET":
        return render_template("profile.html",details = details,user=session["firstname"])
    username = request.form.get("username")
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")
    
    if not username:
        username = details[0]["username"]
    if not firstname:
        firstname = details[0]["firstname"]
    if not lastname:
        lastname = details[0]["lastname"]
    if not email:
        email = details[0]["email"]   
    if request.form.get("oldpassword"):
        if not check_password_hash(details[0]["password"], request.form.get("oldpassword")):
            return render_template('profile.html',message = "Old password doesn't match",user=session["firstname"],color="danger",details=details)
        if not request.form.get("newpassword") == request.form.get("renewpassword"):
            return render_template('profile.html',message = "New passwords doesn't match",user=session["firstname"],color="danger",details=details)
        db.execute("UPDATE users SET password =:password",{'password': generate_password_hash(request.form.get("newpassword"), method='pbkdf2:sha256', salt_length=8)})
        return render_template('profile.html',message = "Password Updated Successfully !",user=session["firstname"],color="success",details=details)
                  
    db.execute("UPDATE users SET username =:username,firstname=:firstname, lastname=:lastname, email=:email",
                  {'username':username,'firstname':firstname,'lastname':lastname,'email':email})
    db.commit()
    details = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    return render_template('profile.html',message = "Profile updated Succesfully",details = details,user=session["firstname"],color="success")              




#POLLS
@epoller.route('/createpoll', methods=['GET','POST'])
@login_required
def polls():
    poll_total=db.execute("SELECT COUNT(*) FROM poll ").scalar() #TOTAL POLLS CREATED
    if request.method=="POST":
        poll_detail=db.execute("SELECT COUNT(*) FROM poll ").scalar()
        db.execute("INSERT INTO poll (pollid,question,user_id) VALUES(:pollid,:question, :user_id)",
                      {'pollid':poll_detail+1, 'question': request.form.get("question"), 'user_id':int(session["user_id"])})
                  
        temp = request.form.getlist("option")
        for name in temp:   
          db.execute("INSERT INTO option (pollid,name,user_id) VALUES(:pollid,:name,:user_id)",
                      {'pollid':poll_detail+1, 'name': name,'user_id':int(session["user_id"])})         
        db.commit()
        return redirect("/pollscreated/ongoing")
    return render_template("create_poll.html",poll_total=poll_total)

#CREATED POLLS
@epoller.route('/pollscreated/ongoing',methods=['GET','POST'])
@login_required
def ongoingpolls():
    type = "created"
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended=0  ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    options = db.execute("SELECT * FROM option WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    pollid=request.form.get("pollid")
    
    check=checkpoll()
    if request.method=='POST':
        if 'end' in request.form:
            db.execute("UPDATE poll SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.commit()
            return redirect("/pollscreated/ended")
        elif 'voteforpoll' in request.form:
            vote=request.form.get("vote")
            voteforpoll(pollid,vote)
        elif 'result' in request.form:
            print_result=result(pollid)
            return render_template("/poll.html",user=session["firstname"],totalpolls=totalpolls,check=check,print_result=print_result,options=options,type=type)
    return render_template("/poll.html",user=session["firstname"],totalpolls=totalpolls,check=check,options=options,type=type)



#ENDED POLLS
@epoller.route('/pollscreated/ended',methods=['GET','POST'])
@login_required
def endedpolls():
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended =1 ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    options = db.execute("SELECT * FROM option WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    if request.method=='POST':
        pollid=request.form.get("pollid")
        print_result=result(pollid)
        return render_template("/pollended.html",user=session["firstname"],totalpolls=totalpolls,print_result=print_result,options=options)
    return render_template("/pollended.html",user=session["firstname"],totalpolls=totalpolls,options=options)


#VOTE FOR OTHER POLLS
@epoller.route('/polltovote',methods=['GET','POST'])
@login_required
def polltovote():
    if request.method == 'GET':
        return redirect("/dashboard")
    else:   		
        pollid=request.form.get("pollid")
        return redirect(url_for('search', pollid=pollid)) 
        
        

#VOTE FOR OTHER POLLS        
@epoller.route('/search/<int:pollid>',methods=['GET','POST'])
@login_required
def search(pollid):
    totalpolls = db.execute("SELECT * FROM poll WHERE pollid=:pollid",{'pollid':pollid}).fetchall()
    options = db.execute("SELECT * FROM option WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    if len(totalpolls) != 0:
        if totalpolls[0]["user_id"]!= int(session["user_id"]):
            hide=0
        else:
            hide=1
        if 'voteforpoll' in request.form:
            vote=request.form.get("vote")
            voteforpoll(pollid,vote)
        elif 'result' in request.form:
            print_result=result(pollid)
            return render_template("polltovote.html",user=session["firstname"],totalpolls=totalpolls,print_result=print_result,options=options)
        check=checkpoll()
        return render_template("polltovote.html", totalpolls=totalpolls, user=session["firstname"],hide=hide,check=check,end=int(totalpolls[0]["ended"],options=options))
    else:
        return render_template("polltovote.html",message="Not found",user=session["firstname"])


#MAIN FUNCTION
if __name__=='__main__':
    epoller.run(debug=True)
    
    
    

