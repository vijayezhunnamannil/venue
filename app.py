from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from datetime import datetime
import pandas as pd
import io

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
            email TEXT NOT NULL,
            venue TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT NOT NULL
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
        email = request.form['email']
        venue = request.form['venue']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        purpose = request.form['purpose']

        conn = sqlite3.connect('bookings.db')
        c = conn.cursor()

        # Conflict check
        c.execute("""SELECT * FROM bookings WHERE venue = ? AND date = ? AND (
                        (? BETWEEN start_time AND end_time) OR
                        (? BETWEEN start_time AND end_time) OR
                        (start_time BETWEEN ? AND ?) OR
                        (end_time BETWEEN ? AND ?)
                    )""",
                  (venue, date, start_time, end_time, start_time, end_time, start_time, end_time))
        conflicts = c.fetchall()

        if conflicts:
            flash('Venue is already booked for the selected time.', 'danger')
        else:
            c.execute("""INSERT INTO bookings (name, email, venue, date, start_time, end_time, purpose)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (name, email, venue, date, start_time, end_time, purpose))
            conn.commit()
            flash('Venue booked successfully!', 'success')

        conn.close()
        return redirect(url_for('book'))

    return render_template('book.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('view_bookings'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/bookings')
def view_bookings():
    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('bookings.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bookings ORDER BY date, start_time')
    bookings = c.fetchall()
    conn.close()
    return render_template('bookings.html', bookings=bookings)

@app.route('/export')
def export_bookings():
    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('bookings.db')
    df = pd.read_sql_query("SELECT * FROM bookings ORDER BY date, start_time", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bookings')

    output.seek(0)
    return send_file(output, download_name='bookings.xlsx', as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
