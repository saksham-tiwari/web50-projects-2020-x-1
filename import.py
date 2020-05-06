import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for a,b,c,d in reader:
        db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": a, "title": b, "author": c, "year": d})
        print(f"\t ISBN: {a}, \t Title: {b}, \t Author: {c}, \t Published in: {d}")
    db.commit()

if __name__ == "__main__":
    main()
