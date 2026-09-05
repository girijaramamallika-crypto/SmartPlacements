from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    password = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    resume = db.Column(db.String(255))
class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
class Company(db.Model):
    __tablename__ = "companies"

    company_id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(100), nullable=False)

    job_role = db.Column(db.String(100), nullable=False)

    package = db.Column(db.String(50))

    eligibility_cgpa = db.Column(db.Float)

    required_skills = db.Column(db.Text)

    location = db.Column(db.String(100))

    drive_date = db.Column(db.String(30))
class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    drive_id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.company_id"),
        nullable=False
    )

    drive_title = db.Column(db.String(100), nullable=False)
    drive_date = db.Column(db.Date, nullable=False)
    last_date_to_apply = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(100))
    description = db.Column(db.Text)

    company = db.relationship(
        "Company",
        backref="placement_drives"
    )
class Application(db.Model):
    __tablename__ = "applications"

    application_id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.student_id"),
        nullable=False
    )

    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drives.drive_id"),
        nullable=False
    )

    application_date = db.Column(db.Date)
    status = db.Column(
        db.String(50),
        default="Applied"
    )

    student = db.relationship(
        "Student",
        backref="applications"
    )

    drive = db.relationship(
        "PlacementDrive",
        backref="applications"
    )