from flask import Flask, render_template, request, redirect, session, send_file
from sqlalchemy import create_engine, text
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL connection (use your Render external DB URL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ajay_user:emG6rfDDpoppKsmYfOvz5H50vtvuEIhk@dpg-d18eqejuibrs73cvfr80-a.oregon-postgres.render.com/ajaybabupadamatiaj")
engine = create_engine(DATABASE_URL)

# Home/Login Page
@app.route('/')
def home():
    return render_template('login.html')

# Handle Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    with engine.connect() as conn:
        user = conn.execute(text('SELECT * FROM users WHERE username = :u AND password = :p'), {"u": username, "p": password}).fetchone()
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
        with engine.begin() as conn:
            existing_user = conn.execute(text("SELECT * FROM users WHERE username = :u"), {"u": username}).fetchone()
            if existing_user:
                return "User already exists. <a href='/'>Login</a>"
            conn.execute(text("INSERT INTO users (username, password) VALUES (:u, :p)"), {"u": username, "p": password})
        return redirect('/')
    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    with engine.connect() as conn:
        tasks = conn.execute(text('SELECT * FROM tasks WHERE user = :u'), {"u": session['user']}).fetchall()
    return render_template('dashboard.html', tasks=tasks)

# Add Task
@app.route('/add-task', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect('/')
    task = request.form['task']
    with engine.begin() as conn:
        conn.execute(text('INSERT INTO tasks (task, user, status) VALUES (:t, :u, :s)'), {"t": task, "u": session['user'], "s": 'Pending'})
    return redirect('/dashboard')

# Mark task as done
@app.route('/mark-done/<int:task_id>')
def mark_done(task_id):
    if 'user' not in session:
        return redirect('/')
    with engine.begin() as conn:
        conn.execute(text("UPDATE tasks SET status = 'Done' WHERE id = :id AND user = :u"), {"id": task_id, "u": session['user']})
    return redirect('/dashboard')

# Delete task
@app.route('/delete-task/<int:task_id>')
def delete_task(task_id):
    if 'user' not in session:
        return redirect('/')
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM tasks WHERE id = :id AND user = :u'), {"id": task_id, "u": session['user']})
    return redirect('/dashboard')

# Edit Task
@app.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user' not in session:
        return redirect('/')
    if request.method == 'POST':
        new_task = request.form['task']
        with engine.begin() as conn:
            conn.execute(text('UPDATE tasks SET task = :task WHERE id = :id AND user = :u'), {"task": new_task, "id": task_id, "u": session['user']})
        return redirect('/dashboard')
    with engine.connect() as conn:
        task = conn.execute(text('SELECT * FROM tasks WHERE id = :id AND user = :u'), {"id": task_id, "u": session['user']}).fetchone()
    return render_template('edit_task.html', task=task)

# Export to Excel
@app.route('/export')
def export():
    if 'user' not in session:
        return redirect('/')
    with engine.connect() as conn:
        tasks = conn.execute(text('SELECT task, status FROM tasks WHERE user = :u'), {"u": session['user']}).fetchall()
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

if __name__ == '__main__':
    app.run(debug=True)
