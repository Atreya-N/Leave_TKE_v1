from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import prac


app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"


@app.route("/", methods = ["GET", "POST", "PATCH", "DELETE"])
def login():
    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        connection = prac.connection_db()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT Employee_Name, Username, Password, Role
            FROM admin_log
            WHERE Username = ?""", (username,))

        user = cursor.fetchone()

        if user is None:
            connection.close()
            flash("Invalid username or password.")
            return render_template("login.html")
        
        employee_name, db_username, stored_password, role = user

        # Check password
        password_valid = False

        try:
            password_valid = check_password_hash(
                stored_password, password
            )
        except (ValueError, TypeError):
            password_valid = False

        # Convert an old plain-text password into a hash
        if not password_valid and stored_password == password:

            password_valid = True

            new_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE admin_log
                SET Password = ?
                WHERE Username = ?
            """, (new_hash, db_username))

            connection.commit()

        connection.close()

        if not password_valid:
            flash("Invalid username or password.")
            return render_template("login.html")

        # Store login information
        session.clear()
        session["username"] = db_username
        session["employee_name"] = employee_name
        session["role"] = role.strip().lower()

        # Redirect according to database role
        if session["role"] == "employee":
            return redirect(url_for("employee"))

        elif session["role"] == "manager":
            return redirect(url_for("manager"))

        elif session["role"] == "admin":
            return redirect(url_for("admin"))

        session.clear()
        flash("Invalid account role.")
        return redirect(url_for("login"))

    return render_template("login.html")

def role_required(required_role):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "username" not in session:
                flash("Please log in first.")
                return redirect(url_for("login"))

            if session.get("role") != required_role:
                flash("You do not have permission.")
                return redirect(url_for("login"))

            return function(*args, **kwargs)

        return wrapper

    return decorator

@app.route("/employee")
@role_required("employee")
def employee():
    return render_template("employee.html")

@app.route("/manager")
@role_required("manager")
def manager():
    return render_template("manager.html")

@app.route("/admin")
@role_required("admin")
def admin():
    return render_template("admin.html")

@app.route("/create_user", methods = ["POST"])
@role_required("admin")
def create_user():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        message = prac.add_user(name, username, password, role)

        flash(message)
        return redirect(url_for("create_user"))

    return render_template("create_user.html")
@app.route("/manage-users", methods = ["GET"])
@role_required("admin")
def manage_users():
    users = prac.view_user()

    return render_template("updateuser.html", users=users)


# UPDATE EMPLOYEE DETAILS(use patch)

@app.route("/update-user", methods=["PATCH"])
@role_required("admin")
def update_user():

    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            success=False,
            message="Invalid request data."
        ), 400

    username = data.get("username")
    name = data.get("name", "").strip()
    role = data.get("role", "").strip().lower()

    if not username or not name:
        return jsonify(
            success=False,
            message="Employee ID and name are required."
        ), 400

    if role not in ["employee", "manager", "admin"]:
        return jsonify(
            success=False,
            message="Invalid role."
        ), 400

    message = prac.update_log(
        username,
        role=role,
        name=name
    )

    if message == "User Updated Successfully":
        return jsonify(
            success=True,
            message="Changes saved successfully!"
        )

    return jsonify(
        success=False,
        message=message
    ), 400

# DELETE EMPLOYEE(use delete)https merthodfs

@app.route("/delete-user", methods=["DELETE"])
@role_required("admin")
def delete_user():

    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            success=False,
            message="Invalid request."
        ), 400

    username = data.get("username")

    if not username:
        return jsonify(
            success=False,
            message="Employee ID is required."
        ), 400

    # Prevent deleting your own account
    if str(session.get("username")) == str(username):
        return jsonify(
            success=False,
            message="You cannot delete your own account."
        ), 400

    connection = prac.connection_db()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT Role FROM admin_log WHERE Username = ?",
            (username,)
        )

        user = cursor.fetchone()

        if user is None:
            return jsonify(
                success=False,
                message="Employee not found."
            ), 404

        target_role = user[0].strip().lower()

        # Prevent deleting the last admin
        if target_role == "admin":

            cursor.execute("""
                SELECT COUNT(*)
                FROM admin_log
                WHERE LOWER(Role) = 'admin'
            """)

            admin_count = cursor.fetchone()[0]

            if admin_count <= 1:
                return jsonify(
                    success=False,
                    message="You cannot delete the last admin account."
                ), 400

        cursor.execute(
            "DELETE FROM admin_log WHERE Username = ?",
            (username,)
        )

        connection.commit()

        return jsonify(
            success=True,
            message="Employee deleted successfully!"
        )

    finally:
        connection.close()

@app.route("/system_logs")
@role_required("admin")
def system_logs():
    return "Coming soon!"

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out.")

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
