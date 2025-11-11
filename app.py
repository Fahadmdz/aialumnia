from flask import Flask, render_template, request, redirect, url_for, session
import os
import mysql.connector
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'super_secret_key'

# Ensure uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password_here'
mail = Mail(app)

# Database connection

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="your_mysql_user",
        password="your_mysql_password",
        database="ailumina_db"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        msg = Message('AiLumina - Contact Message',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['your_email@gmail.com'])
        msg.body = f"From: {name} <{email}>\n\nMessage:\n{message}"

        try:
            mail.send(msg)
        except Exception as e:
            print("Email Error:", e)

        return render_template('message.html', message="Thank you for contacting us!")
    return render_template('contact.html')

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        use_case = request.form.get('use_case')
        file = request.files.get('cv')

        saved_filename = None
        if file and file.filename:
            saved_filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
            file.save(file_path)

        msg = Message('AiLumina - New Join Request',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['your_email@gmail.com'])
        msg.body = f"""
Name: {name}
Role: {role}
Use Case: {use_case}
File Attached: {"Yes - " + saved_filename if saved_filename else "No"}
"""

        try:
            mail.send(msg)
        except Exception as e:
            print("Email Error:", e)

        return render_template('message.html', message="Thank you for your submission!")
    return render_template('join.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
            conn.commit()
            conn.close()

            msg = Message('Welcome to AiLumina!', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Hello {name},\n\nThank you for registering at AiLumina."
            mail.send(msg)
            return redirect('/login')
        except mysql.connector.Error as err:
            return render_template('register.html', error=f"Error: {err.msg}")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, password FROM users WHERE email=%s", (email,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password_hash(result[1], password):
            session['user'] = result[0]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', name=session['user'])
    return redirect('/login')

@app.route('/admin')
def admin():
    if 'user' in session and session['user'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        conn.close()
        return render_template('admin_dashboard.html', users=users)
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

