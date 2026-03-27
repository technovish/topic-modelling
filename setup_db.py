import sqlite3
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'analytics_portal.db')

def setup_database():
    try:
        print(f"Connecting to SQLite database '{DB_NAME}'...")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create users table
        print("Creating 'users' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if default user exists
        cursor.execute("SELECT id FROM users WHERE email = 'user@intellize.com'")
        if not cursor.fetchone():
            print("Inserting default user 'user@intellize.com' ...")
            # Create a default user with hashed password
            hashed_pw = generate_password_hash('intellize')
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ('user@intellize.com', hashed_pw)
            )
            conn.commit()
            print("Default user created successfully. Email: user@intellize.com, Password: intellize")
        else:
            print("Default user already exists.")
            
        print("Database setup completed successfully!")

    except sqlite3.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
