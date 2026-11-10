
from getpass import getpass

from app import app
from database import db, User
from werkzeug.security import generate_password_hash


with app.app_context():

    username = input("Enter manager username: ")
    password = getpass("Enter manager password: ")

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        print("This username already exists!")

    else:
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password_hash=hashed_password,
            role="manager"
        )

        db.session.add(new_user)
        db.session.commit()

        print("Manager account created successfully!")
