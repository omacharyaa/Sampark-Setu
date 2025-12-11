"""
Profile Routes
Handles user profile management
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, User
import os
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

# Get absolute path for profile pictures folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILE_PICTURES_FOLDER = os.path.join(BASE_DIR, 'uploads', 'profiles')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure profile pictures directory exists
os.makedirs(PROFILE_PICTURES_FOLDER, exist_ok=True)

def allowed_image_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@profile_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Display user profile page"""
    return render_template('profile.html')

@profile_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile data"""
    return jsonify(current_user.to_dict())

@profile_bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Update username
        if 'username' in data and data['username']:
            new_username = data['username'].strip()
            if new_username != current_user.username:
                # Check if username is already taken
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user and existing_user.id != current_user.id:
                    return jsonify({'error': 'Username already taken'}), 400
                current_user.username = new_username
        
        # Update display name
        if 'display_name' in data:
            current_user.display_name = data['display_name'].strip() if data['display_name'] else None
        
        # Update email
        if 'email' in data and data['email']:
            new_email = data['email'].strip()
            if new_email != current_user.email:
                # Check if email is already taken
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user and existing_user.id != current_user.id:
                    return jsonify({'error': 'Email already taken'}), 400
                current_user.email = new_email
        
        db.session.commit()
        return jsonify({'success': True, 'user': current_user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/profile/picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Upload profile picture"""
    if 'picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['picture']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_image_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_IMAGE_SIZE:
        return jsonify({'error': 'File too large. Maximum size: 5MB'}), 400
    
    try:
        # Delete old profile picture if exists
        if current_user.profile_picture:
            old_path = os.path.join(BASE_DIR, current_user.profile_picture.lstrip('/'))
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Generate secure filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{current_user.id}_{timestamp}.{ext}"
        filepath = os.path.join(PROFILE_PICTURES_FOLDER, filename)
        
        # Ensure directory exists
        os.makedirs(PROFILE_PICTURES_FOLDER, exist_ok=True)
        file.save(filepath)
        
        # Update user profile picture path
        current_user.profile_picture = f"/uploads/profiles/{filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'profile_picture': current_user.profile_picture
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to upload picture: {str(e)}'}), 500

@profile_bp.route('/uploads/profiles/<filename>')
def serve_profile_picture(filename):
    """Serve profile pictures (public endpoint)"""
    from flask import send_from_directory
    
    # Security: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    file_path = os.path.join(PROFILE_PICTURES_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_from_directory(PROFILE_PICTURES_FOLDER, filename)

