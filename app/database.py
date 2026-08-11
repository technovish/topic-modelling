import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'comments.db')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_SOCKET = os.getenv('DB_SOCKET')

def get_db_connection():
    try:
        if DB_SOCKET:
            conn = mysql.connector.connect(
                unix_socket=DB_SOCKET,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
        else:
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
