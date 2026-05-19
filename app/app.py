from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "todo-app-gizli-anahtar"

# MySQL bağlantı ayarları
DB_HOST = os.environ.get('DB_HOST', 'todo-db-service')
DB_USER = 'root'
DB_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD', 'todo123')
DB_NAME = os.environ.get('MYSQL_DATABASE', 'tododb')

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Todos tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Tabloları oluştur
init_db()

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            return "Şifreler eşleşmiyor!", 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return "Bu kullanıcı adı zaten alınmış!", 400
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return "Bu e-posta zaten kayıtlı!", 400
        
        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s)", 
                      (email, username, hashed))
        conn.commit()
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or user['password'] != hash_password(password):
            return "Geçersiz e-posta veya şifre!", 400
        
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    filter_type = request.args.get('filter', 'all')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if filter_type == 'active':
        cursor.execute("SELECT * FROM todos WHERE user_id = %s AND completed = 0 ORDER BY created_at DESC", 
                      (session['user_id'],))
    elif filter_type == 'completed':
        cursor.execute("SELECT * FROM todos WHERE user_id = %s AND completed = 1 ORDER BY created_at DESC", 
                      (session['user_id'],))
    else:
        cursor.execute("SELECT * FROM todos WHERE user_id = %s ORDER BY created_at DESC", 
                      (session['user_id'],))
    
    todos = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', todos=todos, filter=filter_type, username=session.get('username'))

@app.route('/add-todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmalısınız"}), 401
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    if not title:
        return jsonify({"error": "Başlık gerekli"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO todos (user_id, title, description) VALUES (%s, %s, %s)",
                  (session['user_id'], title, description))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/toggle-todo/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmalısınız"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET completed = NOT completed WHERE id = %s AND user_id = %s",
                  (todo_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/delete-todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmalısınız"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = %s AND user_id = %s",
                  (todo_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/edit-todo/<int:todo_id>', methods=['POST'])
def edit_todo(todo_id):
    if 'user_id' not in session:
        return jsonify({"error": "Giriş yapmalısınız"}), 401
    
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET title = %s, description = %s WHERE id = %s AND user_id = %s",
                  (title, description, todo_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        conn = get_db()
        cursor = conn.cursor()
        
        if action == 'update_email':
            new_email = request.form.get('email')
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", 
                          (new_email, session['user_id']))
            session['user_email'] = new_email
            conn.commit()
        
        elif action == 'change_password':
            current = request.form.get('current_password')
            new_pass = request.form.get('new_password')
            confirm = request.form.get('confirm_password')
            
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            
            if user['password'] != hash_password(current):
                conn.close()
                return "Mevcut şifre yanlış!", 400
            
            if new_pass != confirm:
                conn.close()
                return "Yeni şifreler eşleşmiyor!", 400
            
            cursor.execute("UPDATE users SET password = %s WHERE id = %s",
                          (hash_password(new_pass), session['user_id']))
            conn.commit()
        
        conn.close()
        return redirect(url_for('profile'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, username, created_at FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as completed FROM todos WHERE user_id = %s AND completed = 1", 
                  (session['user_id'],))
    completed = cursor.fetchone()
    conn.close()
    
    return render_template('profile.html', user=user, completed_count=completed['completed'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
