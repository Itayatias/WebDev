from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'Itay2503'  # Needed for session

DATABASE = 'Database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return render_template('Manager/dashboard.html', username=user['username'])
        elif user['role'] == 'customer':
            return render_template('customer/dashboard.html', username=user['username'])
        else:
            flash('Role not recognized.')
            return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("You must create and populate Database.db with a 'users' table including 'username', 'password', 'role'.")
    app.run(debug=True)
