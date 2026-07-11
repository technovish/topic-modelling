import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'comments.db')
DB_PORT = os.getenv('DB_PORT', '3306')

def setup_database():
    try:
        print(f"Connecting to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=int(DB_PORT)
        )
        cursor = conn.cursor()
        
        # Create users table with MySQL compatible syntax
        print("Creating 'users' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if default user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", ('user@intellize.com',))
        if not cursor.fetchone():
            print("Inserting default user 'user@intellize.com' ...")
            # Create a default user with hashed password
            hashed_pw = generate_password_hash('intellize')
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                ('user@intellize.com', hashed_pw)
            )
            conn.commit()
            print("Default user created successfully. Email: user@intellize.com, Password: intellize")
        else:
            print("Default user already exists.")
            
        print("Database setup completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
