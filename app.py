from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import os
import re
from collections import Counter
from datetime import date
from models.models import (
    db,
    Student,
    Admin,
    Company,
    PlacementDrive,
    Application,
    Announcement,
    SuccessStory,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "placement_secret_key")

app.config.from_pyfile("config.py")
app.config["UPLOAD_FOLDER"] = "static/resumes"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def student_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "student_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def placement_summary():
    packages = []
    for (package,) in Company.query.with_entities(Company.package).all():
        match = re.search(r"(\d+(?:\.\d+)?)", package or "")
        if match:
            packages.append(float(match.group(1)))

    branch_counts = Counter(
        student.branch for student in Student.query.all() if student.branch
    )
    highest_package = max(packages) if packages else None
    average_package = sum(packages) / len(packages) if packages else None

    return {
        "highest_package": f"{highest_package:g} LPA" if highest_package else "Not published",
        "average_package": f"{average_package:.1f} LPA" if average_package else "Not published",
        "featured_package": "Not published",
        "featured_student": None,
        "featured_company": None,
        "placed_students": Application.query.filter_by(status="Selected").count(),
        "companies_participated": Company.query.count(),
        "drives_conducted": PlacementDrive.query.count(),
        "top_branches": [branch for branch, _ in branch_counts.most_common(4)],
        "applications": Application.query.count(),
    }


def company_to_dict(company):
    return {
        "id": company.company_id,
        "name": company.company_name,
        "job_role": company.job_role,
        "package": company.package,
        "location": company.location,
    }


def drive_to_dict(drive):
    return {
        "id": drive.drive_id,
        "title": drive.drive_title,
        "company": drive.company.company_name if drive.company else None,
        "drive_date": drive.drive_date.isoformat(),
        "last_date_to_apply": drive.last_date_to_apply.isoformat(),
        "venue": drive.venue,
        "description": drive.description,
    }


def announcement_to_dict(announcement):
    return {
        "id": announcement.announcement_id,
        "title": announcement.title,
        "body": announcement.body,
        "published_at": announcement.published_at.isoformat(),
        "is_active": announcement.is_active,
    }


def story_to_dict(story):
    return {
        "id": story.story_id,
        "student_name": story.student_name,
        "company_name": story.company_name,
        "role": story.role,
        "package": story.package,
        "story": story.story,
        "is_featured": story.is_featured,
    }


# ---------------- PUBLIC PORTAL ----------------

@app.route("/")
def home():
    summary = placement_summary()
    upcoming_drives = PlacementDrive.query.order_by(PlacementDrive.drive_date.asc()).limit(3).all()
    recruiters = Company.query.order_by(Company.company_id.desc()).limit(4).all()
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.published_at.desc()).limit(3).all()
    success_stories = SuccessStory.query.order_by(SuccessStory.is_featured.desc(), SuccessStory.story_id.desc()).limit(3).all()

    return render_template(
        "index.html",
        summary=summary,
        upcoming_drives=upcoming_drives,
        recruiters=recruiters,
        announcements=announcements,
        success_stories=success_stories,
    )


@app.route("/about-placements")
def about_placements():
    return render_template("about_placements.html")


@app.route("/statistics")
def statistics():
    return render_template("placement_statistics.html", summary=placement_summary())


@app.route("/recruiters")
def recruiters():
    companies = Company.query.order_by(Company.company_id.desc()).all()
    return render_template("recruiters.html", companies=companies)


@app.route("/public-drives")
def public_drives():
    drives = PlacementDrive.query.order_by(PlacementDrive.drive_date.asc()).all()
    return render_template("public_drives.html", drives=drives)


@app.route("/success-stories")
def success_stories():
    records = SuccessStory.query.order_by(SuccessStory.is_featured.desc(), SuccessStory.story_id.desc()).all()
    return render_template("success_stories.html", success_stories=records)


@app.route("/announcements")
def announcements():
    records = Announcement.query.filter_by(is_active=True).order_by(Announcement.published_at.desc()).all()
    return render_template("announcements.html", announcements=records)


@app.route("/api/public/home")
def public_home_api():
    return jsonify({
        "summary": placement_summary(),
        "recruiters": [company_to_dict(company) for company in Company.query.order_by(Company.company_id.desc()).limit(4).all()],
        "drives": [drive_to_dict(drive) for drive in PlacementDrive.query.order_by(PlacementDrive.drive_date.asc()).limit(3).all()],
        "announcements": [announcement_to_dict(item) for item in Announcement.query.filter_by(is_active=True).order_by(Announcement.published_at.desc()).limit(3).all()],
        "success_stories": [story_to_dict(item) for item in SuccessStory.query.order_by(SuccessStory.is_featured.desc(), SuccessStory.story_id.desc()).limit(3).all()],
    })


@app.route("/api/public/drives")
def public_drives_api():
    return jsonify([drive_to_dict(drive) for drive in PlacementDrive.query.order_by(PlacementDrive.drive_date.asc()).all()])


@app.route("/api/health/db")
def database_health_api():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "database": db.engine.url.get_backend_name()})
    except Exception:
        app.logger.exception("Database health check failed")
        return jsonify({"status": "error", "message": "Database connection failed"}), 503


@app.route("/api/admin/announcements", methods=["GET", "POST"])
@admin_required
def admin_announcements_api():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        announcement = Announcement(
            title=payload["title"],
            body=payload["body"],
            published_at=date.fromisoformat(payload.get("published_at", date.today().isoformat())),
            is_active=payload.get("is_active", True),
        )
        db.session.add(announcement)
        db.session.commit()
        return jsonify(announcement_to_dict(announcement)), 201

    records = Announcement.query.order_by(Announcement.published_at.desc()).all()
    return jsonify([announcement_to_dict(item) for item in records])


@app.route("/api/admin/announcements/<int:announcement_id>", methods=["PUT", "PATCH", "DELETE"])
@admin_required
def admin_announcement_detail_api(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    if request.method == "DELETE":
        db.session.delete(announcement)
        db.session.commit()
        return "", 204

    payload = request.get_json(silent=True) or {}
    for field in ("title", "body", "is_active"):
        if field in payload:
            setattr(announcement, field, payload[field])
    if "published_at" in payload:
        announcement.published_at = date.fromisoformat(payload["published_at"])
    db.session.commit()
    return jsonify(announcement_to_dict(announcement))


@app.route("/api/admin/success-stories", methods=["GET", "POST"])
@admin_required
def admin_success_stories_api():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        story = SuccessStory(
            student_name=payload["student_name"],
            company_name=payload["company_name"],
            role=payload["role"],
            package=payload.get("package"),
            story=payload["story"],
            is_featured=payload.get("is_featured", False),
        )
        db.session.add(story)
        db.session.commit()
        return jsonify(story_to_dict(story)), 201

    records = SuccessStory.query.order_by(SuccessStory.story_id.desc()).all()
    return jsonify([story_to_dict(item) for item in records])


@app.route("/api/admin/success-stories/<int:story_id>", methods=["PUT", "PATCH", "DELETE"])
@admin_required
def admin_success_story_detail_api(story_id):
    story = SuccessStory.query.get_or_404(story_id)
    if request.method == "DELETE":
        db.session.delete(story)
        db.session.commit()
        return "", 204

    payload = request.get_json(silent=True) or {}
    for field in ("student_name", "company_name", "role", "package", "story", "is_featured"):
        if field in payload:
            setattr(story, field, payload[field])
    db.session.commit()
    return jsonify(story_to_dict(story))


@app.route("/contact-placement-cell")
def contact_placement_cell():
    return render_template("contact_placement_cell.html")


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
            skills=request.form["skills"],
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

        student = Student.query.filter_by(email=email, password=password).first()
        if student:
            session["student_id"] = student.student_id
            return redirect(url_for("student_dashboard"))
        return "Invalid Email or Password"

    return render_template("login.html")


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session["admin_id"] = admin.admin_id
            return redirect(url_for("admin_dashboard"))
        return "Invalid Admin Username or Password"

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
@admin_required
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
        total_applications=total_applications,
    )


# ---------------- ADD COMPANY ----------------

@app.route("/add-company", methods=["GET", "POST"])
@admin_required
def add_company():
    if request.method == "POST":
        company = Company(
            company_name=request.form["company_name"],
            job_role=request.form["job_role"],
            package=request.form["package"],
            eligibility_cgpa=float(request.form["eligibility_cgpa"]) if request.form["eligibility_cgpa"] else None,
            required_skills=request.form["required_skills"],
            location=request.form["location"],
            drive_date=request.form["drive_date"],
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
                Company.location.ilike(f"%{search}%"),
            )
        ).all()
    else:
        companies = Company.query.all()

    return render_template("view_companies.html", companies=companies, search=search)


# ---------------- EDIT COMPANY ----------------

@app.route("/edit-company/<int:company_id>", methods=["GET", "POST"])
@admin_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        company.company_name = request.form["company_name"]
        company.job_role = request.form["job_role"]
        company.package = request.form["package"]
        company.eligibility_cgpa = float(request.form["eligibility_cgpa"]) if request.form["eligibility_cgpa"] else None
        company.required_skills = request.form["required_skills"]
        company.location = request.form["location"]
        company.drive_date = request.form["drive_date"]
        db.session.commit()
        return redirect(url_for("view_companies"))

    return render_template("edit_company.html", company=company)


# ---------------- DATABASE ----------------

@app.route("/delete-company/<int:company_id>")
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    return redirect(url_for("view_companies"))


@app.route("/add-drive", methods=["GET", "POST"])
@admin_required
def add_drive():
    companies = Company.query.all()

    if request.method == "POST":
        drive = PlacementDrive(
            company_id=request.form["company_id"],
            drive_title=request.form["drive_title"],
            drive_date=request.form["drive_date"],
            last_date_to_apply=request.form["last_date_to_apply"],
            venue=request.form["venue"],
            description=request.form["description"],
        )
        db.session.add(drive)
        db.session.commit()
        return redirect(url_for("view_drives"))

    return render_template("add_drive.html", companies=companies)


@app.route("/view-drives")
def view_drives():
    search = request.args.get("search", "").strip()

    if search:
        drives = PlacementDrive.query.join(Company).filter(
            db.or_(
                PlacementDrive.drive_title.ilike(f"%{search}%"),
                PlacementDrive.venue.ilike(f"%{search}%"),
                Company.company_name.ilike(f"%{search}%"),
            )
        ).all()
    else:
        drives = PlacementDrive.query.all()

    return render_template("view_drives.html", drives=drives, search=search)


@app.route("/edit-drive/<int:drive_id>", methods=["GET", "POST"])
@admin_required
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

    return render_template("edit_drive.html", drive=drive, companies=companies)


@app.route("/delete-drive/<int:drive_id>")
@admin_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    return redirect(url_for("view_drives"))


@app.route("/student/drives")
@student_required
def student_view_drives():
    drives = PlacementDrive.query.all()
    return render_template("student_view_drives.html", drives=drives)


@app.route("/apply/<int:drive_id>")
@student_required
def apply_drive(drive_id):
    if "student_id" not in session:
        return redirect(url_for("login"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    existing_application = Application.query.filter_by(
        student_id=session["student_id"],
        drive_id=drive.drive_id,
    ).first()
    if existing_application:
        return redirect(url_for("my_applications"))

    application = Application(
        student_id=session["student_id"],
        drive_id=drive_id,
        application_date=date.today(),
        status="Applied",
    )

    db.session.add(application)
    db.session.commit()
    return redirect(url_for("student_view_drives"))


# ---------------- VIEW STUDENTS ----------------
# ---------------- PLACEMENT REPORTS ----------------

@app.route("/reports")
@admin_required
def reports():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    selected_students = Application.query.filter_by(status="Selected").count()
    rejected_students = Application.query.filter_by(status="Rejected").count()

    return render_template(
        "reports.html",
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        selected_students=selected_students,
        rejected_students=rejected_students,
    )


@app.route("/view-students")
@admin_required
def view_students():
    search = request.args.get("search", "").strip()

    if search:
        students = Student.query.filter(
            db.or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.roll_number.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.branch.ilike(f"%{search}%"),
            )
        ).all()
    else:
        students = Student.query.all()

    return render_template("view_students.html", students=students, search=search)


@app.route("/add-student", methods=["GET", "POST"])
@admin_required
def add_student():
    if request.method == "POST":
        student = Student(
            full_name=request.form["full_name"],
            roll_number=request.form["roll_number"],
            email=request.form["email"],
            phone=request.form.get("phone", ""),
            password=request.form["password"],
            branch=request.form.get("branch", ""),
            cgpa=float(request.form["cgpa"]) if request.form.get("cgpa") else None,
            skills=request.form.get("skills", ""),
        )
        db.session.add(student)
        db.session.commit()
        return redirect(url_for("view_students"))

    return render_template("edit_student.html", student=None)


@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        student.full_name = request.form["full_name"]
        student.roll_number = request.form["roll_number"]
        student.email = request.form["email"]
        student.phone = request.form.get("phone", "")
        student.branch = request.form.get("branch", "")
        student.cgpa = float(request.form["cgpa"]) if request.form.get("cgpa") else None
        student.skills = request.form.get("skills", "")
        db.session.commit()
        return redirect(url_for("view_students"))

    return render_template("edit_student.html", student=student)


@app.route("/delete-student/<int:student_id>")
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    Application.query.filter_by(student_id=student.student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for("view_students"))


@app.route("/admin/upload-resume/<int:student_id>", methods=["GET", "POST"])
@admin_required
def admin_upload_resume(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        file = request.files.get("resume")
        filename = secure_filename(file.filename) if file else ""
        if not filename:
            return render_template("admin_upload_resume.html", student=student, error="Choose a resume file.")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        student.resume = filename
        db.session.commit()
        return redirect(url_for("view_students"))

    return render_template("admin_upload_resume.html", student=student)


@app.route("/view-applications")
@admin_required
def view_applications():
    applications = Application.query.all()
    return render_template("view_applications.html", applications=applications)


@app.route("/update-application/<int:application_id>", methods=["GET", "POST"])
@admin_required
def update_application(application_id):
    application = Application.query.get_or_404(application_id)

    if request.method == "POST":
        application.status = request.form["status"]
        db.session.commit()
        return redirect(url_for("view_applications"))

    return render_template("update_application.html", application=application)


with app.app_context():
    db.create_all()


@app.route("/my-applications")
@student_required
def my_applications():
    if "student_id" not in session:
        return redirect(url_for("login"))

    applications = Application.query.filter_by(student_id=session["student_id"]).all()
    return render_template("my_applications.html", applications=applications)


@app.route("/edit-profile", methods=["GET", "POST"])
@student_required
def edit_profile():
    if "student_id" not in session:
        return redirect(url_for("login"))

    student = Student.query.get_or_404(session["student_id"])

    if request.method == "POST":
        student.full_name = request.form["full_name"]
        student.email = request.form["email"]
        student.phone = request.form["phone"]
        student.cgpa = float(request.form["cgpa"]) if request.form["cgpa"] else None
        student.skills = request.form["skills"]
        db.session.commit()
        return redirect(url_for("edit_profile"))

    return render_template("edit_profile.html", student=student)


@app.route("/upload-resume", methods=["GET", "POST"])
@student_required
def upload_resume():
    if "student_id" not in session:
        return redirect(url_for("login"))

    student = Student.query.get_or_404(session["student_id"])
    if request.method == "POST":
        file = request.files["resume"]
        filename = secure_filename(file.filename) if file else ""
        if filename:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            student.resume = filename
            db.session.commit()
            return redirect(url_for("student_dashboard"))

    return render_template("upload_resume.html", student=student)


@app.route("/student-dashboard")
@student_required
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("login"))

    student = Student.query.get_or_404(session["student_id"])
    application = Application.query.filter_by(student_id=student.student_id).first()

    return render_template("student_dashboard.html", student=student, application=application)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
