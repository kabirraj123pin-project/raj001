from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "hostel_secret_key"

# ---------------- DATABASE CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="hostel_db"
)
cursor = db.cursor(dictionary=True)

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("home.html")




# ---------------- STUDENT REGISTER ----------------
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":

        # 🔹 STEP 2: Create folders if not exist
        folders = [
            "static/uploads/photo",
            "static/uploads/signature",
            "static/uploads/aadhaar",
            "static/uploads/hostel_fee",
            "static/uploads/admission_fee",
            "static/uploads/income_certificate"
        ]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # -------- FORM DATA --------
        name = request.form['name']
        branch = request.form['branch']
        semester = request.form['semester']
        rollno = request.form['rollno']
        gender = request.form['gender']
        dob = request.form['dob']
        email = request.form['email']
        password = request.form['password']
        
        contact = request.form['contact']
        father = request.form['father']
        mother = request.form['mother']
        parent_contact = request.form['parent_contact']
        address = request.form['address']

        rank = request.form['rank']
        category = request.form['category']
        category_rank = request.form['category_rank']
        income = request.form['income']
        aadhaar_number = request.form['aadhaar_number']

        # -------- FILES --------
        photo = request.files['photo']
        signature = request.files['signature']
        aadhaar_file = request.files['aadhaar_file']
        hostel_fee = request.files['hostel_fee_receipt']
        admission_fee = request.files['admission_fee_slip']
        income_cert = request.files['income_Certificate']   # 👈 name must match HTML

        # -------- SAVE FILES --------
        photo_name = secure_filename(photo.filename)
        signature_name = secure_filename(signature.filename)
        aadhaar_name = secure_filename(aadhaar_file.filename)
        hostel_fee_name = secure_filename(hostel_fee.filename)
        admission_fee_name = secure_filename(admission_fee.filename)
        income_cert_name = secure_filename(income_cert.filename)

        photo.save(os.path.join("static/uploads/photo", photo_name))
        signature.save(os.path.join("static/uploads/signature", signature_name))
        aadhaar_file.save(os.path.join("static/uploads/aadhaar", aadhaar_name))
        hostel_fee.save(os.path.join("static/uploads/hostel_fee", hostel_fee_name))
        admission_fee.save(os.path.join("static/uploads/admission_fee", admission_fee_name))
        income_cert.save(os.path.join("static/uploads/income_certificate", income_cert_name))

        # -------- INSERT INTO DATABASE --------
        sql = """
        INSERT INTO students
        (name, branch, semester, rollno, gender, dob, email, password,
         contact, father, mother, parent_contact, address,
         rank, category, category_rank, income, aadhaar_number,
         photo, signature, aadhaar_file, hostel_fee_receipt,
         admission_fee_slip, income_certificate)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s)
        """

        values = (
            name, branch, semester, rollno, gender, dob, email, password,
            contact, father, mother, parent_contact, address,
            rank, category, category_rank, income, aadhaar_number,
            photo_name, signature_name, aadhaar_name,
            hostel_fee_name, admission_fee_name, income_cert_name
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect("/student/login")

    return render_template("student_register.html")



# ---------------- STUDENT LOGIN ----------------
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        rollno = request.form['rollno']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM students WHERE rollno=%s AND password=%s",
            (rollno, password)
        )
        student = cursor.fetchone()

        if student:
            # 🔹 Store student info in session
            session['student_id'] = student['id']
            session['student_name'] = student['name']

            # 🔹 Redirect to dashboard
            return redirect("/student/dashboard")
        else:
            return "Invalid Roll Number or Password"

    return render_template("student_login.html")




@app.route("/student/dashboard")
def student_dashboard():
    if 'student_id' not in session:
        return redirect("/student/login")

    student_id = session['student_id']

    # Student info
    cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()

    # Hostel applications
    cursor.execute("""
    SELECT ha.*, s.name, s.rollno
    FROM hostel_applications ha
    JOIN students s ON ha.student_id = s.id
    WHERE ha.student_id=%s
    ORDER BY ha.applied_on DESC
    """, (student_id,))
    applications = cursor.fetchall()


    return render_template("student_dashboard.html",
                           student=student,
                           applications=applications)




@app.route("/student/apply", methods=["GET", "POST"])
def student_apply():
    if 'student_id' not in session:
        return redirect("/student/login")

    if request.method == "POST":
        hostel_name = request.form['hostel_name']
        room_type = request.form['room_type']
        reason = request.form['reason']
        distance = request.form['distance']  # 🔹 new field
        student_id = session['student_id']

        # Insert into hostel_applications table
        sql = """
        INSERT INTO hostel_applications (student_id, hostel_name, room_type, reason, distance)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (student_id, hostel_name, room_type, reason, distance))
        db.commit()

        return "Application Submitted Successfully! <a href='/student/dashboard'>Back to Dashboard</a>"

    return render_template("student_apply.html")




@app.route("/warden/login", methods=["GET", "POST"])
def warden_login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM warden WHERE email=%s AND password=%s", (email, password))
        warden = cursor.fetchone()

        if warden:
            session['warden_id'] = warden['id']
            session['warden_name'] = warden['name']
            return redirect("/warden/dashboard")
        else:
            return "Invalid Email or Password"

    return render_template("warden_login.html")




@app.route("/warden/dashboard")
def warden_dashboard():
    if 'warden_id' not in session:
        return redirect("/warden/login")

    # Get all students
    cursor.execute("SELECT * FROM students ORDER BY id")
    students_all = cursor.fetchall()

    # Get all hostel applications with student details
    cursor.execute("""
        SELECT ha.*, s.name, s.rollno, s.branch, s.semester, s.photo, s.signature
        FROM hostel_applications ha
        JOIN students s ON ha.student_id = s.id
        ORDER BY ha.applied_on DESC
    """)
    applications = cursor.fetchall()

    # Stats
    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()['total_students']

    cursor.execute("SELECT COUNT(DISTINCT student_id) AS total_applied FROM hostel_applications")
    total_applied = cursor.fetchone()['total_applied']

    cursor.execute("SELECT COUNT(*) AS approved_count FROM hostel_applications WHERE status='Approved'")
    approved_count = cursor.fetchone()['approved_count']

    cursor.execute("SELECT COUNT(*) AS pending_count FROM hostel_applications WHERE status='Pending'")
    pending_count = cursor.fetchone()['pending_count']

    return render_template("warden_dashboard.html",
                           total_students=total_students,
                           total_applied=total_applied,
                           approved_count=approved_count,
                           pending_count=pending_count,
                           students_all=students_all,
                           applications=applications)






# @app.route("/warden/approve/<int:app_id>")
# def warden_approve(app_id):
#     if 'warden_id' not in session:
#         return redirect("/warden/login")
#     cursor.execute("UPDATE hostel_applications SET status='Approved' WHERE id=%s", (app_id,))
#     db.commit()
#     return redirect("/warden/dashboard")

@app.route("/warden/reject/<int:app_id>")
def warden_reject(app_id):
    if 'warden_id' not in session:
        return redirect("/warden/login")
    cursor.execute("UPDATE hostel_applications SET status='Rejected' WHERE id=%s", (app_id,))
    db.commit()
    return redirect("/warden/dashboard")


@app.route("/warden/approve/<int:application_id>", methods=["GET", "POST"])
def warden_approve(application_id):
    if 'warden_id' not in session:
        return redirect("/warden/login")

    # Get application details
    cursor.execute("""
        SELECT ha.*, s.name, s.rollno, s.branch
        FROM hostel_applications ha
        JOIN students s ON ha.student_id = s.id
        WHERE ha.id=%s
    """, (application_id,))
    app_data = cursor.fetchone()

    if request.method == "POST":
        block = request.form['block']
        floor_no = request.form['floor_no']
        room_no = request.form['room_no']
        bed_no = request.form['bed_no']

        # Update application as approved with extra info
        cursor.execute("""
            UPDATE hostel_applications
            SET status='Approved', block=%s, floor_no=%s, room_no=%s, bed_no=%s
            WHERE id=%s
        """, (block, floor_no, room_no, bed_no, application_id))
        db.commit()

        return redirect("/warden/dashboard")

    return render_template("warden_approve.html", app=app_data)







@app.route("/principal/login", methods=["GET", "POST"])
def principal_login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM principal WHERE email=%s AND password=%s", (email, password))
        principal = cursor.fetchone()  # dictionary=True

        if principal:
            session['principal_id'] = principal['id']
            session['principal_name'] = principal['name']
            return redirect("/principal/dashboard")
        else:
            return "Invalid Email or Password"

    return render_template("principal_login.html")

@app.route("/principal/dashboard")
def principal_dashboard():
    if 'principal_id' not in session:
        return redirect("/principal/login")

    cursor.execute("""
        SELECT s.*, ha.id AS application_id, ha.hostel_name, ha.room_type,
               ha.distance, ha.reason, ha.status AS application_status
        FROM students s
        LEFT JOIN hostel_applications ha ON s.id = ha.student_id
        ORDER BY s.id
    """)
    students = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()['total_students']

    cursor.execute("SELECT COUNT(*) AS total_applications FROM hostel_applications")
    total_applications = cursor.fetchone()['total_applications']

    return render_template("principal_dashboard.html",
                           students=students,
                           total_students=total_students,
                           total_applications=total_applications)



@app.route("/principal/final_approve/<int:app_id>")
def principal_final_approve(app_id):
    cursor.execute("UPDATE hostel_applications SET final_status='Final Approved' WHERE id=%s", (app_id,))
    db.commit()
    return redirect("/principal/dashboard")

@app.route("/principal/final_reject/<int:app_id>")
def principal_final_reject(app_id):
    cursor.execute("UPDATE hostel_applications SET final_status='Rejected by Principal' WHERE id=%s", (app_id,))
    db.commit()
    return redirect("/principal/dashboard")





from flask import session  # ensure session imported

@app.route("/logout")
def logout():
    user_type = session.get('user_type')  # get current user type
    session.clear()  # sab session data clear

    # redirect user type ke according login page pe
    if user_type == 'student':
        return redirect("/student/login")
    elif user_type == 'warden':
        return redirect("/warden/login")
    elif user_type == 'principal':
        return redirect("/principal/login")
    else:
        return redirect("/")  # default home page




# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
