from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "myplatform_secret"

DATABASE = "platform.db"

UPLOAD_FOLDER = "static/uploads/course_images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(username,email,password,role) VALUES(?,?,?,?)",
            (username, email, password, role)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email,password)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "teacher":
                return redirect("/teacher")

            return redirect("/student")

        return "بيانات الدخول غير صحيحة"

    return render_template("login.html")
@app.route("/teacher")
def teacher():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "teacher":
        return redirect("/student")

    return render_template("teacher_dashboard.html")


@app.route("/student")
def student():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("student_dashboard.html")


@app.route("/add-course", methods=["GET", "POST"])
def add_course():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "teacher":
        return redirect("/student")

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]

        image = request.files["image"]

        filename = ""

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO courses
            (title, description, price, image, teacher_id)
            VALUES (?,?,?,?,?)
        """, (
            title,
            description,
            price,
            filename,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/courses")

    return render_template("add_course.html")


@app.route("/courses")
def courses():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM courses")

    courses = cur.fetchall()

    conn.close()

    return render_template(
        "courses.html",
        courses=courses
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
