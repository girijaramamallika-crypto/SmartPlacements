from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import date
from models.models import db, Student, Admin, Company, PlacementDrive, Application

app = Flask(__name__)
app.secret_key = "placement_secret_key"

app.config.from_pyfile("config.py")
app.config["UPLOAD_FOLDER"] = "static/resumes"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- STUDENT REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student = Student(
            full_name=request.form["full_name"],
            roll_number=request.form["roll_number"],
            email=request.form["email"],
            phone=request.form["phone"],
            password=request.form["password"],
            branch=request.form["branch"],
            cgpa=float(request.form["cgpa"]) if request.form["cgpa"] else None,
            skills=request.form["skills"]
        )

        db.session.add(student)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("register.html")
# ---------------- STUDENT LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        student = Student.query.filter_by(
            email=email,
            password=password
        ).first()
        if student:
            session["student_id"] = student.student_id

            return redirect(url_for("student_dashboard"))
            
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(
            username=username,
            password=password
        ).first()

        
        if admin:
            session["admin_id"] = admin.admin_id
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid Admin Username or Password"

    return render_template("admin_login.html")
# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(session["admin_id"])

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()

    return render_template(
        "admin_dashboard.html",
        admin=admin,
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications
    )
# ---------------- ADD COMPANY ----------------

@app.route("/add-company", methods=["GET", "POST"])
def add_company():

    if request.method == "POST":

        company = Company(
            company_name=request.form["company_name"],
            job_role=request.form["job_role"],
            package=request.form["package"],
            eligibility_cgpa=float(request.form["eligibility_cgpa"])
            if request.form["eligibility_cgpa"] else None,
            required_skills=request.form["required_skills"],
            location=request.form["location"],
            drive_date=request.form["drive_date"]
        )

        db.session.add(company)
        db.session.commit()

        return redirect(url_for("view_companies"))

    return render_template("add_company.html")


# ---------------- VIEW COMPANIES ----------------

@app.route("/view-companies")
def view_companies():

    search = request.args.get("search", "").strip()

    if search:
        companies = Company.query.filter(
            db.or_(
                Company.company_name.ilike(f"%{search}%"),
                Company.job_role.ilike(f"%{search}%"),
                Company.location.ilike(f"%{search}%")
            )
        ).all()
    else:
        companies = Company.query.all()

    return render_template(
        "view_companies.html",
        companies=companies,
        search=search
    )


# ---------------- EDIT COMPANY ----------------

@app.route("/edit-company/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):

    company = Company.query.get_or_404(company_id)

    if request.method == "POST":

        company.company_name = request.form["company_name"]
        company.job_role = request.form["job_role"]
        company.package = request.form["package"]

        company.eligibility_cgpa = (
            float(request.form["eligibility_cgpa"])
            if request.form["eligibility_cgpa"]
            else None
        )

        company.required_skills = request.form["required_skills"]
        company.location = request.form["location"]
        company.drive_date = request.form["drive_date"]

        db.session.commit()

        return redirect(url_for("view_companies"))

    return render_template(
        "edit_company.html",
        company=company
    )


# ---------------- DATABASE ----------------
@app.route("/delete-company/<int:company_id>")
def delete_company(company_id):

    company = Company.query.get_or_404(company_id)

    db.session.delete(company)
    db.session.commit()

    return redirect(url_for("view_companies"))
@app.route("/add-drive", methods=["GET", "POST"])
def add_drive():

    companies = Company.query.all()

    if request.method == "POST":

        drive = PlacementDrive(
            company_id=request.form["company_id"],
            drive_title=request.form["drive_title"],
            drive_date=request.form["drive_date"],
            last_date_to_apply=request.form["last_date_to_apply"],
            venue=request.form["venue"],
            description=request.form["description"]
        )

        db.session.add(drive)
        db.session.commit()

        return redirect(url_for("admin_login"))

    return render_template(
        "add_drive.html",
        companies=companies
    )
@app.route("/view-drives")
def view_drives():

    search = request.args.get("search", "").strip()

    if search:
        drives = PlacementDrive.query.join(Company).filter(
            db.or_(
                PlacementDrive.drive_title.ilike(f"%{search}%"),
                PlacementDrive.venue.ilike(f"%{search}%"),
                Company.company_name.ilike(f"%{search}%")
            )
        ).all()
    else:
        drives = PlacementDrive.query.all()

    return render_template(
        "view_drives.html",
        drives=drives,
        search=search
    )
@app.route("/edit-drive/<int:drive_id>", methods=["GET", "POST"])
def edit_drive(drive_id):

    drive = PlacementDrive.query.get_or_404(drive_id)
    companies = Company.query.all()

    if request.method == "POST":

        drive.company_id = request.form["company_id"]
        drive.drive_title = request.form["drive_title"]
        drive.drive_date = request.form["drive_date"]
        drive.last_date_to_apply = request.form["last_date_to_apply"]
        drive.venue = request.form["venue"]
        drive.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("view_drives"))

    return render_template(
        "edit_drive.html",
        drive=drive,
        companies=companies
    )
@app.route("/delete-drive/<int:drive_id>")
def delete_drive(drive_id):

    drive = PlacementDrive.query.get_or_404(drive_id)

    db.session.delete(drive)
    db.session.commit()

    return redirect(url_for("view_drives"))
@app.route("/student/drives")
def student_view_drives():

    drives = PlacementDrive.query.all()

    return render_template(
        "student_view_drives.html",
        drives=drives
    )
@app.route("/apply/<int:drive_id>")
def apply_drive(drive_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    application = Application(
        student_id=session["student_id"],
        drive_id=drive_id,
        application_date=date.today(),
        status="Applied"
    )

    db.session.add(application)
    db.session.commit()

    return redirect(url_for("student_view_drives"))
# ---------------- VIEW STUDENTS ----------------
# ---------------- PLACEMENT REPORTS ----------------

@app.route("/reports")
def reports():

    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()

    selected_students = Application.query.filter_by(
        status="Selected"
    ).count()

    rejected_students = Application.query.filter_by(
        status="Rejected"
    ).count()

    return render_template(
        "reports.html",
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        selected_students=selected_students,
        rejected_students=rejected_students
    )

@app.route("/view-students")
def view_students():

    search = request.args.get("search", "").strip()

    if search:
        students = Student.query.filter(
            db.or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.roll_number.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.branch.ilike(f"%{search}%")
            )
        ).all()
    else:
        students = Student.query.all()

    return render_template(
        "view_students.html",
        students=students,
        search=search
    )
@app.route("/view-applications")
def view_applications():

    applications = Application.query.all()

    return render_template(
        "view_applications.html",
        applications=applications
    )
@app.route("/update-application/<int:application_id>", methods=["GET", "POST"])
def update_application(application_id):

    application = Application.query.get_or_404(application_id)

    if request.method == "POST":

        application.status = request.form["status"]

        db.session.commit()

        return redirect(url_for("view_applications"))

    return render_template(
        "update_application.html",
        application=application
    )
with app.app_context():
    db.create_all()
@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:
        return redirect(url_for("login"))

    applications = Application.query.filter_by(
        student_id=session["student_id"]
    ).all()

    return render_template(
        "my_applications.html",
        applications=applications
    )
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "student_id" not in session:
        return redirect(url_for("login"))

    student = Student.query.get_or_404(session["student_id"])

    if request.method == "POST":

        student.full_name = request.form["full_name"]
        student.email = request.form["email"]
        student.phone = request.form["phone"]

        student.cgpa = (
            float(request.form["cgpa"])
            if request.form["cgpa"] else None
        )

        student.skills = request.form["skills"]

        db.session.commit()

        return redirect(url_for("edit_profile"))

    return render_template(
        "edit_profile.html",
        student=student
    )
@app.route("/upload-resume", methods=["GET", "POST"])
def upload_resume():

    if request.method == "POST":

        file = request.files["resume"]

        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            return "Resume uploaded successfully!"

    return render_template("upload_resume.html")


with app.app_context():
    db.create_all()
@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(url_for("login"))

    student = Student.query.get_or_404(session["student_id"])

    application = Application.query.filter_by(
        student_id=student.student_id
    ).first()

    return render_template(
        "student_dashboard.html",
        student=student,
        application=application
    )
# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)
