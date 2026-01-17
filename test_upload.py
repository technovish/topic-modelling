import unittest
import os
import shutil
import time
import threading
import requests
from werkzeug.serving import make_server
from server import app

class TestFileUpload(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = 'test_data'
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        self.server_thread = threading.Thread(target=app.run, kwargs={'port': 5001, 'debug': False, 'use_reloader': False})
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(2)
        self.base_url = 'http://localhost:5001'

    def tearDown(self):
        # Clean up test data
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])

    def test_upload_flow(self):
        # Create a dummy CSV file
        filename = 'test_comments.csv'
        with open(filename, 'w') as f:
            f.write('Customer Feedback Filtered\n')
            f.write('Great service!\n')
            f.write('Terrible experience.\n')
        
        try:
            with open(filename, 'rb') as f:
                files = {'file': f}
                response = requests.post(f'{self.base_url}/upload', files=files)
            
            # Check response
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('File uploaded', response.json()['message'])
            
            # Check if file was saved
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            self.assertTrue(os.path.exists(saved_path), "File should be saved to upload folder")
            
        finally:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    unittest.main()
