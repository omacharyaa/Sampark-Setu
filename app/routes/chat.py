"""
Chat Routes
Handles main chat interface and room management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Room, Message, User
from datetime import datetime
import requests
import os

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def index():
    """Main chat interface"""
    # Don't show any rooms by default - users must join by ID
    # Only show rooms that have messages from the current user (joined rooms)
    user_rooms = Room.query.join(Message).filter(
        Message.user_id == current_user.id
    ).distinct().order_by(Room.created_at.desc()).all()
    
    return render_template('chat.html', 
                         rooms=user_rooms)  # Only show rooms user has joined


@chat_bp.route('/create-room', methods=['POST'])
@login_required
def create_room():
    """Create a new chat room with auto-generated ID-based name"""
    room_name = request.form.get('room_name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not room_name or len(room_name) < 3:
        flash('Room name must be at least 3 characters long.', 'error')
        return redirect(url_for('chat.index'))
    
    try:
        # Create room - ID will be auto-generated
        new_room = Room(
            name=room_name,
            description=description,
            created_by=current_user.id
        )
        db.session.add(new_room)
        db.session.commit()
        
        # Auto-join: Create a welcome message so the room appears in user's joined rooms
        welcome_message = Message(
            content=f"Welcome to {room_name}!",
            user_id=current_user.id,
            room_id=new_room.id,
            message_type='text'
        )
        db.session.add(welcome_message)
        db.session.commit()
        
        flash(f'Room "{room_name}" created successfully! Room ID: {new_room.id}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the room.', 'error')
    
    return redirect(url_for('chat.index'))


@chat_bp.route('/join-room', methods=['POST'])
@login_required
def join_room_by_id():
    """Join a room by room ID"""
    room_id = request.form.get('room_id', '').strip()
    
    if not room_id:
        flash('Please enter a room ID.', 'error')
        return redirect(url_for('chat.index'))
    
    try:
        room_id_int = int(room_id)
        room = Room.query.get(room_id_int)
        
        if not room:
            flash(f'Room with ID {room_id} not found.', 'error')
            return redirect(url_for('chat.index'))
        
        # Create a join message so the room appears in user's joined rooms
        # Check if user already has messages in this room
        existing_message = Message.query.filter_by(
            user_id=current_user.id,
            room_id=room_id_int
        ).first()
        
        if not existing_message:
            # Create a system join message
            join_message = Message(
                content=f"{current_user.username} joined the room",
                user_id=current_user.id,
                room_id=room_id_int,
                message_type='text'
            )
            db.session.add(join_message)
            db.session.commit()
        
        # Room exists, redirect to chat with room_id parameter
        flash(f'Joined room: {room.name} (ID: {room.id})', 'success')
        return redirect(f"{url_for('chat.index')}?room_id={room_id_int}")
    except ValueError:
        flash('Invalid room ID. Please enter a number.', 'error')
        return redirect(url_for('chat.index'))
    except Exception as e:
        flash('An error occurred while joining the room.', 'error')
        return redirect(url_for('chat.index'))


@chat_bp.route('/api/messages/<int:room_id>')
@login_required
def get_messages(room_id):
    """API endpoint to get messages for a room"""
    try:
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        limit = request.args.get('limit', 50, type=int)
        
        # Get messages with proper error handling and eager loading
        try:
            from sqlalchemy.orm import joinedload
            messages = Message.query.options(joinedload(Message.user), joinedload(Message.room))\
                .filter_by(room_id=room_id)\
                .order_by(Message.timestamp.desc())\
                .limit(limit)\
                .all()
        except Exception as query_error:
            print(f"Database query error: {query_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Database error: {str(query_error)}'}), 500
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Convert to dict and handle any serialization errors
        messages_data = []
        for message in messages:
            try:
                message_dict = message.to_dict()
                # Ensure all required fields are present
                if message_dict and 'id' in message_dict:
                    messages_data.append(message_dict)
            except Exception as e:
                print(f"Error serializing message {message.id}: {e}")
                import traceback
                traceback.print_exc()
                # Skip this message but continue with others
                continue
        
        return jsonify(messages_data)
    except Exception as e:
        print(f"Error in get_messages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/rooms')
@login_required
def get_rooms():
    """API endpoint to get rooms user has joined (has messages in)"""
    # Only return rooms where the current user has sent at least one message
    user_rooms = Room.query.join(Message).filter(
        Message.user_id == current_user.id
    ).distinct().order_by(Room.created_at.desc()).all()
    
    return jsonify([room.to_dict() for room in user_rooms])


@chat_bp.route('/api/online-users/<int:room_id>')
@login_required
def get_online_users(room_id):
    """API endpoint to get online users in a specific room"""
    try:
        room = Room.query.get(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        # Get users who have messages in this room and are online
        from sqlalchemy import distinct
        room_user_ids = db.session.query(distinct(Message.user_id)).filter_by(room_id=room_id).all()
        user_ids = [uid[0] for uid in room_user_ids]
        
        if user_ids:
            users = User.query.filter(
                User.id.in_(user_ids),
                User.is_online == True
            ).all()
        else:
            users = []
        
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message (only by the sender)"""
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Only allow the message sender to delete their own message
        if message.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized: You can only delete your own messages'}), 403
        
        room_id = message.room_id
        
        # Delete associated audio file if it's an audio message
        if message.message_type == 'audio' and message.content:
            import os
            audio_path = message.content
            if audio_path.startswith('/'):
                audio_path = audio_path[1:]  # Remove leading slash
            # Try to find and delete the audio file
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), audio_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"Warning: Could not delete audio file: {e}")
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'success': True, 'message_id': message_id, 'room_id': room_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@login_required
def delete_room(room_id):
    """Delete a room (only by the creator)"""
    try:
        room = Room.query.get(room_id)
        
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        # Only allow the room creator to delete the room
        if room.created_by != current_user.id:
            return jsonify({'error': 'Unauthorized: You can only delete rooms you created'}), 403
        
        # Prevent deletion of global room
        if room.is_global:
            return jsonify({'error': 'Cannot delete the global room'}), 400
        
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
        
        return jsonify({'success': True, 'room_id': room_id, 'room_name': room_name})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/search-gifs')
@login_required
def search_gifs():
    """Search GIFs using Giphy API"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Giphy API (using public beta key - replace with your own for production)
    # Get free API key from https://developers.giphy.com/
    api_key = os.environ.get('GIPHY_API_KEY', 'GlVGYHkr3WSBnllca54iNt0yFbjz7L65')  # Public beta key
    url = f'https://api.giphy.com/v1/gifs/search'
    
    try:
        response = requests.get(url, params={
            'api_key': api_key,
            'q': query,
            'limit': limit,
            'rating': 'g'  # General audience
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            gifs = []
            for gif in data.get('data', []):
                gifs.append({
                    'id': gif.get('id'),
                    'url': gif.get('images', {}).get('original', {}).get('url'),
                    'preview': gif.get('images', {}).get('preview_gif', {}).get('url'),
                    'title': gif.get('title', '')
                })
            return jsonify({'gifs': gifs}), 200
        else:
            return jsonify({'error': 'Failed to fetch GIFs'}), 500
    except Exception as e:
        return jsonify({'error': f'Error searching GIFs: {str(e)}'}), 500


@chat_bp.route('/api/trending-gifs')
@login_required
def trending_gifs():
    """Get trending GIFs from Giphy"""
    limit = request.args.get('limit', 20, type=int)
    api_key = os.environ.get('GIPHY_API_KEY', 'GlVGYHkr3WSBnllca54iNt0yFbjz7L65')
    url = f'https://api.giphy.com/v1/gifs/trending'
    
    try:
        response = requests.get(url, params={
            'api_key': api_key,
            'limit': limit,
            'rating': 'g'
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            gifs = []
            for gif in data.get('data', []):
                gifs.append({
                    'id': gif.get('id'),
                    'url': gif.get('images', {}).get('original', {}).get('url'),
                    'preview': gif.get('images', {}).get('preview_gif', {}).get('url'),
                    'title': gif.get('title', '')
                })
            return jsonify({'gifs': gifs}), 200
        else:
            return jsonify({'error': 'Failed to fetch trending GIFs'}), 500
    except Exception as e:
        return jsonify({'error': f'Error fetching trending GIFs: {str(e)}'}), 500

