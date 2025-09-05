from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import uuid
import time
import sqlite3
import os


app = Flask(__name__)
app.secret_key = 'Itay2503'  # Needed for session

DATABASE = 'Database.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# שליחת קבצי תבנית
@app.route('/')
def home():
    return render_template('index.html')


# התחברות למערכת
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
            return render_template('customer/customerHomePage.html', username=user['username'])
        else:
            flash('Role not recognized.')
            return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('home'))

# התנתקות מהמערכת
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# הרשמה למערכת
from Controller.register import register_bp
app.register_blueprint(register_bp)


from Controller.contact import contact_bp
app.register_blueprint(contact_bp)

@app.route('/customer/home')
def customer_home():
    return render_template('Customer/customerHomePage.html')

@app.route('/customer/shop')
def customer_shop():
    return render_template('Customer/customerStore.html')

@app.route('/customer/about')
def about_us():
    return render_template('Customer/aboutUs.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_name = data.get('productName')
    price = data.get('price')
    quantity = int(data.get('quantity', 1))
    user = session.get('username')

    if not user:
        return jsonify({'message': 'User not logged in'}), 401

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT quantity FROM carts WHERE user=? AND productName=?', (user, product_name))
    row = cursor.fetchone()
    if row:
        # עדכן כמות קיימת
        cursor.execute('UPDATE carts SET quantity = quantity + ? WHERE user=? AND productName=?',
                       (quantity, user, product_name))
    else:
        # הוסף מוצר חדש עם הכמות שנבחרה
        cursor.execute('INSERT INTO carts (user, productName, quantity, price) VALUES (?, ?, ?, ?)',
                       (user, product_name, quantity, price))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added to cart!'})

@app.route('/get_cart', methods=['GET'])
def get_cart():
    user = session.get('username')
    if not user:
        return jsonify({'cart': []})
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT productName, quantity, price FROM carts WHERE user=?', (user,))
    cart_items = [
        {
            'productName': row[0],
            'quantity': row[1],
            'price': row[2]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify({'cart': cart_items})

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    user = session.get('username')
    product_name = data.get('productName')
    delta = int(data.get('delta', 0))
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT quantity FROM carts WHERE user=? AND productName=?', (user, product_name))
    row = cursor.fetchone()
    if row:
        new_quantity = row[0] + delta
        if new_quantity > 0:
            cursor.execute('UPDATE carts SET quantity=? WHERE user=? AND productName=?',
                           (new_quantity, user, product_name))
        else:
            cursor.execute('DELETE FROM carts WHERE user=? AND productName=?',
                           (user, product_name))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Cart updated'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    user = session.get('username')
    product_name = data.get('productName')
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM carts WHERE user=? AND productName=?', (user, product_name))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product removed'})

import uuid
import time

@app.route('/create_order', methods=['POST'])
def create_order():
    user = session.get('username')
    if not user:
        return jsonify({'message': 'User not logged in'}), 401

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    # שליפת סכום כולל מהסל
    cursor.execute('SELECT price, quantity FROM carts WHERE user=?', (user,))
    rows = cursor.fetchall()
    total = 0
    for price, quantity in rows:
        try:
            total += float(price) * int(quantity)
        except Exception:
            continue
    if total == 0:
        conn.close()
        return jsonify({'message': 'Cart is empty'}), 400

    # יצירת מספר הזמנה ייחודי
    order_id = str(uuid.uuid4())
    order_datetime = int(time.time())
    customer_name = user

    # הכנסת ההזמנה לטבלה orders
    cursor.execute('''
        INSERT INTO orders (orderID, orderDateTime, customerName, totalOrder)
        VALUES (?, ?, ?, ?)
    ''', (order_id, order_datetime, customer_name, int(total)))

    # ריקון הסל של המשתמש
    cursor.execute('DELETE FROM carts WHERE user=?', (user,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Order created successfully!', 'orderID': order_id})

# הרצה
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("You must create and populate Database.db with a 'users' table including 'username', 'password', 'role'.")
    app.run(debug=True)
