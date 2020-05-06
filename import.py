import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Create table to import data into
    #TABLE TO STORE USER'S INFORMATION
    db.execute("CREATE TABLE users (user_id SERIAL PRIMARY KEY, firstname VARCHAR NOT NULL, lastname VARCHAR NOT NULL, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    #TABLE TO STORE POLLS CREATED
    db.execute("CREATE TABLE poll (question VARCHAR NOT NULL, option1 VARCHAR NOT NULL,option2 VARCHAR NOT NULL,
                option3 VARCHAR ,option4 VARCHAR ,pollid VARCHAR NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL FOREIGN KEY REFERENCES users(user_id),ended INTEGER DEFAULT 0)")
    #TABLE TO STORE VOTES' INFORMATION
    db.execute("CREATE TABLE votes (pollid INTEGER NOT NULL FOREIGN KEY REFERENCES poll(pollid),
                user_id INTEGER NOT NULL FOREIGN KEY REFERENCES user(user_id),
                option VARCHAR NOT NULL,voted INTEGER DEFAULT 0)")


if __name__ == "__main__":
    main()
