from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import bcrypt
import sqlite3
import os

app = Flask(__name__)

load_dotenv(dotenv_path="secret.env")
app.secret_key = os.environ.get('SECRET_KEY')

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL)''')

cur.execute('''CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT NOT NULL,
            color TEXT NOT NULL,
            assignment TEXT NOT NULL,
            assignment_desc TEXT NOT NULL,
            due_date TEXT NOT NULL
)''')

conn.commit()
conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    session.clear()
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username = ?', (username,))
        try:
            hashed = cur.fetchone()[0]
        except TypeError:
            return render_template('login.html', login_error=True)
        if bcrypt.hashpw(password, hashed) == hashed:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', login_error=True)
        return render_template('login.html', login_error=False)
    return render_template('login.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form['username']
        if ' ' in username:
            return render_template('create_account.html', error='Username cannot contain spaces')
        if not(username.isalnum()):
            return render_template('create_account.html', error='Username is not alphanumeric.')
        password = request.form['password'].encode('utf-8')
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT username FROM users WHERE username = ?', [username])
        if len(cur.fetchall()) > 0:
            return render_template('create_account.html', error='Username is already taken')
        if username == '':
            return render_template('create_account.html', error='Username cannot be blank')
        if ' ' in password.decode('utf-8'):
            return render_template('create_account.html', error='Password cannot contain spaces')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        print(salt, hashed)
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('create_account.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    # prevents users from just directly accessing "/home"
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'logout' in request.form:
            return redirect(url_for('logout'))
        if 'remove-assignment' in request.form:
            session['assignment_id'] = request.form['remove-assignment']
            print('assignment-id:', request.form['remove-assignment'])
            return redirect(url_for('remove_assignment'))
        return redirect(url_for('add_assignment'))
    username = session['username']
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE username=?', [username])
    user_id = cur.fetchall()[0][0]
    print('user id:', user_id)
    cur.execute('SELECT assignment_id, subject, color, assignment, assignment_desc, due_date FROM assignments WHERE user_id=?', [user_id])
    assignment_list = cur.fetchall()
    print(assignment_list)
    return render_template('home.html', username=username, assignment_list=assignment_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_assignment', methods=['GET', 'POST'])
def add_assignment():
    if request.method == 'POST':
        subject = request.form['subject']
        color = request.form['color']
        assignment = request.form['assignment']
        assignment_desc = request.form['assignment_desc']
        due_date = request.form['due_date']
        username = session['username']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM users WHERE username=?', [username])
        user_id = cur.fetchall()[0][0]
        cur.execute('INSERT INTO assignments(user_id, subject, color, assignment, assignment_desc, due_date) VALUES (?, ?, ?, ?, ?, ?)', (user_id, subject, color, assignment, assignment_desc, due_date))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add_assignment.html')

@app.route('/remove_assignment')
def remove_assignment():
    assignment_id = session['assignment_id']
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM assignments WHERE assignment_id=?', [assignment_id])
    conn.commit()
    conn.close()
    session.pop('assignment_id')
    return redirect(url_for('home'))

app.run(debug=True)