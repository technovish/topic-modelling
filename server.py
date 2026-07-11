from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import os
import topic_analysis
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'comments.db')
DB_PORT = os.getenv('DB_PORT', '3306')

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=int(DB_PORT)
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = 'super_secret_key_for_this_demo_only_change_in_production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not password or not confirm_password:
            return "All fields are required.", 400
            
        if password != confirm_password:
            return "Passwords do not match.", 400
            
        if len(password) < 6:
            return "Password must be at least 6 characters long.", 400
            
        import re
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            return "Invalid email address format.", 400
            
        conn = get_db_connection()
        if not conn:
            return "Database connection error. Please try again later.", 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return "A user with this email already exists.", 409
                
            # Create new user
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, hashed_pw)
            )
            conn.commit()
            
            return redirect(url_for('login', registered='true'))
            
        except mysql.connector.Error as err:
            print(f"Database error during registration: {err}")
            return "An internal database error occurred.", 500
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    return send_from_directory('.', 'register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            return "Database connection error. Please try again later.", 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user'] = email
                return redirect(url_for('index'))
            else:
                return send_from_directory('.', 'invalid.html'), 401
        except mysql.connector.Error as err:
            print(f"Database error during login: {err}")
            return "An internal database error occurred.", 500
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    return send_from_directory('.', 'login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    return send_from_directory('.', 'index.html')

@app.route('/results')
def results():
    if not session.get('user'):
        return redirect(url_for('login'))
    return send_from_directory('.', 'results.html')

@app.route('/chart.png')
def serve_chart():
    if not session.get('user'):
        return redirect(url_for('login'))
    return send_from_directory('.', 'chart.png')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Trigger topic analysis
        try:
            # We are running this synchronously for now. 
            # For large files, this should be a background task (e.g., Celery/Redis Queue).
            result_df = topic_analysis.analyze_file(filepath)
            
            if result_df is not None:
                rows_count = len(result_df)
                return jsonify({'message': 'File uploaded and analyzed successfully', 'rows': rows_count}), 200
            else:
                 return jsonify({'message': 'File uploaded but analysis failed', 'rows': 0}), 500

        except Exception as e:
            print(f"Error during analysis: {e}")
            return jsonify({'message': 'File uploaded but error during analysis', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
