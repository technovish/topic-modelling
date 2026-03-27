import unittest
from unittest.mock import patch, MagicMock
import os

# Set testing environment variables
os.environ['DB_NAME'] = 'testdb.db'

from server import app
from werkzeug.security import generate_password_hash

class TestLogin(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret'
        self.client = app.test_client()

    @patch('server.get_db_connection')
    def test_login_success(self, mock_get_db):
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Setup mock behavior
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database response
        mock_user = {
            'id': 1,
            'email': 'user@intellize.com',
            'password_hash': generate_password_hash('intellize')
        }
        mock_cursor.fetchone.return_value = mock_user
        
        # Test login
        response = self.client.post('/login', data={
            'email': 'user@intellize.com',
            'password': 'intellize'
        })
        
        # Check redirect (302)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/'))

    @patch('server.get_db_connection')
    def test_login_failure(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database response (wrong password)
        mock_user = {
            'id': 1,
            'email': 'user@intellize.com',
            'password_hash': generate_password_hash('intellize')
        }
        mock_cursor.fetchone.return_value = mock_user
        
        response = self.client.post('/login', data={
            'email': 'user@intellize.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 401)
        self.assertIn("Sign In Failed", response.data.decode())
        
    @patch('server.get_db_connection')
    def test_login_db_error(self, mock_get_db):
        mock_get_db.return_value = None
        
        response = self.client.post('/login', data={
            'email': 'user@intellize.com',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("Database connection error", response.data.decode())

if __name__ == '__main__':
    unittest.main()
