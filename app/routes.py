from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, send_from_directory, current_app
import os
import re
from werkzeug.security import check_password_hash, generate_password_hash
from google.cloud import storage
import mysql.connector

# Import the database connection helper and the analysis function
from app.database import get_db_connection
from app.analysis import analyze_file

main_bp = Blueprint('main', __name__)

@main_bp.route('/register', methods=['GET', 'POST'])
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
            
            return redirect(url_for('main.login', registered='true'))
            
        except mysql.connector.Error as err:
            print(f"Database error during registration: {err}")
            return "An internal database error occurred.", 500
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        session['user'] = email
        return redirect(url_for('main.index'))

        conn = get_db_connection()
        if not conn:
            return redirect(url_for('main.index'))
            return "Database connection error. Please try again later.", 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user'] = email
                return redirect(url_for('main.index'))
            else:
                return render_template('invalid.html'), 401
        except mysql.connector.Error as err:
            print(f"Database error during login: {err}")
            return "An internal database error occurred.", 500
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    get_db_connection.close()
    session.pop('user', None)
    return redirect(url_for('main.login'))

@main_bp.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('main.login'))
    return render_template('index.html')

@main_bp.route('/results')
def results():
    if not session.get('user'):
        return redirect(url_for('main.login'))
    return render_template('results.html')

@main_bp.route('/sentiment_chart.png')
@main_bp.route('/chart.png')
def serve_chart():
    if not session.get('user'):
        return redirect(url_for('main.login'))
    charts_dir = os.path.join(current_app.root_path, '../charts')
    return send_from_directory(charts_dir, 'sentiment_chart.png')

@main_bp.route('/upload', methods=['POST'])
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
        gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        result_df = None
        
        if gcs_bucket_name:
            try:
                print(f"Uploading file '{filename}' to GCS bucket '{gcs_bucket_name}'...")
                storage_client = storage.Client()
                bucket = storage_client.bucket(gcs_bucket_name)
                blob = bucket.blob(filename)
                
                file.seek(0)
                blob.upload_from_file(file)
                
                # Dynamic GCS resolution uses project-relative paths
                result_df = analyze_file(filename)
                
            except Exception as e:
                print(f"Error during GCS upload or analysis: {e}")
                return jsonify({'message': 'GCS upload or analysis failed', 'error': str(e)}), 500
        else:
            # Local upload directory path resolved relative to root directory
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            try:
                result_df = analyze_file(filepath)
            except Exception as e:
                print(f"Error during local analysis: {e}")
                return jsonify({'message': 'File uploaded locally but error during analysis', 'error': str(e)}), 500
                
        if result_df is not None:
            rows_count = len(result_df)
            return jsonify({'message': 'File uploaded and analyzed successfully', 'rows': rows_count}), 200
        else:
            return jsonify({'message': 'File uploaded but analysis failed', 'rows': 0}), 500
