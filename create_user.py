from getpass import getpass

from app import app
from database import db, User
from werkzeug.security import generate_password_hash


with app.app_context():

    username = input("Enter username: ").strip()
    password = getpass("Enter password: ")

    print("\nSelect user role:")
    print("1. Super Admin")
    print("2. Admin")
    print("3. Manager")
    print("4. Employee")

    role_choices = {
        "1": "super_admin",
        "2": "admin",
        "3": "manager",
        "4": "employee"
    }

    choice = input("Enter choice: ").strip()

    if not username:
        print("Username cannot be empty!")

    elif not password:
        print("Password cannot be empty!")

    elif choice not in role_choices:
        print("Invalid role selection!")

    else:
        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            print("This username already exists!")

        else:
            role = role_choices[choice]

            hashed_password = generate_password_hash(password)

            new_user = User(
                username=username,
                password_hash=hashed_password,
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

            print(f"{role} account created successfully!")
