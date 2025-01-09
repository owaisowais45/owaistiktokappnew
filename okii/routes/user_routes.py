from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from okii import mongo
from datetime import datetime
import os
import logging
from gridfs import GridFS
import cloudinary.uploader
from flask import jsonify
from bson import ObjectId


ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

user_bp = Blueprint('user', __name__)

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            bio = request.form.get('bio', '').strip()
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            
            if 'avatar' in request.files:
                avatar = request.files['avatar']
                if avatar and avatar.filename:
                    if allowed_file(avatar.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                        filename = secure_filename(avatar.filename)
                        avatar_path = os.path.join('okii', 'static', 'uploads', 'avatars', filename)
                        avatar.save(avatar_path)
                        mongo.db.users.update_one(
                            {'_id': current_user.id},
                            {'$set': {'avatar': filename}}
                        )
                        flash('Avatar updated successfully!', 'success')
                    else:
                        flash('Invalid file type. Please upload an image.', 'error')

            
            updates = {}
            if username and username != current_user.username:
                
                if not mongo.db.users.find_one({'username': username, '_id': {'$ne': current_user.id}}):
                    updates['username'] = username
                else:
                    flash('Username already taken.', 'error')
                    return render_template('user/settings.html')

            if email and email != current_user.email:
                
                if not mongo.db.users.find_one({'email': email, '_id': {'$ne': current_user.id}}):
                    updates['email'] = email
                else:
                    flash('Email already registered.', 'error')
                    return render_template('user/settings.html')

            if bio != current_user.bio:
                updates['bio'] = bio

            
            if current_password and new_password and confirm_password:
                if not check_password_hash(current_user.password, current_password):
                    flash('Current password is incorrect.', 'error')
                    return render_template('user/settings.html')
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return render_template('user/settings.html')
                
                if len(new_password) < 8:
                    flash('Password must be at least 8 characters long.', 'error')
                    return render_template('user/settings.html')
                
                updates['password'] = generate_password_hash(new_password)

            
            if updates:
                mongo.db.users.update_one(
                    {'_id': current_user.id},
                    {'$set': updates}
                )
                flash('Settings updated successfully!', 'success')

            return redirect(url_for('user.settings'))

        except Exception as e:
            print(f"Error updating settings: {e}")
            flash('An error occurred while updating settings.', 'error')

    return render_template('user/settings.html')



@user_bp.route('/follow/<user_id>')
@login_required
def follow_user(user_id):
    if user_id != str(current_user.id):
        try:
            
            mongo.db.users.update_one(
                {'_id': current_user.id},
                {'$addToSet': {'following': user_id}}
            )
            
            mongo.db.users.update_one(
                {'_id': user_id},
                {'$addToSet': {'followers': str(current_user.id)}}
            )
            flash('User followed successfully!', 'success')
        except Exception as e:
            print(f"Error following user: {e}")
            flash('An error occurred while following user.', 'error')
    return redirect(request.referrer or url_for('main.index'))

@user_bp.route('/unfollow/<user_id>')
@login_required
def unfollow_user(user_id):
    if user_id != str(current_user.id):
        try:
            
            mongo.db.users.update_one(
                {'_id': current_user.id},
                {'$pull': {'following': user_id}}
            )
            
            mongo.db.users.update_one(
                {'_id': user_id},
                {'$pull': {'followers': str(current_user.id)}}
            )
            flash('User unfollowed successfully!', 'success')
        except Exception as e:
            print(f"Error unfollowing user: {e}")
            flash('An error occurred while unfollowing user.', 'error')
    return redirect(request.referrer or url_for('main.index'))












            





























            








            







    












            















            

            








def creator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_creator:
            flash('This feature is only available for creators.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/upload-video', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        try:
            
            if 'video' not in request.files:
                flash('No video file uploaded', 'error')
                return redirect(request.url)
            
            video_file = request.files['video']
            if not video_file or video_file.filename == '':
                flash('No video selected', 'error')
                return redirect(request.url)

            
            if not allowed_file(video_file.filename):
                flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
                return redirect(request.url)

            
            upload_result = cloudinary.uploader.upload(
                video_file,
                resource_type="video",
                folder="videos/",
                eager=[
                    {"width": 300, "height": 300, "crop": "pad", "audio_codec": "none"},
                    {"width": 160, "height": 100, "crop": "crop", "gravity": "south", "audio_codec": "none"}
                ],
                eager_async=True
            )

            
            video_data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'video_url': upload_result['secure_url'],
                'thumbnail_url': upload_result['eager'][1]['secure_url'],
                'public_id': upload_result['public_id'],
                'user_id': str(current_user.id),
                'username': current_user.username,
                'created_at': datetime.utcnow(),
                'views': 0,
                'likes': [],
                'comments': [],
                'status': 'active'
            }
            
            
            result = mongo.db.videos.insert_one(video_data)
            
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('user.profile', username=current_user.username))

        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            flash('Error uploading video. Please try again.', 'error')
            return redirect(request.url)
            
    return render_template('user/upload_video.html')


































@user_bp.route('/video/<video_id>/like', methods=['POST'])
@login_required
def like_video(video_id):
    try:
        user_id = str(current_user.id)
        
        
        video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video not found'}), 404

        likes = video.get('likes', [])
        is_liked = user_id in likes

        
        if is_liked:
            result = mongo.db.videos.update_one(
                {'_id': ObjectId(video_id)},
                {'$pull': {'likes': user_id}}
            )
        else:
            result = mongo.db.videos.update_one(
                {'_id': ObjectId(video_id)},
                {'$addToSet': {'likes': user_id}}
            )

        if result.modified_count:
            
            updated_video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
            new_likes = updated_video.get('likes', [])
            
            return jsonify({
                'success': True,
                'liked': not is_liked,
                'likes_count': len(new_likes)
            })

        return jsonify({'error': 'Failed to update like'}), 400

    except Exception as e:
        print(f"Error in like_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/video/<video_id>/comment', methods=['POST'])
@login_required
def add_comment(video_id):
    try:
        comment = request.json.get('comment')
        if not comment:
            return jsonify({'error': 'Comment is required'}), 400

        new_comment = {
            'user_id': str(current_user.id),
            'username': current_user.username,
            'content': comment,
            'created_at': datetime.utcnow()
        }

        result = mongo.db.videos.update_one(
            {'_id': ObjectId(video_id)},
            {
                '$push': {'comments': new_comment},
                '$inc': {'comments_count': 1}
            }
        )

        if result.modified_count:
            return jsonify({
                'success': True,
                'comment': new_comment
            })
        return jsonify({'error': 'Failed to add comment'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/video/<video_id>/comments', methods=['GET'])
def get_comments(video_id):
    try:
        video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video not found'}), 404
            
        comments = video.get('comments', [])
        for comment in comments:
            comment['created_at'] = comment['created_at'].isoformat()
            
        return jsonify({'comments': comments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
        
@user_bp.route('/profile/<username>')
def profile(username):
    try:
        
        user_data = mongo.db.users.find_one({'username': username})
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('main.index'))

        
        user_id = str(user_data['_id'])
        
        
        videos = list(mongo.db.videos.find({'user_id': user_id}).sort('created_at', -1))
        
        
        total_views = sum(video.get('views', 0) for video in videos)
        total_likes = sum(len(video.get('likes', [])) for video in videos)
        followers = user_data.get('followers', [])
        following = user_data.get('following', [])
        
        stats = {
            'videos_count': len(videos),
            'total_views': total_views,
            'total_likes': total_likes,
            'followers_count': len(followers),
            'following_count': len(following)
        }
        
        
        is_following = False
        if current_user.is_authenticated:
            is_following = str(current_user.id) in followers

        return render_template('user/profile.html',
            user=user_data,
            videos=videos,
            stats=stats,
            is_following=is_following
        )
        
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        flash('An error occurred while loading the profile.', 'error')
        return redirect(url_for('main.index'))
    
    
@user_bp.route('/profile/<username>/videos')
def user_videos(username):
    try:
        
        user_data = mongo.db.users.find_one({'username': username})
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('main.index'))

        
        page = request.args.get('page', 1, type=int)
        per_page = 12
        skip = (page - 1) * per_page

        
        query = {'user_id': str(user_data['_id'])}
        if str(user_data['_id']) != str(current_user.id):
            query['visibility'] = 'public'

        
        videos = list(mongo.db.videos.find(query)
                     .sort('created_at', -1)
                     .skip(skip)
                     .limit(per_page))
        
        
        total_videos = mongo.db.videos.count_documents(query)
        total_pages = (total_videos + per_page - 1) // per_page

        return render_template('user/videos.html',
            profile_user=user_data,
            videos=videos,
            page=page,
            total_pages=total_pages,
            total_videos=total_videos
        )
    except Exception as e:
        print(f"Error loading user videos: {e}")
        flash('An error occurred while loading videos.', 'error')
        return redirect(url_for('main.index'))