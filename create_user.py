from app import app
from database import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "1950"
    password = "1950"

    hashed_password = generate_password_hash(password)

    new_user = User(
        username = username,
        password_hash = hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    print("User created successfully")