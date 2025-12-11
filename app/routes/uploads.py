"""
File Upload Routes
Handles audio file uploads and file attachments
"""

from flask import Blueprint, request, jsonify, send_from_directory, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

uploads_bp = Blueprint('uploads', __name__)

# Get absolute path for upload folder (root directory of project)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'audio')
ATTACHMENTS_FOLDER = os.path.join(BASE_DIR, 'uploads', 'attachments')
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'webm', 'm4a'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'csv'}
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for other files

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_FILE_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(filename):
    """Determine file type based on extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return 'file'
    return 'file'

@uploads_bp.route('/upload_audio', methods=['POST'])
@login_required
def upload_audio():
    """Handle audio file upload"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
        return jsonify({'error': 'Invalid file type. Allowed: mp3, wav, ogg, webm, m4a'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_AUDIO_SIZE:
        return jsonify({'error': 'File too large. Maximum size: 10MB'}), 400
    
    # Generate secure filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{current_user.id}_{timestamp}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Ensure directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        # Verify file was saved
        if not os.path.exists(filepath):
            return jsonify({'error': 'File was not saved correctly'}), 500
        
        # Return URL path (not full system path)
        url = f"/uploads/audio/{filename}"
        return jsonify({
            'success': True,
            'url': url,
            'filename': filename
        }), 200
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

@uploads_bp.route('/uploads/audio/<filename>')
def serve_audio(filename):
    """Serve audio files with proper headers for audio playback"""
    try:
        # Security: ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Determine MIME type based on extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        mime_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'webm': 'audio/webm',
            'm4a': 'audio/mp4'
        }
        mime_type = mime_types.get(ext, 'audio/mpeg')
        
        # Create response with proper headers for audio streaming
        response = make_response(send_from_directory(UPLOAD_FOLDER, filename, mimetype=mime_type))
        
        # Enable range requests for audio playback (important for seeking)
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Content-Type'] = mime_type
        
        # Add CORS headers if needed
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Range'
        
        return response
    except Exception as e:
        print(f"Error serving audio file: {e}")
        return jsonify({'error': str(e)}), 500


@uploads_bp.route('/upload_attachment', methods=['POST'])
@login_required
def upload_attachment():
    """Handle file attachment upload (images, videos, documents, etc.)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: images, videos, documents, audio files'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    try:
        # Generate secure filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        filename = f"{current_user.id}_{timestamp}_{original_filename}"
        filepath = os.path.join(ATTACHMENTS_FOLDER, filename)
        
        # Ensure directory exists
        os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)
        file.save(filepath)
        
        # Verify file was saved
        if not os.path.exists(filepath):
            return jsonify({'error': 'File was not saved correctly'}), 500
        
        file_type = get_file_type(original_filename)
        
        # Return URL path
        url = f"/uploads/attachments/{filename}"
        return jsonify({
            'success': True,
            'url': url,
            'filename': filename,
            'original_filename': original_filename,
            'file_type': file_type,
            'file_size': file_size
        }), 200
    except Exception as e:
        print(f"Error saving attachment file: {e}")
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500


@uploads_bp.route('/uploads/attachments/<filename>')
def serve_attachment(filename):
    """Serve attachment files with proper MIME types"""
    try:
        # Security: ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join(ATTACHMENTS_FOLDER, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Determine MIME type based on extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        mime_types = {
            # Images
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
            'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp', 'svg': 'image/svg+xml',
            # Videos
            'mp4': 'video/mp4', 'webm': 'video/webm', 'ogg': 'video/ogg',
            'mov': 'video/quicktime', 'avi': 'video/x-msvideo', 'mkv': 'video/x-matroska',
            # Documents
            'pdf': 'application/pdf',
            'doc': 'application/msword', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel', 'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'txt': 'text/plain', 'rtf': 'application/rtf', 'csv': 'text/csv',
            # Audio (for attachments)
            'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg', 'webm': 'audio/webm', 'm4a': 'audio/mp4'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        response = make_response(send_from_directory(ATTACHMENTS_FOLDER, filename, mimetype=mime_type))
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        # For videos, enable range requests for seeking
        if ext in ALLOWED_VIDEO_EXTENSIONS or ext in ALLOWED_AUDIO_EXTENSIONS:
            response.headers['Accept-Ranges'] = 'bytes'
        
        return response
    except Exception as e:
        print(f"Error serving attachment file: {e}")
        return jsonify({'error': str(e)}), 500

