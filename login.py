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

    @patch('server.get_db_connection')
    def test_register_get(self, mock_get_db):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Create an Account", response.data.decode())

    @patch('server.get_db_connection')
    def test_register_success(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # User does not exist yet (fetchone returns None)
        mock_cursor.fetchone.return_value = None
        
        response = self.client.post('/register', data={
            'email': 'newuser@intellize.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        
        # Check redirect (302) to login page with registered query param
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/login?registered=true'))
        mock_cursor.execute.assert_any_call("SELECT id FROM users WHERE email = %s", ('newuser@intellize.com',))
        mock_conn.commit.assert_called_once()

    @patch('server.get_db_connection')
    def test_register_duplicate_email(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # User already exists
        mock_cursor.fetchone.return_value = {'id': 1}
        
        response = self.client.post('/register', data={
            'email': 'existing@intellize.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        
        self.assertEqual(response.status_code, 409)
        self.assertIn("A user with this email already exists", response.data.decode())

    @patch('server.get_db_connection')
    def test_register_passwords_mismatch(self, mock_get_db):
        response = self.client.post('/register', data={
            'email': 'newuser@intellize.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Passwords do not match", response.data.decode())

    @patch('server.get_db_connection')
    def test_register_password_too_short(self, mock_get_db):
        response = self.client.post('/register', data={
            'email': 'newuser@intellize.com',
            'password': '12345',
            'confirm_password': '12345'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password must be at least 6 characters long", response.data.decode())

    @patch('server.get_db_connection')
    def test_register_invalid_email(self, mock_get_db):
        response = self.client.post('/register', data={
            'email': 'invalid-email',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid email address format", response.data.decode())

    @patch('server.mysql.connector.connect')
    def test_get_db_connection_unix_socket(self, mock_connect):
        import server
        server.DB_SOCKET = '/cloudsql/test-instance'
        try:
            server.get_db_connection()
            mock_connect.assert_called_once_with(
                unix_socket='/cloudsql/test-instance',
                user=server.DB_USER,
                password=server.DB_PASSWORD,
                database=server.DB_NAME
            )
        finally:
            server.DB_SOCKET = None

if __name__ == '__main__':
    unittest.main()
