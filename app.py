from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import os
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database Configuration
db_config = {
    'host': os.environ.get('MYSQL_HOST', 'db'),
    'user': os.environ.get('MYSQL_USER', 'bank_user'),
    'password': os.environ.get('MYSQL_PASSWORD', 'your_password'),
    'database': os.environ.get('MYSQL_DB', 'banking_db')
}

def get_db_connection():
    """Establish and return a database connection"""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "Database starting... please refresh in 10 seconds.", 503
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    # Debugging: This will print the data in your Docker logs
    print(f"Fetched from DB: {customers}")

    cursor.close()
    conn.close()
    return render_template('index.html', customers=customers)

@app.route('/create', methods=['POST'])
def create():
    name = request.form['name']
    acc_num = request.form['acc_num']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO customers (name, account_number, balance) VALUES (%s, %s, 0)", (name, acc_num))
            conn.commit()
            flash("Customer Created Successfully!")
        except Error as e:
            flash(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('index'))

@app.route('/transaction', methods=['POST'])
def transaction():
    acc_num = request.form['acc_num']
    amount = float(request.form['amount'])
    action = request.form['action']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT balance FROM customers WHERE account_number = %s", [acc_num])
        result = cursor.fetchone()

        if result:
            current_balance = float(result['balance'])
            new_balance = current_balance + amount if action == 'deposit' else current_balance - amount
            
            if new_balance < 0:
                flash("Insufficient Funds!")
            else:
                cursor.execute("UPDATE customers SET balance = %s WHERE account_number = %s", (new_balance, acc_num))
                conn.commit()
                flash(f"{action.capitalize()} Successful!")
        else:
            flash("Account Not Found!")
        
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Initial wait to let MySQL container finish its internal setup
    print("Application starting... waiting 15 seconds for DB to stabilize.")
    time.sleep(15) 
    app.run(host='0.0.0.0', port=5000)
