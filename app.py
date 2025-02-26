from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import secrets
import datetime
from email.mime.text import MIMEText
import hashlib
import smtplib

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/Login"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Access the database
db = mongo.db  # This gives access to the "newdb" database

users_collection = db.users  # Access "users" collection (like a table)

# Flask-Mail Configuration (Use a real SMTP server)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False  # Make sure this is False
app.config["MAIL_DEFAULT_SENDER"] = "kangethealex5972@gmail.com"
app.config["MAIL_USERNAME"] = "kangethealex5972@gmail.com"
app.config["MAIL_PASSWORD"] = "furt btzz bfce kvdn"  # Use the 16-character App Password here
mail = Mail(app)

EMAIL = "kangethealex4972@gmail.com"
PASSWORD = "furt btzz bfce kvdn"  # Use the 16-character App Password here

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    print("✅ SMTP login successful!")
    server.quit()
except Exception as e:
    print(f"❌ SMTP error: {e}")

# --- ROUTES ---
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if user exists
        if mongo.db.users.find_one({"username": username}):
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        mongo.db.users.insert_one({"username": username, "email": email, "password": hashed_password})

        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = mongo.db.users.find_one({"username": username})
        
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

# Function to send password reset email
def send_reset_email(email, token):
    reset_link = url_for("reset_password", token=token, _external=True)
    subject = "Password Reset Request"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\nThis link will expire in 1 hour."

    try:
        msg = Message(subject, sender=app.config["MAIL_DEFAULT_SENDER"], recipients=[email])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_reset_token(email):
    """Generate a unique token for password reset and store it in a separate collection."""
    token = secrets.token_hex(16)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Store the token in a separate collection
    mongo.db.password_resets.insert_one({
        "email": email,
        "reset_token": token,
        "token_expiry": expiration_time
    })

    print(f"Generated Token: {token} for {email}")  # Debugging line
    return token

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = mongo.db.users.find_one({"email": email})

        if user:
            reset_token = generate_reset_token(email)  # Use the new function
            reset_link = url_for("reset_password", token=reset_token, _external=True)

            msg = Message("Password Reset", sender=app.config["MAIL_USERNAME"], recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_link}"
            mail.send(msg)

            flash("Password reset link sent to your email.", "success")
        else:
            flash("Email not found.", "danger")

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset_entry = mongo.db.password_resets.find_one({"reset_token": token})

    if not reset_entry:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for("login"))

    # Check if the token has expired
    if datetime.datetime.utcnow() > reset_entry["token_expiry"]:
        flash("Token has expired. Please request a new reset link.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        
        # Update user password
        mongo.db.users.update_one(
            {"email": reset_entry["email"]}, 
            {"$set": {"password": new_password}}
        )

        # Delete the reset token after use
        mongo.db.password_resets.delete_one({"reset_token": token})

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)



@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        contact = {
            "phone": request.form["phone"],
            "email": request.form["email"],
            "address": request.form["address"],
            "reg_number": request.form["reg_number"]
        }
        mongo.db.contacts.insert_one(contact)
        flash("Contact saved successfully!", "success")

    return render_template("dashboard.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    contact = None
    if request.method == "POST":
        reg_number = request.form["reg_number"]
        contact = mongo.db.contacts.find_one({"reg_number": reg_number})

        if not contact:
            flash("No contact found with this registration number.", "warning")

    return render_template("search.html", contact=contact)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
