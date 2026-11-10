import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date
from database import db, add_leave, view_leaves, get_leave_by_id, update_leave, delete_leave, User
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
            session["role"] = user.role

            if user.role == "manager":
                return redirect(url_for("manager_dashboard"))
            else:
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

@app.route("/edit/<int:leave_id>", methods=["GET", "POST"])
@login_required
def edit_leave(leave_id):

    leave = get_leave_by_id(leave_id)

    if leave is None or leave.employee_id != int(session["username"]):
        return "Leave application not found!", 404

    if leave.status != "Pending":
        return "Only pending leave applications can be deleted!", 403


    if request.method == "POST":

        leave_type = request.form.get("leave_type")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        reason = request.form.get("reason")
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

        except (TypeError, ValueError):
            return "Invalid date format!", 400

        if not all([leave_type, start_date_str, end_date_str, reason]):
            return "All fields are required!", 400

        if end_date < start_date:
            return "End date cannot be before start date!", 400
        
        update_leave(
            leave,
            leave_type,
            start_date,
            end_date,
            reason
        )

        return redirect(url_for("dashboard"))
    return render_template("edit_leave.html", leave=leave)

@app.route("/delete/<int:leave_id>", methods = ["POST"])
@login_required
def delete_leave_record(leave_id):
    
    leave = get_leave_by_id(leave_id)
    
    if leave is None or leave.employee_id != int(session["username"]):
        return "Leave application not found", 404
    
    if leave.status != "Pending":
        return "Only pending leave applications can be deleted!", 403

    delete_leave(leave)

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug = True)