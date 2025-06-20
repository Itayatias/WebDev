from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

contact_bp = Blueprint('contact', __name__)

DATABASE = 'Database.db'

@contact_bp.route('/customer/contact', methods=['POST'])
def customer_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # Save the message to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)
    ''', (name, email, message))
    conn.commit()
    conn.close()

    flash('Your message has been sent! Thank you for contacting us.', 'contact')
    return redirect(url_for('customer_homepage'))

# Optional: If you want to serve the customer home page from here as well
@contact_bp.route('/customer/home')
def customer_homepage():
    return render_template('Customer/customerHomePage.html')