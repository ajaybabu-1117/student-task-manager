from flask import Flask, render_template, request, redirect, session, send_file
import psycopg2
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = '72c7baeb30d86401bed44ff643471726'

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        task TEXT NOT NULL,
        "user" TEXT NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['user'] = username
        return redirect('/dashboard')
    return 'Invalid credentials. <a href="/">Try again</a>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return "User already exists. <a href='/'>Login</a>"
        cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, task, status FROM tasks WHERE "user" = %s', (session['user'],))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', tasks=[{'id': t[0], 'task': t[1], 'status': t[2]} for t in tasks])

@app.route('/add-task', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect('/')
    task = request.form['task']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO tasks (task, "user", status) VALUES (%s, %s, %s)', (task, session['user'], 'Pending'))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/mark-done/<int:task_id>')
def mark_done(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = 'Done' WHERE id = %s AND \"user\" = %s", (task_id, session['user']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete-task/<int:task_id>')
def delete_task(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM tasks WHERE id = %s AND "user" = %s', (task_id, session['user']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/dashboard')

@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        new_task = request.form['task']
        cur.execute('UPDATE tasks SET task = %s WHERE id = %s AND "user" = %s', (new_task, task_id, session['user']))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/dashboard')
    cur.execute('SELECT id, task FROM tasks WHERE id = %s AND "user" = %s', (task_id, session['user']))
    task = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_task.html', task={'id': task[0], 'task': task[1]})

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT task, status FROM tasks WHERE "user" = %s', (session['user'],))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    df = pd.DataFrame(rows, columns=['Task', 'Status'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='tasks.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
