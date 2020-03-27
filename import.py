import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Create table to import data into
    db.execute("CREATE TABLE users (user_id SERIAL PRIMARY KEY, firstname VARCHAR NOT NULL, lastname VARCHAR NOT NULL, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    db.execute("CREATE TABLE poll (title VARCHAR NOT NULL, option1 VARCHAR NOT NULL,option2 VARCHAR NOT NULL,option3 VARCHAR ,option4 VARCHAR ,uid VARCHAR NOT NULL PRIMARY KEY)")
    db.execute("CREATE TABLE vote_count()")


if __name__ == "__main__":
    main()
