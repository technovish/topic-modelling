import unittest
import os
import shutil
import time
import threading
import requests
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from server import app

class TestFileUpload(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = 'test_data'
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        # Start global mock patch for get_db_connection so background thread uses it
        self.db_patcher = patch('app.routes.get_db_connection')
        self.mock_get_db = self.db_patcher.start()
        
        # Setup mock behavior
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_get_db.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        
        # Mock database response for login endpoint
        self.mock_user = {
            'id': 1,
            'email': 'user@intellize.com',
            'password_hash': generate_password_hash('intellize')
        }
        self.mock_cursor.fetchone.return_value = self.mock_user
        
        self.server_thread = threading.Thread(target=app.run, kwargs={'port': 5001, 'debug': False, 'use_reloader': False})
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(2)
        self.base_url = 'http://localhost:5001'

    def tearDown(self):
        # Stop database patcher
        self.db_patcher.stop()
        
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
            # Use requests Session to persist session/cookies
            session = requests.Session()
            
            # Log in first to establish session
            login_response = session.post(f'{self.base_url}/login', data={
                'email': 'user@intellize.com',
                'password': 'intellize'
            })
            
            # Login redirects to home (302) or returns 200
            self.assertIn(login_response.status_code, [200, 302])
            
            with open(filename, 'rb') as f:
                files = {'file': f}
                response = session.post(f'{self.base_url}/upload', files=files)
            
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
