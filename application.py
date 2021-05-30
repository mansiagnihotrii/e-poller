import os

from flask import Flask, session, render_template, redirect, request, url_for, flash, jsonify
from flask_session import Session
from actions import voteforpoll,checkpoll,result,send_email,username_return
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from flask_mail import Mail,Message


epoller= Flask(__name__)
mail = Mail(epoller)

#configuration of Mail
epoller.config['MAIL_SERVER']='smtp.gmail.com'
epoller.config['MAIL_PORT'] = 465
epoller.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
epoller.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
epoller.config['MAIL_USE_TLS'] = False
epoller.config['MAIL_USE_SSL'] = True
mail = Mail(epoller)

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
        row = username_return(request.form.get("username"))
        next_url = request.form.get("next")
        if len(row)!=1  or not check_password_hash(row[0]["password"], request.form.get("password")):
            return render_template("index.html",message = "Invalid username/password")
        session["user_id"] = row[0]["user_id"]
        session["firstname"]=row[0]["firstname"]
        if next_url:
            return redirect(next_url)
        return redirect("/dashboard")
        #return redirect("/dashboard")


#DASHBOARD
@epoller.route("/dashboard")
@login_required
def dashboard():
    poll_total=db.execute("SELECT COUNT(*) FROM poll ").scalar() #TOTAL POLLS CREATED
    temp=db.execute("SELECT * FROM poll WHERE user_id=:userid ORDER BY totalvotes DESC",{'userid':int(session["user_id"])}).fetchall() #TOTAL POLLS CREATED BY CURRENT USER
    poll_ongoing=db.execute("SELECT COUNT(*) FROM poll WHERE ended =0 AND user_id=:userid",{'userid':int(session["user_id"])}).scalar() #TOTAL ONGOING POLLS
    poll_total_user = len(temp)
    poll_ended=poll_total_user-poll_ongoing #TOTAL ENDED POLLS


    return render_template("user.html",temp=temp,user=session["firstname"],poll_total=poll_total,poll_total_user=poll_total_user,poll_ongoing=poll_ongoing,poll_ended=poll_ended,name='dashboard')



#REGISTER USER
@epoller.route("/register", methods=['GET', 'POST'])
def register():
    session.clear()
    if request.method == "POST":
        if request.form.get("password") !=  request.form.get("confirmation"):
            return render_template("register.html", message="Password do not match")
        if len(username_return(request.form.get("username")))!=0:
            return render_template("register.html", message = "Username Already Exist")
        else:
            key = db.execute("INSERT INTO users (firstname, lastname, username, email,aadhar,password) VALUES(:firstname, :lastname, :username, :email,:aadhar, :password)",
                  {'firstname': request.form.get("firstname"), 'lastname': request.form.get("lastname"), 'username': request.form.get("username"), 'email':request.form.get("email"),'aadhar':request.form.get("aadhar"),
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
        return render_template("profile.html",details = details,user=session["firstname"],name='profile')
    username = request.form.get("username")
    if len(username_return(username))!=0:
        return render_template("profile.html", message = "Username Already Exist",user=session["firstname"],color="danger",details=details,name='profile')
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
            return render_template('profile.html',message = "Old password doesn't match",user=session["firstname"],color="danger",details=details,name='profile')

        if not request.form.get("newpassword") == request.form.get("renewpassword"):
            return render_template('profile.html',message = "New passwords doesn't match",user=session["firstname"],color="danger",details=details,name='profile')
        db.execute("UPDATE users SET password =:password WHERE user_id=:user",{'password': generate_password_hash(request.form.get("newpassword"), method='pbkdf2:sha256', salt_length=8),'user': int(session["user_id"])})
        db.commit()
        return render_template('profile.html',message = "Password Updated Successfully !",user=session["firstname"],color="success",details=details,name='profile')
                  
    db.execute("UPDATE users SET username =:username,firstname=:firstname, lastname=:lastname, email=:email WHERE user_id=:user",
                  {'username':username,'firstname':firstname,'lastname':lastname,'email':email,'user': int(session["user_id"])})
    db.commit()
    details = db.execute("SELECT * FROM users WHERE user_id = :user", {'user': int(session["user_id"])}).fetchall()
    return render_template('profile.html',message = "Profile updated Succesfully",details = details,user=session["firstname"],color="success",name='profile')              



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
        url = "/search/"+str(int(poll_detail+1))
        return redirect(url)
    return render_template("create_poll.html",poll_total=poll_total,name='polls',user=session["firstname"])

#CREATED POLLS
@epoller.route('/pollscreated/ongoing',methods=['GET','POST'])
@login_required
def ongoingpolls():
    type = "created"
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended=0  ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    options = db.execute("SELECT * FROM option WHERE user_id = :user AND ended=0 ORDER BY option_id ASC", {'user': int(session["user_id"])}).fetchall()
    check = checkpoll()
    error = ""
    print_result = {}
    for x in range(len(totalpolls)):
        p = totalpolls[x]["pollid"]
        print_result[p] = result(p)
    if request.method=='POST':
        pollid=request.form.get("pollid")
        if 'end' in request.form:
            db.execute("UPDATE poll SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.execute("UPDATE option SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.commit()
            return redirect("/pollscreated/ended")
        if 'voteforpoll' in request.form:
            if pollid in check:
                error = "Already voted"
            else:
                vote=request.form.get("vote")
                voteforpoll(pollid,vote)
                return redirect("/pollscreated/ongoing")
    return render_template("/poll.html",error=error,totalpolls=totalpolls,user=session["firstname"],check=check,options=options,type=type,name='polls',print_result=print_result)



#ENDED POLLS
@epoller.route('/pollscreated/ended',methods=['GET','POST'])
@login_required
def endedpolls():
    totalpolls = db.execute("SELECT * FROM poll WHERE user_id = :user AND ended =1 ORDER BY pollid DESC", {'user': int(session["user_id"])}).fetchall()
    options = db.execute("SELECT * FROM option WHERE user_id = :user ORDER BY option_id ASC", {'user': int(session["user_id"])}).fetchall()
    print_result = {}
    for x in range(len(totalpolls)):
        p = totalpolls[x]["pollid"]
        print_result[p] = result(p)
    return render_template("/pollended.html",user=session["firstname"],totalpolls=totalpolls,options=options,print_result=print_result,name='polls')
 

#VOTE FOR OTHER POLLS
@epoller.route('/polltovote',methods=['GET','POST'])
@login_required
def polltovote():
    if request.method == 'GET':
        return redirect("/dashboard",name='dashboard')
    else:           
        pollid=request.form.get("pollid")
        return redirect(url_for('search', pollid=pollid)) 


#VOTE FOR OTHER POLLS        
@epoller.route('/search/<int:pollid>',methods=['GET','POST'])
@login_required
def search(pollid):
    totalpolls = db.execute("SELECT * FROM poll WHERE pollid=:pollid",{'pollid':pollid}).fetchall()
    options = db.execute("SELECT * FROM option WHERE pollid=:pollid", {'pollid':pollid}).fetchall()
    print_result = {}
    for x in range(len(totalpolls)):
        p = totalpolls[x]["pollid"]
        print_result[p] = result(p)
    error=""
    if len(totalpolls) != 0:
        check=checkpoll()
        if totalpolls[0]["user_id"]!= int(session["user_id"]):
            hide=0
        else:
            hide=1

        if 'end' in request.form:
            db.execute("UPDATE poll SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.execute("UPDATE option SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
            db.commit()
            return redirect('/search/'+str(pollid ))

        if 'voteforpoll' in request.form:
            if pollid in check:
                error = "Already voted"
            else:
                vote=request.form.get("vote")
                voteforpoll(pollid,vote)
                return redirect('/search/'+str(pollid ))
        return render_template("polltovote.html", totalpolls=totalpolls, user=session["firstname"],hide=hide,check=check,end=int(totalpolls[0]["ended"]),options=options,name='polls',print_result=print_result,error=error)
    else:
        return render_template("polltovote.html",message="Not found",user=session["firstname"],name='polls',print_result=print_result,error=error)


#CONTACT PAGE
@epoller.route('/contact',methods=['GET','POST'])
@login_required
def contact():
    if request.method == 'GET':
        return render_template("contact.html",user=session["firstname"],name='contact')
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")
    message = request.form.get("message")
    
    db.execute("INSERT INTO contact(firstname,lastname,email,message) VALUES(:firstname,:lastname,:email,:message)",{'firstname':firstname,'lastname':lastname,'email':email,'message':message})
    db.commit() 
    receiver = [os.getenv("MAIL_USERNAME")]
    message = "Name: "+firstname+" "+lastname+"\n"+"Email: "+email+"\n"+"Message: "+message
    subject = 'Feedback received from '+firstname+' '+lastname
    send_email(receiver,message,subject)
    return render_template("contact.html",user=session["firstname"],message = "Message sent successfully !",name='contact')        


#FAQ
@epoller.route('/faq')
@login_required
def faq():
    return render_template("faq.html",user=session["firstname"],name='faq') 

@epoller.errorhandler(404)
def page_not_found(e):
    return render_template('error_page.html'), 404

#MAIN FUNCTION
if __name__=='__main__':
    epoller.run(debug=True)
