import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from collections import OrderedDict
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



#FUNCTION TO CHECK IF USERNAME ALREADY EXISTS
def username_return(username):
    return db.execute("SELECT * FROM users WHERE username = :username", {'username': username}).fetchall()
    

#FUNCTION TO INSERT VOTE INTO DATABASE
def voteforpoll(pollid,option):
    db.execute("INSERT INTO votes (pollid,user_id,option_id) VALUES(:pollid,:user_id,:option_id)",
                        {'pollid':pollid, 'user_id':int(session["user_id"]), 'option_id':option})
    db.execute("UPDATE poll SET totalvotes = totalvotes+1 WHERE pollid=:pollid",{'pollid':pollid})
    db.execute("UPDATE option SET votes = votes+1 WHERE option_id=:option_id",{'option_id':option})
    db.commit()

#FUNCTION TO CHECK WHETHER USER ALREADY VOTED OR NOT
def checkpoll():
    listt=db.execute("SELECT DISTINCT pollid FROM votes WHERE user_id = :user ", {'user': int(session["user_id"])}).fetchall()
    check=[x[0] for x in listt]
    return check


#FUNCTION TO END POLL
def endpoll(pollid):
    db.execute("UPDATE poll SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
    db.execute("UPDATE option SET ended=1 WHERE pollid=:pollid",{'pollid':pollid})
    db.commit()


#FUNCTION TO RETURN RESULT OF A POLL
def result(pollid):
    totalvotes = db.execute("SELECT totalvotes FROM poll WHERE pollid=:pollid",{'pollid':pollid}).scalar()
    options = db.execute("SELECT * FROM option WHERE pollid=:pollid ORDER BY option_id ASC",{'pollid':pollid}).fetchall()
    print_result = OrderedDict()
    for item in range(len(options)):
        if totalvotes == 0:
            temp = 0
        else:
            temp = round((options[item]["votes"]/totalvotes)*100,2)
        print_result[options[item]["option_id"]] = [temp,options[item]["name"]]
    return print_result

#FUNCTION TO SEND EMAIL
def send_email(receiver,message,subject):
    msg = Message(
        subject,
        sender = os.getenv("MAIL_USERNAME"),
        recipients = receiver
        )
    msg.body = message
    mail.send(msg)