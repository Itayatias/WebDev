from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

register_bp = Blueprint('register', __name__)

DATABASE = 'Database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        # בדיקה אם המשתמש או האימייל כבר קיימים
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username or email already exists.')
            conn.close()
            return render_template('register.html')

        # הוספת המשתמש החדש עם role=customer
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (username, email, password, 'customer')
        )
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.')
        return redirect(url_for('home'))

    return render_template('register.html')