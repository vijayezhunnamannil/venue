from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from datetime import datetime
import pandas as pd
import io
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Initialize database
def init_db():
    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            venue TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            purpose TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        name = request.form['name']
        venue = request.form['venue']
        date = request.form['date']
        time = request.form['time']
        purpose = request.form['purpose']

        conn = sqlite3.connect('bookings.db')
        c = conn.cursor()
        c.execute("INSERT INTO bookings (name, venue, date, time, purpose) VALUES (?, ?, ?, ?, ?)",
                  (name, venue, date, time, purpose))
        conn.commit()
        conn.close()

        flash('Venue booked successfully!')
        return redirect(url_for('index'))

    return render_template('book.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('admin_login'))

    return render_template('login.html')

@app.route('/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bookings ORDER BY date DESC")
    bookings = c.fetchall()
    conn.close()
    return render_template('bookings.html', bookings=bookings)

@app.route('/export')
def export_excel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('bookings.db')
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bookings')

    output.seek(0)
    return send_file(output, download_name="venue_bookings.xlsx", as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
