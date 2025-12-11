"""
Database Models for Sampark Setu
Defines User, Room, and Message models
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)  # Path to profile picture
    display_name = db.Column(db.String(100), nullable=True)  # Optional display name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify user password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'profile_picture': self.profile_picture,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Room(db.Model):
    """Chat room model"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_global = db.Column(db.Boolean, default=False)  # Global chat room
    
    # Relationships
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        """Convert room to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_global': self.is_global,
            'message_count': len(self.messages)
        }
    
    def __repr__(self):
        return f'<Room {self.name}>'


class Message(db.Model):
    """Message model for chat messages with support for text, GIF, audio, and file attachments"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # Text content, GIF URL, audio file path, or file path
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    message_type = db.Column(db.String(20), default='text', nullable=False)  # 'text', 'gif', 'audio', 'file', 'image', 'video'
    file_name = db.Column(db.String(255), nullable=True)  # Original filename for attachments
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        try:
            # Handle message_type - use default if not set (for older messages)
            message_type = getattr(self, 'message_type', 'text')
            if not message_type:
                message_type = 'text'
            
            # Safely get user information
            username = 'Unknown'
            display_name = 'Unknown'
            profile_picture = None
            try:
                if hasattr(self, 'user') and self.user:
                    username = self.user.username or 'Unknown'
                    display_name = self.user.display_name or self.user.username or 'Unknown'
                    profile_picture = getattr(self.user, 'profile_picture', None)
            except Exception as user_error:
                print(f"Error accessing user for message {self.id}: {user_error}")
            
            # Safely get room information
            room_name = 'Unknown'
            try:
                if hasattr(self, 'room') and self.room:
                    room_name = self.room.name or 'Unknown'
            except Exception as room_error:
                print(f"Error accessing room for message {self.id}: {room_error}")
            
            # Safely get timestamp
            timestamp_iso = None
            formatted_time = ''
            formatted_date = ''
            try:
                if self.timestamp:
                    timestamp_iso = self.timestamp.isoformat()
                    formatted_time = self.timestamp.strftime('%I:%M %p')
                    formatted_date = self.timestamp.strftime('%B %d, %Y')
            except Exception as time_error:
                print(f"Error formatting timestamp for message {self.id}: {time_error}")
            
            return {
                'id': self.id,
                'content': str(self.content) if self.content else '',
                'user_id': self.user_id,
                'username': username,
                'display_name': display_name,
                'profile_picture': profile_picture,
                'room_id': self.room_id,
                'room_name': room_name,
                'message_type': message_type,
                'file_name': getattr(self, 'file_name', None),
                'timestamp': timestamp_iso,
                'formatted_time': formatted_time,
                'formatted_date': formatted_date
            }
        except Exception as e:
            # Fallback for any serialization errors
            print(f"Critical error in to_dict for message {getattr(self, 'id', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'id': getattr(self, 'id', 0),
                'content': str(getattr(self, 'content', '')),
                'user_id': getattr(self, 'user_id', 0),
                'username': 'Unknown',
                'display_name': 'Unknown',
                'profile_picture': None,
                'room_id': getattr(self, 'room_id', 0),
                'room_name': 'Unknown',
                'message_type': 'text',
                'file_name': None,
                'timestamp': None,
                'formatted_time': '',
                'formatted_date': ''
            }
    
    def __repr__(self):
        return f'<Message {self.id} [{self.message_type}] by {self.user_id} in {self.room_id}>'

