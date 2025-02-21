from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/Login"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Flask-Mail Configuration (Use a real SMTP server)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_DEFAULT_SENDER"] = "kangethealex5972@gmail.com"
app.config["MAIL_USERNAME"] = "kangethealex5972@gmail.com"
app.config["MAIL_PASSWORD"] = "jcrg nlxw jvlv hbhu"
mail = Mail(app)

# --- ROUTES ---
@app.route("/", methods=["GET", "POST"])
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

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = mongo.db.users.find_one({"email": email})

        if user:
            reset_token = secrets.token_hex(16)
            mongo.db.users.update_one({"email": email}, {"$set": {"reset_token": reset_token}})
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
    user = mongo.db.users.find_one({"reset_token": token})

    if not user:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        mongo.db.users.update_one({"reset_token": token}, {"$set": {"password": new_password, "reset_token": None}})
        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/register", methods=["GET", "POST"])
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
