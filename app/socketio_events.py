"""
SocketIO Event Handlers
Handles real-time communication events
"""

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, disconnect
from app.models import db, Message, Room, User
from datetime import datetime
from functools import wraps

# Store typing users per room: {room_id: {user_id: timestamp}}
typing_users = {}

# Store room members: {room_id: set(user_ids)}
room_members = {}

def authenticated_only(f):
    """Decorator to ensure user is authenticated for SocketIO events"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Authentication required'})
                disconnect()
                return False
        except Exception:
            emit('error', {'message': 'Authentication required'})
            disconnect()
            return False
        return f(*args, **kwargs)
    return wrapped


def register_socketio_events(socketio):
    """Register all SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        # Check authentication
        if not current_user.is_authenticated:
            print("Unauthenticated connection attempt")
            return False
        
        # Update user online status
        current_user.is_online = True
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Join user to their personal room for notifications
        join_room(f"user_{current_user.id}")
        
        # Send current user info
        emit('connected', {
            'user_id': current_user.id,
            'username': current_user.username
        })
        
        print(f"User {current_user.username} connected")
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        # Check authentication
        if not current_user.is_authenticated:
            return
        
        # Update user online status
        current_user.is_online = False
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Clear typing status for all rooms
        for room_id in list(typing_users.keys()):
            if current_user.id in typing_users[room_id]:
                del typing_users[room_id][current_user.id]
        
        # Broadcast user offline status
        emit('user_status', {
            'user_id': current_user.id,
            'username': current_user.username,
            'is_online': False
        }, broadcast=True, include_self=False)
        
        print(f"User {current_user.username} disconnected")
    
    
    @socketio.on('join_room')
    @authenticated_only
    def handle_join_room(data):
        """Handle user joining a chat room"""
        room_id = data.get('room_id')
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return
        
        # Join the SocketIO room
        join_room(f"room_{room_id}")
        
        # Track room membership
        if room_id not in room_members:
            room_members[room_id] = set()
        room_members[room_id].add(current_user.id)
        
        # Broadcast join notification
        emit('user_joined', {
            'username': current_user.username,
            'user_id': current_user.id,
            'room_id': room_id,
            'room_name': room.name,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"room_{room_id}", include_self=False)
        
        # Send confirmation to user with room members
        room_user_ids = list(room_members.get(room_id, set()))
        room_users = User.query.filter(User.id.in_(room_user_ids), User.is_online == True).all()
        
        emit('room_joined', {
            'room_id': room_id,
            'room_name': room.name,
            'members': [user.to_dict() for user in room_users]
        })
        
        # Broadcast updated room members to all room members
        emit('room_members_update', {
            'room_id': room_id,
            'members': [user.to_dict() for user in room_users]
        }, room=f"room_{room_id}")
        
        print(f"User {current_user.username} joined room {room.name}")
    
    
    @socketio.on('leave_room')
    @authenticated_only
    def handle_leave_room(data):
        """Handle user leaving a chat room"""
        room_id = data.get('room_id')
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return
        
        # Leave the SocketIO room
        leave_room(f"room_{room_id}")
        
        # Remove from room members tracking
        if room_id in room_members:
            room_members[room_id].discard(current_user.id)
            if len(room_members[room_id]) == 0:
                del room_members[room_id]
        
        # Clear typing status
        if room_id in typing_users and current_user.id in typing_users[room_id]:
            del typing_users[room_id][current_user.id]
        
        # Broadcast leave notification
        emit('user_left', {
            'username': current_user.username,
            'user_id': current_user.id,
            'room_id': room_id,
            'room_name': room.name,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"room_{room_id}", include_self=False)
        
        # Send confirmation to user
        emit('room_left', {
            'room_id': room_id,
            'room_name': room.name
        })
        
        # Broadcast updated room members to remaining members
        if room_id in room_members:
            room_user_ids = list(room_members[room_id])
            room_users = User.query.filter(User.id.in_(room_user_ids), User.is_online == True).all()
            emit('room_members_update', {
                'room_id': room_id,
                'members': [user.to_dict() for user in room_users]
            }, room=f"room_{room_id}")
        
        print(f"User {current_user.username} left room {room.name}")
    
    
    @socketio.on('send_message')
    @authenticated_only
    def handle_send_message(data):
        """Handle sending a chat message (text, GIF, audio, or file attachment)"""
        content = data.get('content', '').strip()
        room_id = data.get('room_id')
        message_type = data.get('message_type', 'text')
        file_name = data.get('file_name', None)
        
        if not content:
            emit('error', {'message': 'Message content cannot be empty'})
            return
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        # Validate message type
        valid_types = ['text', 'gif', 'audio', 'image', 'video', 'file']
        if message_type not in valid_types:
            message_type = 'text'
        
        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room not found'})
            return
        
        # Create and save message
        try:
            message = Message(
                content=content,
                user_id=current_user.id,
                room_id=room_id,
                message_type=message_type,
                file_name=file_name,
                timestamp=datetime.utcnow()
            )
            db.session.add(message)
            db.session.commit()
            
            # Clear typing indicator
            if room_id in typing_users and current_user.id in typing_users[room_id]:
                del typing_users[room_id][current_user.id]
            
            # Broadcast message to room
            message_data = message.to_dict()
            # Ensure file_name is included in the response
            if file_name:
                message_data['file_name'] = file_name
            emit('new_message', message_data, room=f"room_{room_id}")
            
            # Clear typing indicators
            emit('stop_typing', {
                'user_id': current_user.id,
                'username': current_user.username
            }, room=f"room_{room_id}", include_self=False)
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': 'Failed to send message'})
            print(f"Error sending message: {e}")
    
    
    @socketio.on('typing')
    @authenticated_only
    def handle_typing(data):
        """Handle typing indicator"""
        room_id = data.get('room_id')
        
        if not room_id:
            return
        
        # Update typing status
        if room_id not in typing_users:
            typing_users[room_id] = {}
        
        typing_users[room_id][current_user.id] = datetime.utcnow()
        
        # Broadcast typing indicator (exclude sender)
        emit('user_typing', {
            'user_id': current_user.id,
            'username': current_user.username,
            'room_id': room_id
        }, room=f"room_{room_id}", include_self=False)
    
    
    @socketio.on('stop_typing')
    @authenticated_only
    def handle_stop_typing(data):
        """Handle stop typing indicator"""
        room_id = data.get('room_id')
        
        if not room_id:
            return
        
        # Remove typing status
        if room_id in typing_users and current_user.id in typing_users[room_id]:
            del typing_users[room_id][current_user.id]
        
        # Broadcast stop typing
        emit('stop_typing', {
            'user_id': current_user.id,
            'username': current_user.username,
            'room_id': room_id
        }, room=f"room_{room_id}", include_self=False)
    
    
    @socketio.on('request_online_users')
    @authenticated_only
    def handle_request_online_users(data=None):
        """Send list of online users in a specific room"""
        room_id = data.get('room_id') if data else None
        
        if room_id:
            # Return only users in this specific room who are online
            if room_id in room_members:
                room_user_ids = list(room_members[room_id])
                room_users = User.query.filter(
                    User.id.in_(room_user_ids),
                    User.is_online == True
                ).all()
                emit('online_users', {
                    'room_id': room_id,
                    'users': [user.to_dict() for user in room_users]
                })
            else:
                emit('online_users', {
                    'room_id': room_id,
                    'users': []
                })
        else:
            # Return all online users (fallback)
            online_users = User.query.filter_by(is_online=True).all()
            emit('online_users', {
                'room_id': None,
                'users': [user.to_dict() for user in online_users]
            })
    
    
    @socketio.on('delete_message')
    @authenticated_only
    def handle_delete_message(data):
        """Handle message deletion"""
        message_id = data.get('message_id')
        
        if not message_id:
            emit('error', {'message': 'Message ID is required'})
            return
        
        try:
            message = Message.query.get(message_id)
            
            if not message:
                emit('error', {'message': 'Message not found'})
                return
            
            # Only allow the message sender to delete their own message
            if message.user_id != current_user.id:
                emit('error', {'message': 'Unauthorized: You can only delete your own messages'})
                return
            
            room_id = message.room_id
            
            # Delete associated audio file if it's an audio message
            if message.message_type == 'audio' and message.content:
                import os
                audio_path = message.content
                if audio_path.startswith('/'):
                    audio_path = audio_path[1:]
                full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), audio_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception as e:
                        print(f"Warning: Could not delete audio file: {e}")
            
            db.session.delete(message)
            db.session.commit()
            
            # Broadcast deletion to all users in the room
            emit('message_deleted', {
                'message_id': message_id,
                'room_id': room_id
            }, room=f"room_{room_id}")
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': 'Failed to delete message'})
            print(f"Error deleting message: {e}")
    
    
    @socketio.on('delete_room')
    @authenticated_only
    def handle_delete_room(data):
        """Handle room deletion"""
        room_id = data.get('room_id')
        
        if not room_id:
            emit('error', {'message': 'Room ID is required'})
            return
        
        try:
            room = Room.query.get(room_id)
            
            if not room:
                emit('error', {'message': 'Room not found'})
                return
            
            # Only allow the room creator to delete the room
            if room.created_by != current_user.id:
                emit('error', {'message': 'Unauthorized: You can only delete rooms you created'})
                return
            
            # Prevent deletion of global room
            if room.is_global:
                emit('error', {'message': 'Cannot delete the global room'})
                return
            
            room_name = room.name
            
            # Delete all messages in the room (cascade will handle this, but we'll also clean up audio files)
            messages = Message.query.filter_by(room_id=room_id).all()
            import os
            for msg in messages:
                if msg.message_type == 'audio' and msg.content:
                    audio_path = msg.content
                    if audio_path.startswith('/'):
                        audio_path = audio_path[1:]
                    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), audio_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except Exception as e:
                            print(f"Warning: Could not delete audio file: {e}")
            
            db.session.delete(room)
            db.session.commit()
            
            # Remove from room_members tracking
            if room_id in room_members:
                del room_members[room_id]
            
            # Broadcast room deletion to all users
            emit('room_deleted', {
                'room_id': room_id,
                'room_name': room_name
            }, broadcast=True)
            
        except Exception as e:
            db.session.rollback()
            emit('error', {'message': 'Failed to delete room'})
            print(f"Error deleting room: {e}")
    
    
    @socketio.on('request_rooms')
    @authenticated_only
    def handle_request_rooms():
        """Send list of rooms user has joined"""
        # Only return rooms where the current user has sent at least one message
        user_rooms = Room.query.join(Message).filter(
            Message.user_id == current_user.id
        ).distinct().order_by(Room.created_at.desc()).all()
        emit('rooms_list', [room.to_dict() for room in user_rooms])

