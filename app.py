from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
    count = data.get('count', 1)
    size = data.get('size')
    price = data.get('price')
    user = session.get('username')  # ודא שהמשתמש שמור ב-session

    if not user:
        return jsonify({'message': 'User not logged in'}), 401

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    # בדוק אם המוצר כבר קיים בסל של המשתמש (כולל מידה)
    cursor.execute('SELECT countOfProducts FROM carts WHERE user=? AND productName=? AND size=?', (user, product_name, size))
    row = cursor.fetchone()
    if row:
        # עדכן כמות
        cursor.execute('UPDATE carts SET countOfProducts = countOfProducts + ? WHERE user=? AND productName=? AND size=?',
                       (count, user, product_name, size))
    else:
        # הוסף מוצר חדש לסל
        cursor.execute('INSERT INTO carts (user, productName, size, price, countOfProducts) VALUES (?, ?, ?, ?, ?)',
                       (user, product_name, size, price, count))
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
    cursor.execute('SELECT productName, size, price, countOfProducts FROM carts WHERE user=?', (user,))
    cart_items = [
        {
            'productName': row[0],
            'size': row[1],
            'price': row[2],
            'count': row[3]
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
    size = data.get('size')
    delta = int(data.get('delta', 0))
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    # עדכן כמות, אם מגיע ל-0 מחק את המוצר
    cursor.execute('SELECT countOfProducts FROM carts WHERE user=? AND productName=? AND size=?', (user, product_name, size))
    row = cursor.fetchone()
    if row:
        new_count = row[0] + delta
        if new_count > 0:
            cursor.execute('UPDATE carts SET countOfProducts=? WHERE user=? AND productName=? AND size=?',
                           (new_count, user, product_name, size))
        else:
            cursor.execute('DELETE FROM carts WHERE user=? AND productName=? AND size=?',
                           (user, product_name, size))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Cart updated'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    user = session.get('username')
    product_name = data.get('productName')
    size = data.get('size')
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM carts WHERE user=? AND productName=? AND size=?', (user, product_name, size))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product removed'})


# הרצה
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("You must create and populate Database.db with a 'users' table including 'username', 'password', 'role'.")
    app.run(debug=True)
