
from flask import Flask, render_template
import sqlite3


app = Flask(__name__)
DATABASE = 'Database.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def login():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def do_login():
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
        return redirect(url_for('dashboard'))  # redirect after successful login
    else:
        flash('Invalid username or password')
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
