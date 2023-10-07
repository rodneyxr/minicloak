"""
Minicloak Microservice

This microservice provides user authentication and user management functionality.
It utilizes Flask as the web framework, SQLAlchemy for database management, and JWT for authentication.

WARNING: This microservice is NOT intended for production use. It is meant to be used as a learning/development tool.

static files: static/{css,js}
templates: templates/

It includes the following endpoints for user authentication:
- POST /auth/authenticate: Authenticate a user and return a JWT token.
- POST /auth/verify: Verify the validity of a JWT token.
- POST /auth/refresh: Refresh a JWT token using a refresh token.
- POST /auth/logout: Logout a user by deleting the refresh token.

It also includes the following endpoints for user management:
- GET    /api/users: Get a list of all users.
- POST   /api/users: Create a new user.
- POST   /api/users/<id>: Edit a specific user.
- DELETE /api/users/<id>: Delete a specific user.

It also includes the following endpoints for the user management interface:
- /users: Render a page of a list of all users.
- /users/create: Render a page for creating a new user.
- /users/<id>/edit: Render a page for editing a specific user.

It includes the following sample users:
- admin: role=admin, clearance=gold
- gold: role=user, clearance=gold, team=frontend, team=backend, team=devops
- silver: role=user, clearance=silver, team=frontend
- bronze: role=user, clearance=bronze, team=devops
- guest: No attributes

SQLite is used as the database backend.
"""

import datetime
import os
import uuid

import jwt
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/static/<path:path>")
def serve_static(path):
    return url_for("static", filename=path)


# Secret key for JWT token generation (change this in production)
SECRET_KEY = "change-this-in-production"

# SQLite database file path
DATABASE_FILE = "minicloak.db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_FILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# SQLAlchemy User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    attributes = db.Column(db.PickleType, nullable=False)


# SQLAlchemy RefreshToken model
class RefreshToken(db.Model):
    token = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


def generate_jwt_token(user):
    """
    Generate a JWT token for a user.

    Args:
        user (User): The user for whom the token is generated.

    Returns:
        str: The JWT token containing user information and attributes.
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "attributes": user.attributes,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


@app.route("/auth/authenticate", methods=["POST"])
def authenticate():
    """
    Authenticate a user and return a JWT token.

    JSON Request:
    {
        "username": "user",
        "password": "password"
    }

    Returns:
    {
        "token": "JWT_token",
        "refresh_token": "refresh_token",
        "user_attributes": ["attribute1", "attribute2"]
    }
    """
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username, password=password).first()

    if user:
        token = generate_jwt_token(user)

        # Generate a refresh token and store it in the database
        refresh_token = str(uuid.uuid4())
        db.session.add(RefreshToken(token=refresh_token, user_id=user.id))
        db.session.commit()

        return jsonify(
            {
                "token": token,
                "refresh_token": refresh_token,
                "user_attributes": user.attributes,
            }
        )

    return jsonify({"message": "Invalid credentials"}), 401


@app.route("/auth/verify", methods=["POST"])
def verify_token():
    """
    Verify the validity of a JWT token.

    JSON Request:
    {
        "token": "JWT_token"
    }

    Returns:
    {
        "message": "Token is valid",
        "user_attributes": ["attribute1", "attribute2"]
    }
    """
    token = request.json.get("token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_attributes = payload["attributes"]
        return jsonify(
            {"message": "Token is valid", "user_attributes": user_attributes}
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.DecodeError:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/auth/refresh", methods=["POST"])
def refresh_token():
    """
    Refresh a JWT token using a refresh token.

    JSON Request:
    {
        "refresh_token": "refresh_token"
    }

    Returns:
    {
        "token": "new_JWT_token"
    }
    """
    refresh_token = request.json.get("refresh_token")
    refresh_token_db = RefreshToken.query.get(refresh_token)

    if refresh_token_db:
        user = User.query.get(refresh_token_db.user_id)
        token = generate_jwt_token(user)
        return jsonify({"token": token})

    return jsonify({"message": "Invalid refresh token"}), 401


@app.route("/auth/logout", methods=["POST"])
def logout():
    """
    Logout a user by deleting the refresh token.

    JSON Request:
    {
        "refresh_token": "refresh_token"
    }

    Returns:
    {
        "message": "Logout successful"
    }
    """
    refresh_token = request.json.get("refresh_token")
    refresh_token_db = RefreshToken.query.get(refresh_token)

    if refresh_token_db:
        db.session.delete(refresh_token_db)
        db.session.commit()
        return jsonify({"message": "Logout successful"})

    return jsonify({"message": "Invalid refresh token"}), 401


"""
User Management Interface
"""


@app.route("/users", methods=["GET"])
def user_management():
    """
    Render the user management interface.

    Returns:
    HTML: The user management interface HTML page.
    """
    users = User.query.all()
    return render_template("list_users.html", users=users)


@app.route("/users/create", methods=["GET"])
def create_user_page():
    """
    Render a page for creating a new user.

    Returns:
    HTML: The user creation page HTML.
    """
    return render_template("create_user.html")


@app.route("/users/<int:user_id>/edit", methods=["GET"])
def edit_user_page(user_id):
    """
    Render a page for editing a specific user.

    Args:
        user_id (int): The ID of the user to be edited.

    Returns:
    HTML: The user editing page HTML.
    """
    user = User.query.get(user_id)
    if user:
        attributes = ",".join(user.attributes)  # Join attributes into a string
        return render_template("edit_user.html", user=user, attributes=attributes)
    return redirect(url_for("user_management"))


"""
User Management API
"""

# /api/users


@app.route("/api/users", methods=["GET"])
def get_users():
    """
    Get a list of all users.

    Returns:
    JSON: A list of all users in JSON format.
    """
    users = User.query.all()
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "attributes": user.attributes,
        }
        user_list.append(user_dict)
    return jsonify(user_list)


@app.route("/api/users", methods=["POST"])
def create_user():
    """
    Create a new user.

    JSON Body:
    {
        "username": "string",
        "password": "string",
        "attributes": ["string", ...]
    }

    Returns:
    JSON: The newly created user in JSON format.
    """
    # Retrieve user data from the JSON body
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    attributes = data.get("attributes")

    # Create a new user and save to the database
    new_user = User(username=username, password=password, attributes=attributes)
    db.session.add(new_user)
    db.session.commit()

    # Return the newly created user in JSON format
    user_dict = {
        "id": new_user.id,
        "username": new_user.username,
        "attributes": new_user.attributes,
    }
    return jsonify(user_dict)


@app.route("/users/<int:user_id>", methods=["POST"])
def edit_user(user_id):
    """
    Edit a specific user.

    Args:
        user_id (int): The ID of the user to be edited.

    Form Data:
    - new_username: The new username of the user.
    - new_attributes: Comma-separated new attributes of the user.

    Redirects:
    - Redirects to the user management interface.
    """
    # Retrieve updated user data from the form
    new_username = request.form.get("username")
    new_attributes = request.form.get("attributes").split(
        ","
    )  # Split attributes into a list

    # Retrieve the user to be updated
    user = User.query.get(user_id)

    if user:
        # Update the user's username and attributes
        user.username = new_username
        user.attributes = new_attributes
        db.session.commit()

    return redirect(url_for("user_management"))


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """
    Delete a specific user.

    Args:
        user_id (int): The ID of the user to be deleted.

    Returns:
    JSON: {"message": "User deleted successfully"} or {"error": "User not found"}.
    """
    # Retrieve the user from the database and delete it
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})

    return jsonify({"error": "User not found"}), 404


def load_sample_users():
    """
    Load sample users into the database.
    """
    sample_users = [
        {
            "username": "admin",
            "password": "admin",
            "attributes": ["role=admin", "clearance=gold"],
        },
        {
            "username": "gold",
            "password": "password",
            "attributes": [
                "role=user",
                "clearance=gold",
                "team=frontend",
                "team=backend",
                "team=devops",
            ],
        },
        {
            "username": "silver",
            "password": "password",
            "attributes": [
                "role=user",
                "clearance=silver",
                "team=frontend",
            ],
        },
        {
            "username": "bronze",
            "password": "password",
            "attributes": [
                "role=user",
                "clearance=bronze",
                "team=devops",
            ],
        },
        {
            "username": "guest",
            "password": "password",
            "attributes": [],
        },
    ]

    for user_data in sample_users:
        user = User(**user_data)
        db.session.add(user)

    db.session.commit()


if __name__ == "__main__":
    db_file = os.path.abspath(os.path.join(app.instance_path, DATABASE_FILE))
    if not os.path.exists(db_file):
        with app.app_context():
            db.create_all()
            print("Database created:", db_file)
            load_sample_users()
            print("Sample users added to the database.")

    print(__doc__)
    app.run(debug=True, host="0.0.0.0", port=8080)
