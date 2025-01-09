from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from okii.models import get_all_videos, get_all_users, get_system_stats, Video, User
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.user_data.get('is_admin', False):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    stats = get_system_stats()
    recent_videos = get_all_videos()[:10]  
    recent_users = get_all_users()[:10]    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_videos=recent_videos,
                         recent_users=recent_users)

@admin_bp.route('/admin/videos')
@login_required
@admin_required
def videos():
    page = int(request.args.get('page', 1))
    per_page = 20
    videos = get_all_videos()
    total_videos = len(videos)
    videos = videos[(page-1)*per_page:page*per_page]
    
    return render_template('admin/videos.html',
                         videos=videos,
                         page=page,
                         total_pages=(total_videos + per_page - 1) // per_page)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def users():
    page = int(request.args.get('page', 1))
    per_page = 20
    users = get_all_users()
    total_users = len(users)
    users = users[(page-1)*per_page:page*per_page]
    
    return render_template('admin/users.html',
                         users=users,
                         page=page,
                         total_pages=(total_users + per_page - 1) // per_page)

@admin_bp.route('/admin/video/<video_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_video(video_id):
    mongo.db.videos.delete_one({'_id': ObjectId(video_id)})
    flash('Video deleted successfully', 'success')
    return redirect(url_for('admin.videos'))

@admin_bp.route('/admin/user/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        new_status = not user.get('is_active', True)
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_active': new_status}}
        )
        status = 'activated' if new_status else 'deactivated'
        flash(f'User {status} successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/video/<video_id>/toggle-visibility', methods=['POST'])
@login_required
@admin_required
def toggle_video_visibility(video_id):
    video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
    if video:
        new_visibility = 'private' if video.get('visibility') == 'public' else 'public'
        mongo.db.videos.update_one(
            {'_id': ObjectId(video_id)},
            {'$set': {'visibility': new_visibility}}
        )
        flash(f'Video visibility changed to {new_visibility}', 'success')
    return redirect(url_for('admin.videos'))