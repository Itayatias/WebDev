from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import uuid
import time
import sqlite3
import os
import requests

app = Flask(__name__)
app.secret_key = 'Itay2503'  # Needed for session
 
 # חיבור למסד הנתונים
DATABASE = 'Database.db'
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# שליחת קבצי תבנית
# מציגה את דף הבית הראשי של האתר.
@app.route('/')
def home():
    return render_template('index.html')


# התחברות למערכת
# מבצעת התחברות של משתמש, בודקת פרטי משתמש ומפנה לדשבורד או לדף לקוח.
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM orders')
            total_orders = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM users WHERE role="customer"')
            total_clients = cursor.fetchone()[0]
            cursor.execute('SELECT orderID, orderDateTime, customerName, totalOrder, status FROM orders')
            orders = cursor.fetchall()
            SumOrders = cursor.execute('SELECT SUM(totalOrder) FROM orders')
            total_sum_orders = SumOrders.fetchone() if SumOrders.fetchone() is not None else 0
            
            conn.close()
            return render_template('Manager/dashboard.html', username=user['username'], total_orders=total_orders, total_clients=total_clients, orders=orders, total_sum_orders=total_sum_orders)
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

# יצירת קשר

# יצירת קשר - שמירת פנייה למסד הנתונים
@app.route('/contact/customer_contact', methods=['POST'])
def customer_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    if not name or not email or not message:
        flash('All fields are required.', 'contact')
        return redirect(url_for('customer_home'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ContactCustomers (Name, Email, Massage) VALUES (?, ?, ?)', (name, email, message))
    conn.commit()
    conn.close()
    flash('Your message has been sent!', 'contact')
    return redirect(url_for('customer_home'))


 # מנתקת את המשתמש ומחזירה לדף הבית.
@app.route('/customer/home')
def customer_home():
    return render_template('Customer/customerHomePage.html')


# מציגה את דף החנות ללקוח.
@app.route('/customer/shop')
def customer_shop():
    return render_template('Customer/customerStore.html')


# מציגה את דף "אודות" ללקוח.
@app.route('/customer/about')
def about_us():
    return render_template('Customer/aboutUs.html')


# מוסיפה מוצר לעגלת הקניות של המשתמש במסד הנתונים.
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


# מחזירה את כל המוצרים שנמצאים בעגלת הקניות של המשתמש.
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


# מעדכנת את הכמות של מוצר בעגלת הקניות או מסירה אותו אם הכמות אפס.
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



# מסירה מוצר מסוים מעגלת הקניות של המשתמש.
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



# יוצרת הזמנה חדשה מהפריטים שבעגלה ומנקה את העגלה לאחר מכן.
@app.route('/create_order', methods=['POST'])
def create_order():
    user = session.get('username')
    if not user:
        return jsonify({'message': 'User not logged in'}), 401

    try:
        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()

        # שליפת כל המוצרים בסל של המשתמש
        cursor.execute('SELECT productName, quantity, price FROM carts WHERE user=?', (user,))
        cart_items = cursor.fetchall()

        if not cart_items:
            conn.close()
            return jsonify({'message': 'Cart is empty'}), 400

        # חישוב סכום כולל
        total = 0
        order_quantity = 0
        status = 'Pending'
        for productName, quantity, price in cart_items:
            try:
                # הסר סימן דולר אם קיים והמר למספר
                price_num = float(str(price).replace('$', '').strip())
                total += price_num * int(quantity)
                order_quantity += int(quantity)
            except Exception as e:
                print(f"Error parsing price for {productName}: {e}")

        # יצירת מזהה הזמנה וזמן
        order_id = str(uuid.uuid4())
        order_datetime = int(time.time())
        customer_name = user

        # הכנסת ההזמנה לטבלת orders
        cursor.execute('''
            INSERT INTO orders (orderID, orderDateTime, customerName, totalOrder, quantity, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, order_datetime, customer_name, int(total), order_quantity, status))

        # ניקוי הסל של המשתמש
        cursor.execute('DELETE FROM carts WHERE user=?', (user,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Order created successfully!', 'orderID': order_id})

    except Exception as e:
        print("Error creating order:", e)
        return jsonify({'message': 'Error creating order'}), 500
    



# מציג את דשבורד הניהול עם נתונים סטטיסטיים על הזמנות, לקוחות ומוצרים.
@app.route('/manager/dashboard')
def manager_dashboard():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    # שליפת סך כל הכמויות שנמכרו מתוך orders
    cursor.execute('SELECT SUM(quantity) FROM orders')
    total_products_sold = cursor.fetchone()[0] or 0
    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users')
    total_clients = cursor.fetchone()[0]
    cursor.execute('SELECT orderID, orderDateTime, customerName, totalOrder,quantity, status FROM orders')
    orders = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = ?', ('In Progress',))
    in_progress_orders = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(totalOrder) FROM orders')
    total_income = cursor.fetchone()[0] or 0
    cursor.execute('SELECT SUM(expense) FROM expenses')
    total_expenses = cursor.fetchone()[0] or 0
    # חישוב אחוזים (דוגמה, שנה לפי הצורך)
    income_target = int((total_income / 10000) * 100) if total_income else 0
    expenses_target = int((total_expenses / 10000) * 100) if total_expenses else 0
    totals_target = int(((total_income - total_expenses) / 10000) * 100) if (total_income - total_expenses) else 0

    # שליפת כל הפניות מהלקוחות
    cursor.execute('SELECT Name, Email, Massage FROM ContactCustomers')
    contact_messages = cursor.fetchall()
    conn.close()
    return render_template(
        'Manager/dashboard.html',
        total_products_sold=total_products_sold,
        total_orders=total_orders,
        total_clients=total_clients,
        orders=orders,
        in_progress_orders=in_progress_orders,
        income_target=income_target,
        total_income=total_income,
        expenses_target=expenses_target,
        total_expenses=total_expenses,
        totals_target=totals_target,
        contact_messages=contact_messages,
        username=session.get('username')
    )

# מעדכן את סטטוס ההזמנה לפי בחירת המנהל.
@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    order_id = request.form['orderID']
    status = request.form['status']
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status=? WHERE orderID=?', (status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('manager_dashboard'))



# משמש כפרוקסי לשליחת שאלות לשרת Ollama ומחזיר תשובת AI.
@app.route('/ollama_proxy', methods=['POST'])
def ollama_proxy():
    from flask import request, jsonify, session
    import requests
    if not session.get('username'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    r = requests.post('http://localhost:11434/api/generate', json=data)
    return r.text, r.status_code, {'Content-Type': 'text/plain'}


# הרצה
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("You must create and populate Database.db with a 'users' table including 'username', 'password', 'role'.")
    app.run(debug=True)
