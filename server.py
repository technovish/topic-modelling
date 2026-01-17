from flask import Flask, request, jsonify, send_from_directory
import os
import topic_analysis

app = Flask(__name__, static_folder='.')

UPLOAD_FOLDER = 'data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/results')
def results():
    return send_from_directory('.', 'results.html')

@app.route('/chart.png')
def serve_chart():
    return send_from_directory('.', 'chart.png')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/upload', methods=['POST'])
def upload_file():
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
    app.run(debug=True, port=5000)
