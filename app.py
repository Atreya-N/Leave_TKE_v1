import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date
from database import db, add_leave, view_leaves, User
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRETY_KEY", "dev-only"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leave_db.db"

db.init_app(app)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username = username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid username or password"

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    employee_id = session["username"]
    leaves = view_leaves(employee_id)
    return render_template("dashboard.html", leaves = leaves)

@app.route("/apply", methods = ["GET", "POST"])
@login_required
def apply_leave():
    if request.method == "POST":
        employee_id = int(session["username"])
        leave_type = request.form.get("leave_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        reason = request.form.get("reason")

        if not all([employee_id, leave_type, start_date, end_date, reason]):
            return "All fields are required ", 400

        try:
            employee_id = int(employee_id)
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        
        except ValueError:
            return "Invalid employee ID or date", 400

        if employee_id <= 0:
            return "Employee ID ,must be positive", 400

        if end_date < start_date:
            return "End date cannot be before start date", 400

        add_leave(
            employee_id,
            leave_type,
            start_date,
            end_date,
            reason
        )
        return redirect(url_for("dashboard"))

    return render_template("apply_leave.html")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug = True)