import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Create table to import data into

    #TABLE TO STORE USER INFORMATION
    db.execute("CREATE TABLE users (user_id SERIAL PRIMARY KEY, firstname VARCHAR NOT NULL, lastname VARCHAR NOT NULL, email VARCHAR NOT NULL, aadhar VARCHAR NOT NULL, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    
    db.execute("CREATE TABLE poll (question VARCHAR NOT NULL ,pollid INTEGER NOT NULL PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(user_id),ended INTEGER DEFAULT 0)")
    
    #TABLE TO STORE OPTIONS
    db.execute("CREATE TABLE option (option_id SERIAL PRIMARY KEY, name VARCHAR NOT NULL,pollid INTEGER NOT NULL,user_id INTEGER NOT NULL REFERENCES users(user_id)")
    
    #TABLE TO STORE VOTES INFORMATION
    db.execute("CREATE TABLE votes (pollid INTEGER NOT NULL REFERENCES poll(pollid),user_id INTEGER NOT NULL REFERENCES users(user_id),option VARCHAR NOT NULL)")
    
    #TABLE TO STORE MESSAGES RECEIVED FROM USER
    db.execute("CREATE TABLE contact (firstname VARCHAR NOT NULL,lastname VARCHAR NOT NULL,message VARCHAR NOT NULL,email VARCHAR NOT NULL)")
    db.commit()

if __name__ == "__main__":
    main()

