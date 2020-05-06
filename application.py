import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request, redirect, session, url_for, json, jsonify, url_for
from flask_session import Session
import requests
from datetime import datetime

app = Flask(__name__)


if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///site.db'
Session(app)


@app.route("/", methods=['GET', 'POST'])
def index():
    if session.get("username") is None:
        print("Session Timed out")
        return redirect("/login")
    else:
        username = session.get('username')
        print(username)
        all_books = db.execute("select * from books").fetchmany(6)[1:]
        if request.method == "POST":
            key = request.form.get("search_key")
            return redirect(url_for("search_result", key=key))
    return render_template("index.html", all=all_books, username=username)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        session['username'] = request.form.get('username')
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        u = db.execute("select username from users where username=:username", {"username": username}).fetchone()
        e = db.execute("select email from users where email=:email", {"email": email}).fetchone()
        if u is not None:
            return "Username already exists try something else"
        elif e is not None:
            return "account with given email already exists"
        elif request.form.get("password") != request.form.get("confirm_password"):
            return "password does not match"
        else:
            db.execute("insert into users (username,password,email) values(:username,:password, :email)",
                       {"username": username, "password": password, "email": email, })
            db.commit()
            return redirect("/login")
    return render_template("Register.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        u = db.execute("select * from users where email= :email", {"email": email}).fetchone()
        if u.email is None or u.password != password:
            return "Wrong Credentials"
        session["username"] = u.username
        return redirect(url_for('index', username=session["username"]))
    return render_template("Login.html")


@app.route("/books/<string:key>", methods=["GET", "POST"])
def search_result(key):
    username = session.get("username")
    m1 = db.execute("select * from books where isbn like '%"+key+"%'").fetchall()
    m2 = db.execute("select * from books where title like '%"+key+"%'").fetchall()
    m3 = db.execute("select * from books where author like '%"+key+"%'").fetchall()
    session["books"] = []
    for i in m1:
        session["books"].append(i)
    for i in m2:
        session["books"].append(i)
    for i in m3:
        session["books"].append(i)
    if len(session["books"]) == 0:
        return render_template("Fail.html")
    return render_template("search_result.html", m1=m1, m2=m2, m3=m3, key=key, username=username)


@app.route("/book/<string:i>", methods=["GET", "POST"])
def book(i):
    username = session.get("username")
    r = requests.get("https://www.goodreads.com/book/review_counts.json",
                     params={"key": "UpOCOvXFrbolK5UMWop8aw", "isbns": i})
    if r.status_code != 200:
        raise Exception("ERROR: isbn not found")
    average_rating = r.json()["books"][0]["average_rating"]
    work_rating_count = r.json()["books"][0]["work_ratings_count"]
    work_text_reviews_count = r.json()["books"][0]["work_text_reviews_count"]
    res = db.execute("select * from books where isbn like :isbn", {"isbn": i}).fetchone()
    if request.method == "POST":
        review = request.form.get("comment")
        rate = int(request.form.get("rating"))
        date = str(datetime.now())
        user = db.execute("select * from users where username= :username", {"username": username}).fetchone()
        db.execute("insert into reviews (rating , comment, user_id, book_id, date) "
                   "values (:rating, :comment, :user_id, :book_id, :date)",
                   {"rating": rate, "comment": review, "user_id": user.id, "book_id": res.id, "date": date})
        db.commit()
        reviews = db.execute("SELECT * FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id",
                             {"book_id": res.id}).fetchall()
        return render_template("book.html", username=username, isbn=i, avg=average_rating, count=work_rating_count,
                               textcount=work_text_reviews_count, book=res, reviews=reviews)
    reviews = db.execute("SELECT * FROM reviews JOIN users ON users.id = reviews.user_id WHERE book_id = :book_id",
                         {"book_id": res.id}).fetchall()
    return render_template("book.html", username=username, isbn=i, avg=average_rating, count=work_rating_count,
                           textcount=work_text_reviews_count, book=res, reviews=reviews)


@app.route("/api/<string:i>", methods=['GET'])
def isbn(i):
    r = requests.get("https://www.goodreads.com/book/review_counts.json",
                     params={"key": "UpOCOvXFrbolK5UMWop8aw", "isbns": i})
    res = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": i}).fetchone()
    if r.status_code != 200:
        raise Exception("ERROR: isbn not found")
    work_ratings_count = r.json()["books"][0]["work_ratings_count"]
    work_text_reviews_count = r.json()["books"][0]["work_text_reviews_count"]
    average_rating = r.json()["books"][0]["average_rating"]
    return jsonify(
        {
            "title": res.title,
            "author": res.author,
            "year": res.year,
            "isbn": res.isbn,
            "work_ratings_count": work_ratings_count,
            "work_text_reviews_count": work_text_reviews_count,
            "average_rating": average_rating,
        }
    )


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect("/login")