from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
from io import BytesIO
import os  # Added to use PORT from environment

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home/Login Page
@app.route('/')
def home():
    return render_template('login.html')

# Handle Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if user:
        session['user'] = username
        return redirect('/dashboard')
    return 'Invalid credentials. <a href="/">Try again</a>'

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        existing_user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            conn.close()
            return "User already exists. <a href='/'>Login</a>"

        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user = ?', (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

# Add Task
@app.route('/add-task', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect('/')
    task = request.form['task']
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (task, user, status) VALUES (?, ?, ?)', (task, session['user'], 'Pending'))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Mark task as done
@app.route('/mark-done/<int:task_id>')
def mark_done(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    conn.execute("UPDATE tasks SET status = 'Done' WHERE id = ? AND user = ?", (task_id, session['user']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Delete task
@app.route('/delete-task/<int:task_id>')
def delete_task(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ? AND user = ?', (task_id, session['user']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Edit Task
@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    if request.method == 'POST':
        new_task = request.form['task']
        conn.execute('UPDATE tasks SET task = ? WHERE id = ? AND user = ?', (new_task, task_id, session['user']))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    task = conn.execute('SELECT * FROM tasks WHERE id = ? AND user = ?', (task_id, session['user'])).fetchone()
    conn.close()
    return render_template('edit_task.html', task=task)

# Export to Excel
@app.route('/export')
def export():
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    tasks = conn.execute('SELECT task, status FROM tasks WHERE user = ?', (session['user'],)).fetchall()
    conn.close()

    df = pd.DataFrame(tasks, columns=['Task', 'Status'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='tasks.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ✅ UPDATED: Use dynamic PORT and public HOST
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
