
import os
from functools import wraps
from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import (
    db,
    add_leave,
    view_leaves,
    get_leave_by_id,
    update_leave,
    delete_leave,
    User,
    LeaveRequest
)

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leave_db.db"

db.init_app(app)


# ==========================================
# AUTHENTICATION DECORATORS
# ==========================================

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            print("Inside login")
            flash("Please login to continue", "error")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*required_roles):

    def decorator(view_function):

        @wraps(view_function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                print("Inside role")
                flash("Please login to continue", "error")
                return redirect(url_for("login"))

            if session.get("role") not in required_roles:
                return "You do not have permission to access this page", 403

            return view_function(*args, **kwargs)

        return wrapper

    return decorator


# ==========================================
# LOGIN
# ==========================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            print("LOGIN USER: ", user.username)
            print("LOGIN ROLE: ", user.role)
            print("SESSION: ", dict(session))

            # Redirect based on user role

            if user.role == "super_admin":
                return redirect(url_for("super_admin_dashboard"))

            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))

            elif user.role == "manager":
                return redirect(url_for("manager_dashboard"))

            elif user.role == "employee":
                return redirect(url_for("dashboard"))

            else:
                session.clear()
                return "Invalid user role", 403

        else:
            return "Invalid username or password"

    return render_template("login.html")


# ==========================================
# EMPLOYEE DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
@role_required("employee")
def dashboard():

    employee_id = session["user_id"]

    leaves = view_leaves(employee_id)

    return render_template(
        "dashboard.html",
        leaves=leaves
    )


# ==========================================
# MANAGER DASHBOARD
# ==========================================

@app.route("/manager_dashboard")
@login_required
@role_required("manager")
def manager_dashboard():

    manager_id = session["user_id"]

    employees = User.query.filter_by(
        manager_id=manager_id
    ).all()

    employee_ids = [employee.id for employee in employees]

    team_leaves = LeaveRequest.query.filter(
        LeaveRequest.employee_id.in_(employee_ids)
    ).order_by(LeaveRequest.id.desc()).all()

    return render_template(
        "manager_dashboard.html",
        leaves=team_leaves,
        employees=employees
    )


# ==========================================
# APPLY FOR LEAVE
# ==========================================

@app.route("/apply", methods=["GET", "POST"])
@login_required
@role_required("employee", "manager")
def apply_leave():

    if request.method == "POST":

        employee_id = session["user_id"]
        leave_type = request.form.get("leave_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        reason = request.form.get("reason")

        if not all([employee_id, leave_type, start_date, end_date, reason]):
            return "All fields are required", 400

        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)

        except ValueError:
            return "Invalid date", 400

        if employee_id <= 0:
            return "Employee ID must be positive", 400

        if end_date < start_date:
            return "End date cannot be before start date", 400

        add_leave(
            employee_id,
            leave_type,
            start_date,
            end_date,
            reason
        )

        if session["role"] == "manager":
            return redirect(url_for("manager_dashboard"))

        else:
            return redirect(url_for("dashboard"))

    return render_template("apply_leave.html")


# ==========================================
# EDIT LEAVE
# ==========================================

@app.route("/edit/<int:leave_id>", methods=["GET", "POST"])
@login_required
@role_required("employee", "manager")
def edit_leave(leave_id):

    leave = get_leave_by_id(leave_id)

    if leave is None or leave.employee_id != session["user_id"]:
        return "Leave application not found!", 404

    if leave.status != "Pending":
        return "Only pending leave applications can be edited!", 403

    if request.method == "POST":

        leave_type = request.form.get("leave_type")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        reason = request.form.get("reason")

        if not all([leave_type, start_date_str, end_date_str, reason]):
            return "All fields are required!", 400

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

        except (TypeError, ValueError):
            return "Invalid date format!", 400

        if end_date < start_date:
            return "End date cannot be before start date!", 400

        update_leave(
            leave,
            leave_type,
            start_date,
            end_date,
            reason
        )

        if session["role"] == "employee":
            return redirect(url_for("dashboard"))

        else:
            return redirect(url_for("manager_dashboard"))

    return render_template(
        "edit_leave.html",
        leave=leave
    )


# ==========================================
# DELETE LEAVE
# ==========================================

@app.route("/delete/<int:leave_id>", methods=["POST"])
@login_required
@role_required("employee", "manager")
def delete_leave_record(leave_id):

    leave = get_leave_by_id(leave_id)

    if leave is None or leave.employee_id != session["user_id"]:
        return "Leave application not found", 404

    if leave.status != "Pending":
        return "Only pending leave applications can be deleted!", 403

    delete_leave(leave)

    if session["role"] == "employee":
        return redirect(url_for("dashboard"))

    else:
        return redirect(url_for("manager_dashboard"))


# ==========================================
# SUPER ADMIN DASHBOARD
# ==========================================

@app.route("/super_admin_dashboard")
@login_required
@role_required("super_admin")
def super_admin_dashboard():

    users = User.query.order_by(
        User.id.desc()
    ).all()

    leaves = LeaveRequest.query.order_by(
        LeaveRequest.id.desc()
    ).all()

    return render_template(
        "super_admin_dashboard.html",
        users=users,
        leaves=leaves
    )
    

# ==========================================
# CREATE USER (SUPER ADMIN ONLY)
# ==========================================

@app.route("/create_user", methods=["POST"])
@login_required
@role_required("super_admin")
def create_user():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "").strip()
    manager_id = request.form.get("manager_id", "").strip()

    # Validate required fields
    if not username or not password or not role:
        flash("All required fields must be filled!", "error")
        return redirect(url_for("super_admin_dashboard"))

    # Validate role
    allowed_roles = [
        "employee",
        "manager",
        "admin",
        "super_admin"
    ]

    if role not in allowed_roles:
        flash("Invalid user role selected!", "error")
        return redirect(url_for("super_admin_dashboard"))

    # Check duplicate username
    existing_user = User.query.filter_by(
        username=username
    ).first()

    if existing_user:
        flash("This username already exists!", "error")
        return redirect(url_for("super_admin_dashboard"))

    # Validate manager assignment
    assigned_manager = None

    if role == "employee" and manager_id:

        try:
            manager_id = int(manager_id)
        except ValueError:
            flash("Invalid manager selected!", "error")
            return redirect(url_for("super_admin_dashboard"))

        assigned_manager = User.query.filter_by(
            id=manager_id,
            role="manager"
        ).first()

        if assigned_manager is None:
            flash("Selected manager does not exist!", "error")
            return redirect(url_for("super_admin_dashboard"))

    # Hash password
    hashed_password = generate_password_hash(password)

    # Create user
    new_user = User(
        username=username,
        password_hash=hashed_password,
        role=role,
        manager_id=assigned_manager.id if assigned_manager else None
    )

    db.session.add(new_user)
    db.session.commit()

    flash(
        f"{role.replace('_', ' ').title()} account created successfully!",
        "success"
    )

    return redirect(url_for("super_admin_dashboard"))



# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin_dashboard")
@login_required
@role_required("admin")
def admin_dashboard():

    users = User.query.order_by(
        User.id.desc()
    ).all()

    leaves = LeaveRequest.query.order_by(
        LeaveRequest.id.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        users=users,
        leaves=leaves
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

with app.app_context():
    db.create_all()


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )
print("Test")