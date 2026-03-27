from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import os
import topic_analysis

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = 'super_secret_key_for_this_demo_only_change_in_production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email=="user@intellize.com" and password=="intellize":
            session['user'] = email
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 401
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
