import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    # Flask templates/static defaults to templates/ and static/ inside the app/ directory
    app = Flask(__name__)
    
    app.secret_key = os.getenv('SECRET_KEY', 'super_secret_key_for_this_demo_only_change_in_production')
    
    # Configure UPLOAD_FOLDER as the root data directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(base_dir, 'data')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
