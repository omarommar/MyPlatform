from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "myplatform_secret"

DATABASE = "platform.db"

UPLOAD_FOLDER = "static/uploads/course_images"

VIDEO_FOLDER = "static/uploads/videos"
PDF_FOLDER = "static/uploads/pdfs"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["VIDEO_FOLDER"] = VIDEO_FOLDER
app.config["PDF_FOLDER"] = PDF_FOLDER

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
        role = "student"

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, password, role)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "هذا البريد الإلكتروني مستخدم بالفعل"

        finally:
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
            session["email"] = user["email"]
            session["role"] = user["role"]

            if user["email"] == "omromat7@gmail.com":
                return redirect("/admin")

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

@app.route("/buy/<int:course_id>", methods=["GET", "POST"])
def buy(course_id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        payment = request.files["payment"]

        filename = ""

        if payment.filename != "":
            filename = secure_filename(payment.filename)

            payment.save(
                os.path.join(
                    "static/uploads",
                    filename
                )
            )

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO purchases
        (user_id,course_id,payment_image)
        VALUES(?,?,?)
        """,
        (
            session["user_id"],
            course_id,
            filename
        ))

        conn.commit()
        conn.close()

        return "تم إرسال طلب الشراء بنجاح"

    return render_template(
        "buy.html",
        course_id=course_id
    )
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

@app.route("/course/<int:course_id>")
def course(course_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM courses WHERE id=?",
        (course_id,)
    )
    course = cur.fetchone()

    show_lessons = False

    # المدرس صاحب الكورس
    if session["role"] == "teacher":
        if course["teacher_id"] == session["user_id"]:
            show_lessons = True

    # الطالب المشترى للكورس
    else:
        cur.execute("""
        SELECT *
        FROM purchases
        WHERE user_id=?
        AND course_id=?
        AND status='approved'
        """,
        (
            session["user_id"],
            course_id
        ))

        if cur.fetchone():
            show_lessons = True

    lessons = []

    if show_lessons:
        cur.execute(
            "SELECT * FROM lessons WHERE course_id=?",
            (course_id,)
        )
        lessons = cur.fetchall()

    conn.close()

    return render_template(
        "course.html",
        course=course,
        lessons=lessons,
        show_lessons=show_lessons
    )
@app.route("/add-lesson/<int:course_id>", methods=["GET", "POST"])
def add_lesson(course_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "teacher":
        return redirect("/student")

    if request.method == "POST":

        title = request.form["title"]

        video = request.files["video"]
        pdf = request.files["pdf"]

        video_name = secure_filename(video.filename)
        pdf_name = secure_filename(pdf.filename)

        if video_name:
            video.save(os.path.join(app.config["VIDEO_FOLDER"], video_name))

        if pdf_name:
            pdf.save(os.path.join(app.config["PDF_FOLDER"], pdf_name))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO lessons(course_id, title, video, pdf)
            VALUES (?, ?, ?, ?)
            """,
            (course_id, title, video_name, pdf_name)
        )

        conn.commit()
        conn.close()

        return redirect(f"/course/{course_id}")

    return render_template("add_lesson.html")
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["email"] != "omromat7@gmail.com":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users
    )
@app.route("/make-teacher/<int:user_id>")
def make_teacher(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["email"] != "omromat7@gmail.com":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET role='teacher' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/make-student/<int:user_id>")
def make_student(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["email"] != "omromat7@gmail.com":
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET role='student' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
