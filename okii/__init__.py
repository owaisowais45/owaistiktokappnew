from flask import Flask, redirect, url_for, render_template, request, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager
from datetime import datetime
from bson import ObjectId
from werkzeug.utils import secure_filename
import os
import timeago as timeago_lib
import logging
import ssl
from flask import send_from_directory
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


mongo = PyMongo()
login_manager = LoginManager()

def timeago(date):
    """Convert datetime to timeago string"""
    if not date:
        return ""
    try:
        return timeago_lib.format(date, datetime.utcnow())
    except Exception:
        return str(date)

def format_number(number):
    """Format large numbers to K/M format"""
    try:
        if number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        return str(number)
    except (TypeError, ValueError):
        return "0"
    
def allowed_file(filename, allowed_extensions={'mp4', 'avi', 'mov', 'wmv'}):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_file(filename, allowed_extensions={'mp4', 'avi', 'mov', 'wmv'}):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('okii.config.Config')
    
    from okii.routes.user_routes import user_bp

    
    cloudinary.config(
        cloud_name="duku3zctg",
        api_key="179741952874928",
        api_secret="Y3BLT3yhO8ZrXUBKIuIrgAvPuB0"
    )

    app.config['SECRET_KEY'] = 'e11dea08e77240f010a0dc56268816c07da06c26b64b4b5b'
    app.config['MONGO_URI'] = 'mongodb+srv://owaise:RrdhrFT96pHXjDup@cluster0.rc14l.mongodb.net/video_sharing?retryWrites=true&w=majority'

    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    mongo.init_app(app)
    login_manager.init_app(app)
    
    try:
        mongo.init_app(app)
        
        mongo.db.command('ping')
        logger.info("MongoDB connection successful!")
        
        
        mongo.db.users.create_index("email", unique=True)
        mongo.db.users.create_index("username", unique=True)
        mongo.db.videos.create_index([("title", "text"), ("description", "text")])
        mongo.db.videos.create_index("user_id")
        mongo.db.videos.create_index("created_at")
        mongo.db.videos.create_index("views")
        
        
        users_count = mongo.db.users.count_documents({})
        logger.info(f"Found {users_count} users in database")
        
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        raise e
    
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    
    app.jinja_env.filters['timeago'] = timeago
    app.jinja_env.filters['format_number'] = format_number
    
    
    @app.context_processor
    def utility_processor():
        return {
            'len': len,
            'str': str,
            'isinstance': isinstance,
            'current_year': datetime.utcnow().year,
            'allowed_file': allowed_file
        }
    
    
    @login_manager.user_loader
    def load_user(user_id):
        from okii.models import User
        return User.get(user_id)
    
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash('File too large. Maximum size is 100MB.', 'error')
        return redirect(request.url)
    
    
    from okii.routes.routes import main_bp
    from okii.routes.auth_routes import auth_bp
    from okii.routes.user_routes import user_bp
    from okii.routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    
    def get_file_extension(filename):
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else None

    def generate_unique_filename(original_filename, prefix=''):
        """Generate a unique filename with timestamp"""
        ext = get_file_extension(original_filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}_{str(ObjectId())}_{secure_filename(original_filename)}"

    
    app.jinja_env.globals.update(
        get_file_extension=get_file_extension,
        generate_unique_filename=generate_unique_filename
    )
    
    
    @app.after_request
    def cleanup_after_request(response):
        temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
        if os.path.exists(temp_folder):  
            try:
                for filename in os.listdir(temp_folder):
                    file_path = os.path.join(temp_folder, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)  
            except Exception as e:
                logger.error(f"Error cleaning up temp files: {e}")  
        return response

    
    return app


def get_video_duration(file_path):
    """Get video duration in seconds"""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(file_path)
        duration = clip.duration
        clip.close()
        return int(duration)
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return 0

def generate_thumbnail(video_path, output_path, time=2.0):
    """Generate thumbnail from video"""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(time)
        from PIL import Image
        import numpy as np
        img = Image.fromarray(np.uint8(frame))
        img.thumbnail((320, 180))  
        img.save(output_path, quality=85, optimize=True)
        clip.close()
        return True
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return False
    

