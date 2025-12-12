/**
 * Sampark Setu - Enhanced Client-side JavaScript
 * Handles SocketIO, voice recording, GIF search, room management, and mobile UI
 */

// Initialize SocketIO connection
const socket = io();

// Application state
let currentRoomId = null;
let currentRoomName = null;
let typingTimeout = null;
let isTyping = false;
let userColors = {};
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingStartTime = null;

// Common emojis
const commonEmojis = [
    '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇',
    '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚',
    '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩',
    '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
    '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬',
    '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗',
    '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯',
    '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐',
    '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈',
    '👋', '🤚', '🖐', '✋', '🖖', '👌', '🤏', '✌️', '🤞', '🤟',
    '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍', '👎',
    '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝', '🙏',
    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
    '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️'
];

// Utility Functions
function getUserColor(userId) {
    if (!userColors[userId]) {
        const colors = [
            '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#ef4444',
            '#f59e0b', '#10b981', '#06b6d4', '#3b82f6', '#a855f7'
        ];
        userColors[userId] = colors[userId % colors.length];
    }
    return userColors[userId];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        info: 'ℹ️',
        success: '✅',
        error: '❌',
        warning: '⚠️'
    };
    
    notification.innerHTML = `
        <span class="notification-icon">${icons[type] || icons.info}</span>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideInDown 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Mobile Navigation
function toggleSidebar(sidebarId) {
    const sidebar = document.getElementById(sidebarId);
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
    }
}

function closeSidebar(sidebarId) {
    const sidebar = document.getElementById(sidebarId);
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebar) {
        sidebar.classList.remove('active');
        if (overlay) {
            overlay.classList.remove('active');
        }
        document.body.style.overflow = '';
        console.log(`Closed sidebar: ${sidebarId}`);
    } else {
        console.warn(`Sidebar not found: ${sidebarId}`);
    }
}

// Make closeSidebar globally accessible for inline onclick handlers
window.closeSidebar = closeSidebar;

// Notification Sounds
function playNotificationSound(type = 'message') {
    // Create audio context for notification sounds
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        if (type === 'message') {
            // Two-tone message sound
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } else if (type === 'join') {
            // Ascending join sound
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(800, audioContext.currentTime + 0.15);
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.15);
        }
    } catch (error) {
        console.log('Could not play notification sound:', error);
    }
}

// Helper function to get profile picture or generate avatar
function getUserAvatar(user, size = 'medium') {
    if (user.profile_picture) {
        const initial = (user.display_name || user.username || 'U')[0].toUpperCase();
        const color = getUserColor(user.id);
        return `
            <img src="${escapeHtml(user.profile_picture)}" 
                 alt="${escapeHtml(user.display_name || user.username)}" 
                 class="profile-img-${size}" 
                 onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="profile-avatar-${size}" style="background: ${color}; display: none;">${initial}</div>
        `;
    }
    const initial = (user.display_name || user.username || 'U')[0].toUpperCase();
    const color = getUserColor(user.id);
    return `<div class="profile-avatar-${size}" style="background: ${color};">${initial}</div>`;
}

// Theme Toggle Functionality
function initThemeToggle() {
    // Get saved theme or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    // Theme toggle handlers
    const themeToggle = document.getElementById('theme-toggle');
    const themeToggleDesktop = document.getElementById('theme-toggle-desktop');
    
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    if (themeToggleDesktop) {
        themeToggleDesktop.addEventListener('click', toggleTheme);
    }
}

function updateThemeIcon(theme) {
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    const sunIconDesktop = document.getElementById('theme-icon-sun-desktop');
    const moonIconDesktop = document.getElementById('theme-icon-moon-desktop');
    
    if (theme === 'light') {
        if (sunIcon) sunIcon.style.display = 'block';
        if (moonIcon) moonIcon.style.display = 'none';
        if (sunIconDesktop) sunIconDesktop.style.display = 'block';
        if (moonIconDesktop) moonIconDesktop.style.display = 'none';
    } else {
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'block';
        if (sunIconDesktop) sunIconDesktop.style.display = 'none';
        if (moonIconDesktop) moonIconDesktop.style.display = 'block';
    }
}

// Message Rendering
function addMessage(messageData, isOwnMessage = false) {
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) return;
    
    // Remove welcome message
    const welcomeMsg = messagesList.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Check for date divider
    const lastMessage = messagesList.lastElementChild;
    let needsDateDivider = false;
    
    if (lastMessage && !lastMessage.classList.contains('message-date-divider')) {
        const lastTimestamp = lastMessage.dataset.timestamp;
        if (lastTimestamp) {
            const lastDate = new Date(lastTimestamp).toDateString();
            const currentDate = new Date(messageData.timestamp).toDateString();
            if (lastDate !== currentDate) {
                needsDateDivider = true;
            }
        }
    } else if (!lastMessage) {
        needsDateDivider = true;
    }
    
    if (needsDateDivider) {
        const dateDivider = document.createElement('div');
        dateDivider.className = 'message-date-divider';
        dateDivider.textContent = formatDate(messageData.timestamp);
        messagesList.appendChild(dateDivider);
    }
    
    // Create message element
    const messageItem = document.createElement('div');
    messageItem.className = `message-item ${isOwnMessage ? 'own-message' : 'other-message'}`;
    messageItem.dataset.timestamp = messageData.timestamp;
    messageItem.dataset.messageId = messageData.id;
    
    const userColor = getUserColor(messageData.user_id);
    const messageType = (messageData.message_type || 'text').toLowerCase();
    const displayName = messageData.display_name || messageData.username || 'Unknown';
    
    // Debug logging
    if (messageType === 'audio') {
        console.log('Rendering audio message:', messageData);
    }
    
    let messageContent = '';
    
    if (messageType === 'gif') {
        messageContent = `
            <div class="message-gif">
                <img src="${escapeHtml(messageData.content)}" alt="GIF" loading="lazy">
            </div>
        `;
    } else if (messageType === 'image') {
        messageContent = `
            <div class="message-image">
                <img src="${escapeHtml(messageData.content)}" alt="${escapeHtml(messageData.file_name || 'Image')}" loading="lazy" onclick="window.open('${escapeHtml(messageData.content)}', '_blank')">
                ${messageData.file_name ? `<div class="file-name">${escapeHtml(messageData.file_name)}</div>` : ''}
            </div>
        `;
    } else if (messageType === 'video') {
        let videoUrl = messageData.content || '';
        if (videoUrl && !videoUrl.startsWith('http') && !videoUrl.startsWith('/')) {
            videoUrl = '/' + videoUrl;
        }
        const safeVideoUrl = escapeHtml(videoUrl);
        
        const urlParts = safeVideoUrl.split('.');
        const ext = urlParts.length > 1 ? urlParts[urlParts.length - 1].toLowerCase() : 'mp4';
        const mimeTypes = {
            'mp4': 'video/mp4', 'webm': 'video/webm', 'ogg': 'video/ogg',
            'mov': 'video/quicktime', 'avi': 'video/x-msvideo'
        };
        const mimeType = mimeTypes[ext] || 'video/mp4';
        
        messageContent = `
            <div class="message-video">
                <video controls preload="metadata" style="max-width: 100%; max-height: 400px; border-radius: 8px;">
                    <source src="${safeVideoUrl}" type="${mimeType}">
                    <source src="${safeVideoUrl}">
                    <p>Your browser does not support video playback. <a href="${safeVideoUrl}" download style="color: inherit; text-decoration: underline;">Download video</a></p>
                </video>
                ${messageData.file_name ? `<div class="file-name">${escapeHtml(messageData.file_name)}</div>` : ''}
            </div>
        `;
    } else if (messageType === 'file') {
        let fileUrl = messageData.content || '';
        if (fileUrl && !fileUrl.startsWith('http') && !fileUrl.startsWith('/')) {
            fileUrl = '/' + fileUrl;
        }
        const safeFileUrl = escapeHtml(fileUrl);
        const fileName = escapeHtml(messageData.file_name || 'File');
        const fileExt = fileName.split('.').pop().toLowerCase();
        
        // Get file icon based on extension
        const fileIcon = getFileIcon(fileExt);
        
        messageContent = `
            <div class="message-file">
                <div class="file-attachment">
                    <div class="file-icon">${fileIcon}</div>
                    <div class="file-info">
                        <div class="file-name">${fileName}</div>
                        <a href="${safeFileUrl}" download="${fileName}" class="file-download-btn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7 10 12 15 17 10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            Download
                        </a>
                    </div>
                </div>
            </div>
        `;
    } else if (messageType === 'audio') {
        // Ensure URL is absolute if it's relative
        let audioUrl = messageData.content || '';
        console.log('Audio URL before processing:', audioUrl);
        
        if (audioUrl && !audioUrl.startsWith('http') && !audioUrl.startsWith('/')) {
            audioUrl = '/' + audioUrl;
        }
        const safeAudioUrl = escapeHtml(audioUrl);
        console.log('Audio URL after processing:', safeAudioUrl);
        
        // Get file extension to determine MIME type
        const urlParts = safeAudioUrl.split('.');
        const ext = urlParts.length > 1 ? urlParts[urlParts.length - 1].toLowerCase() : 'webm';
        const mimeTypes = {
            'webm': 'audio/webm',
            'mp3': 'audio/mpeg',
            'ogg': 'audio/ogg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4'
        };
        const mimeType = mimeTypes[ext] || 'audio/webm';
        
        messageContent = `
            <div class="message-audio">
                <div class="audio-icon">🎤</div>
                <div class="audio-player">
                    <audio 
                        controls 
                        controlsList="nodownload"
                        preload="metadata" 
                        style="width: 100%; min-width: 300px; max-width: 500px; height: 48px; display: block;"
                        onerror="console.error('Audio load error:', this.error, this.src);"
                        onloadstart="console.log('Audio loading:', this.src);"
                        oncanplay="console.log('Audio can play:', this.src); this.style.opacity = '1';"
                        onloadedmetadata="this.style.opacity = '1';">
                        <source src="${safeAudioUrl}" type="${mimeType}">
                        <source src="${safeAudioUrl}">
                        <p>Your browser does not support audio playback. <a href="${safeAudioUrl}" download style="color: inherit; text-decoration: underline;">Download audio</a></p>
                    </audio>
                </div>
            </div>
        `;
    } else {
        messageContent = `<div class="message-content">${escapeHtml(messageData.content)}</div>`;
    }
    
    // Get user avatar
    const userAvatar = getUserAvatar({
        profile_picture: messageData.profile_picture,
        display_name: displayName,
        username: messageData.username,
        id: messageData.user_id
    }, 'small');
    
    // Add delete button for own messages
    const deleteButton = isOwnMessage ? `
        <button class="message-delete-btn" onclick="event.stopPropagation(); window.deleteMessage(${messageData.id}); return false;" title="Delete message">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
        </button>
    ` : '';
    
    messageItem.innerHTML = `
        ${!isOwnMessage ? `<div class="message-avatar">${userAvatar}</div>` : ''}
        <div class="message-content-wrapper">
            <div class="message-header">
                <span class="message-username" style="color: ${isOwnMessage ? userColor : ''}">
                    ${escapeHtml(displayName)}
                    ${messageData.is_online !== false ? '<span class="message-online-indicator"></span>' : ''}
                </span>
                <div class="message-header-right">
                    ${deleteButton}
                    <span class="message-time">${messageData.formatted_time || formatTime(messageData.timestamp)}</span>
                </div>
            </div>
            <div class="message-bubble">
                ${messageContent}
            </div>
        </div>
        ${isOwnMessage ? `<div class="message-avatar">${userAvatar}</div>` : ''}
    `;
    
    messagesList.appendChild(messageItem);
    scrollToBottom();
}

// Load Messages
async function loadMessages(roomId) {
    if (!roomId) {
        console.error('No room ID provided');
        return;
    }
    
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) {
        console.error('Messages list element not found');
        return;
    }
    
    // Show loading state
    messagesList.innerHTML = '<div class="welcome-message"><div class="welcome-icon">⏳</div><p>Loading messages...</p></div>';
    
    try {
        // Add timeout to fetch request (10 seconds)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const response = await fetch(`/api/messages/${roomId}`, {
            signal: controller.signal,
            credentials: 'include',  // Include cookies/session for authentication
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', response.status, errorText);
            let errorMessage = `HTTP ${response.status}: Failed to load messages`;
            
            // Check for authentication issues
            if (response.status === 401 || response.status === 403) {
                errorMessage = 'Authentication failed. Please refresh the page and log in again.';
                console.error('Authentication error - session may have expired');
            } else {
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorMessage;
                } catch (e) {
                    errorMessage = errorText || errorMessage;
                }
            }
            throw new Error(errorMessage);
        }
        
        let messages;
        try {
            const responseText = await response.text();
            if (!responseText) {
                messages = [];
            } else {
                messages = JSON.parse(responseText);
            }
        } catch (jsonError) {
            console.error('JSON parse error:', jsonError, 'Response:', await response.text());
            throw new Error('Invalid response from server. Please refresh the page.');
        }
        
        messagesList.innerHTML = '';
        
        if (!messages || !Array.isArray(messages) || messages.length === 0) {
            messagesList.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">💬</div>
                    <h3>Welcome to ${currentRoomName || 'this room'}!</h3>
                    <p>Be the first to send a message.</p>
                </div>
            `;
            return;
        }
        
        const currentUserId = parseInt(document.querySelector('#sidebar-user-avatar')?.dataset?.userId || document.querySelector('.sidebar-header .user-avatar')?.dataset?.userId || '0');
        let lastDate = null;
        
        messages.forEach((message, index) => {
                if (!message) {
                    console.warn('Null message at index:', index);
                    return;
                }
                
                if (!message.id) {
                    console.warn('Message missing ID:', message);
                    return;
                }
                
                try {
                    // Handle date divider
                    if (message.timestamp) {
                        const messageDate = new Date(message.timestamp).toDateString();
                        if (lastDate !== messageDate) {
                            const dateDivider = document.createElement('div');
                            dateDivider.className = 'message-date-divider';
                            dateDivider.textContent = formatDate(message.timestamp);
                            messagesList.appendChild(dateDivider);
                            lastDate = messageDate;
                        }
                    }
                    
                    const isOwnMessage = message.user_id === currentUserId;
                    addMessage(message, isOwnMessage);
                } catch (msgError) {
                    console.error('Error processing message:', msgError, message);
                    // Continue with next message instead of stopping
                }
            });
            
            scrollToBottom();
    } catch (error) {
        console.error('Error loading messages:', error);
        
        let errorMessage = 'Failed to load messages. Please try again.';
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please check your connection and try again.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        messagesList.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">⚠️</div>
                <h3>Failed to load messages</h3>
                <p>${escapeHtml(errorMessage)}</p>
                <button class="btn btn-primary" onclick="loadMessages(${roomId})" style="margin-top: 12px;">Retry</button>
            </div>
        `;
        showNotification(errorMessage, 'error');
    }
}

// Room Management
function joinRoom(roomId, roomName) {
    if (!roomId || !roomName) {
        console.error('Invalid room ID or name');
        return;
    }
    
    if (currentRoomId === roomId) {
        console.log('Already in this room');
        return;
    }
    
    // Leave previous room
    if (currentRoomId) {
        socket.emit('leave_room', { room_id: currentRoomId });
    }
    
    currentRoomId = roomId;
    currentRoomName = roomName;
    
    // Update UI
    const currentRoomNameEl = document.getElementById('current-room-name');
    const mobileRoomNameEl = document.getElementById('mobile-room-name');
    const roomMetaEl = document.getElementById('room-meta');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (currentRoomNameEl) currentRoomNameEl.textContent = roomName;
    if (mobileRoomNameEl) mobileRoomNameEl.textContent = roomName;
    if (roomMetaEl) roomMetaEl.textContent = 'Active now';
    if (messageInput) messageInput.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    
    // Update active room in sidebar
    document.querySelectorAll('.room-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.roomId) === roomId) {
            item.classList.add('active');
        }
    });
    
    // Join room via SocketIO
    socket.emit('join_room', { room_id: roomId });
    
    // Load messages after a short delay to ensure room is joined
    setTimeout(() => {
        loadMessages(roomId);
        // Refresh rooms list to include newly joined room
        refreshRoomsList();
        // Load room-specific online users
        loadRoomOnlineUsers(roomId);
    }, 100);
    
    // Close mobile sidebar
    closeSidebar('rooms-sidebar');
}

// Load room-specific online users
async function loadRoomOnlineUsers(roomId) {
    if (!roomId) {
        updateOnlineUsersList([]);
        return;
    }
    
    try {
        const response = await fetch(`/api/online-users/${roomId}`, {
            credentials: 'include'  // Include cookies/session for authentication
        });
        if (response.ok) {
            const users = await response.json();
            updateOnlineUsersList(users);
        } else {
            updateOnlineUsersList([]);
        }
    } catch (error) {
        console.error('Error loading room users:', error);
        updateOnlineUsersList([]);
    }
}

// Global function for template onclick
window.joinRoomById = function(roomId, roomName) {
    joinRoom(roomId, roomName);
};

// Voice Recording
async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        recordingStartTime = Date.now();
        
        // Update UI
        const voiceModal = document.getElementById('voice-modal');
        const voiceStartBtn = document.getElementById('voice-start-btn');
        const voiceStopBtn = document.getElementById('voice-stop-btn');
        const voiceSendBtn = document.getElementById('voice-send-btn');
        const voiceVisualizer = document.getElementById('voice-visualizer');
        const voiceRecordBtn = document.getElementById('voice-record-btn');
        
        if (voiceStartBtn) voiceStartBtn.style.display = 'none';
        if (voiceStopBtn) voiceStopBtn.style.display = 'block';
        if (voiceVisualizer) voiceVisualizer.querySelector('.voice-wave').classList.add('recording');
        if (voiceRecordBtn) voiceRecordBtn.classList.add('recording');
        
        // Start timer
        recordingTimer = setInterval(updateVoiceTimer, 1000);
        
        showNotification('Recording started', 'info');
    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('Failed to start recording. Please allow microphone access.', 'error');
    }
}

function stopVoiceRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        clearInterval(recordingTimer);
        recordingTimer = null;
        
        // Update UI
        const voiceStopBtn = document.getElementById('voice-stop-btn');
        const voiceSendBtn = document.getElementById('voice-send-btn');
        const voiceVisualizer = document.getElementById('voice-visualizer');
        const voiceRecordBtn = document.getElementById('voice-record-btn');
        const voicePreview = document.getElementById('voice-preview');
        
        if (voiceStopBtn) voiceStopBtn.style.display = 'none';
        if (voiceVisualizer) voiceVisualizer.querySelector('.voice-wave').classList.remove('recording');
        if (voiceRecordBtn) voiceRecordBtn.classList.remove('recording');
        
        // Create audio blob and preview
        setTimeout(() => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            if (voicePreview) {
                voicePreview.src = audioUrl;
                voicePreview.style.display = 'block';
            }
            
            if (voiceSendBtn) {
                voiceSendBtn.style.display = 'block';
                voiceSendBtn.onclick = () => sendVoiceMessage(audioBlob);
            }
        }, 100);
    }
}

function updateVoiceTimer() {
    if (recordingStartTime) {
        const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timerEl = document.getElementById('voice-timer');
        if (timerEl) {
            timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }
}

async function sendVoiceMessage(audioBlob) {
    if (!currentRoomId) {
        showNotification('Please join a room first', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice-message.webm');
        
        const response = await fetch('/upload_audio', {
            method: 'POST',
            credentials: 'include',  // Include cookies/session for authentication
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.url) {
            console.log('Sending audio message with URL:', data.url);
            // Send message via SocketIO
            socket.emit('send_message', {
                content: data.url,
                room_id: currentRoomId,
                message_type: 'audio'
            });
            
            // Close modal and reset
            closeModal('voice-modal');
            resetVoiceRecorder();
            showNotification('Voice message sent', 'success');
        } else {
            console.error('Audio upload failed:', data);
            showNotification(data.error || 'Failed to upload audio', 'error');
        }
    } catch (error) {
        console.error('Error sending voice message:', error);
        showNotification('Failed to send voice message', 'error');
    }
}

function resetVoiceRecorder() {
    audioChunks = [];
    recordingStartTime = null;
    clearInterval(recordingTimer);
    recordingTimer = null;
    
    const voiceTimer = document.getElementById('voice-timer');
    const voicePreview = document.getElementById('voice-preview');
    const voiceStartBtn = document.getElementById('voice-start-btn');
    const voiceStopBtn = document.getElementById('voice-stop-btn');
    const voiceSendBtn = document.getElementById('voice-send-btn');
    const voiceRecordBtn = document.getElementById('voice-record-btn');
    
    if (voiceTimer) voiceTimer.textContent = '00:00';
    if (voicePreview) {
        voicePreview.src = '';
        voicePreview.style.display = 'none';
    }
    if (voiceStartBtn) voiceStartBtn.style.display = 'block';
    if (voiceStopBtn) voiceStopBtn.style.display = 'none';
    if (voiceSendBtn) voiceSendBtn.style.display = 'none';
    if (voiceRecordBtn) voiceRecordBtn.classList.remove('recording');
}

// GIF Search
async function searchGIFs(query = '') {
    const gifResults = document.getElementById('gif-results');
    if (!gifResults) return;
    
    gifResults.innerHTML = '<div class="gif-loading">Loading GIFs...</div>';
    
    try {
        const endpoint = query ? '/api/search-gifs' : '/api/trending-gifs';
        const url = query 
            ? `${endpoint}?q=${encodeURIComponent(query)}&limit=20`
            : `${endpoint}?limit=20`;
        
        const response = await fetch(url, {
            credentials: 'include'  // Include cookies/session for authentication
        });
        const data = await response.json();
        
        if (data.gifs && data.gifs.length > 0) {
            gifResults.innerHTML = '';
            data.gifs.forEach(gif => {
                const gifItem = document.createElement('div');
                gifItem.className = 'gif-item';
                gifItem.innerHTML = `<img src="${gif.preview || gif.url}" alt="${gif.title}" loading="lazy">`;
                gifItem.onclick = () => sendGIF(gif.url);
                gifResults.appendChild(gifItem);
            });
        } else {
            gifResults.innerHTML = '<div class="gif-loading">No GIFs found</div>';
        }
    } catch (error) {
        console.error('Error searching GIFs:', error);
        gifResults.innerHTML = '<div class="gif-loading">Error loading GIFs</div>';
    }
}

function sendGIF(gifUrl) {
    if (!currentRoomId) {
        showNotification('Please join a room first', 'error');
        return;
    }
    
    socket.emit('send_message', {
        content: gifUrl,
        room_id: currentRoomId,
        message_type: 'gif'
    });
    
    closeModal('gif-modal');
    showNotification('GIF sent', 'success');
}

// Modal Management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Initialize Emoji Picker
function initEmojiPicker() {
    const emojiGrid = document.getElementById('emoji-grid');
    if (!emojiGrid) return;
    
    commonEmojis.forEach(emoji => {
        const emojiItem = document.createElement('div');
        emojiItem.className = 'emoji-item';
        emojiItem.textContent = emoji;
        emojiItem.addEventListener('click', () => {
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.value += emoji;
                messageInput.focus();
            }
            closeModal('emoji-modal');
        });
        emojiGrid.appendChild(emojiItem);
    });
}

// Delete Message
async function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    
    try {
        // Use SocketIO to delete message
        socket.emit('delete_message', { message_id: messageId });
    } catch (error) {
        console.error('Error deleting message:', error);
        showNotification('Failed to delete message', 'error');
    }
}

// Delete Room
async function deleteRoom(roomId, roomName) {
    if (!confirm(`Are you sure you want to delete the room "${roomName}"? This action cannot be undone and all messages in this room will be deleted.`)) {
        return;
    }
    
    try {
        // Use SocketIO to delete room
        socket.emit('delete_room', { room_id: roomId });
    } catch (error) {
        console.error('Error deleting room:', error);
        showNotification('Failed to delete room', 'error');
    }
}

// Upload and send file attachment
async function uploadAndSendFile(file) {
    if (!currentRoomId) {
        showNotification('Please join a room first', 'error');
        return;
    }
    
    // Check file size (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        showNotification(`File too large. Maximum size: ${maxSize / (1024 * 1024)}MB`, 'error');
        return;
    }
    
    // Show upload progress
    const notificationId = 'upload-' + Date.now();
    showUploadProgress(notificationId, file.name);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload_attachment', {
            method: 'POST',
            credentials: 'include',  // Include cookies/session for authentication
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Send message with file
            socket.emit('send_message', {
                content: data.url,
                room_id: currentRoomId,
                message_type: data.file_type,
                file_name: data.original_filename
            });
            
            removeUploadProgress(notificationId);
            showNotification(`File "${file.name}" uploaded successfully`, 'success');
        } else {
            removeUploadProgress(notificationId);
            showNotification(data.error || 'Failed to upload file', 'error');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        removeUploadProgress(notificationId);
        showNotification('Failed to upload file', 'error');
    }
}

// Show upload progress notification
function showUploadProgress(id, fileName) {
    const notification = document.createElement('div');
    notification.id = id;
    notification.className = 'upload-progress-notification';
    notification.innerHTML = `
        <div class="upload-progress-content">
            <div class="upload-spinner"></div>
            <span>Uploading ${escapeHtml(fileName)}...</span>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);
}

// Remove upload progress notification
function removeUploadProgress(id) {
    const notification = document.getElementById(id);
    if (notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }
}

// Get file icon based on extension
function getFileIcon(ext) {
    const icons = {
        'pdf': '📄',
        'doc': '📝', 'docx': '📝',
        'xls': '📊', 'xlsx': '📊',
        'ppt': '📽️', 'pptx': '📽️',
        'txt': '📄', 'rtf': '📄',
        'csv': '📊',
        'zip': '📦', 'rar': '📦', '7z': '📦',
        'mp3': '🎵', 'wav': '🎵', 'ogg': '🎵',
        'mp4': '🎬', 'avi': '🎬', 'mov': '🎬',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️'
    };
    return icons[ext.toLowerCase()] || '📎';
}

// Make functions globally accessible for onclick handlers
window.deleteMessage = deleteMessage;
window.deleteRoom = deleteRoom;

// SocketIO Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('connected', (data) => {
    console.log('Connection confirmed:', data);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    showNotification('Connection lost. Reconnecting...', 'warning');
});

socket.on('error', (data) => {
    showNotification(data.message || 'An error occurred', 'error');
});

socket.on('new_message', (messageData) => {
    const currentUserId = parseInt(document.querySelector('.sidebar-header .user-avatar')?.dataset.userId || '0');
    const isOwnMessage = messageData.user_id === currentUserId;
    
    // Play notification sound if message is not from current user
    if (!isOwnMessage && messageData.room_id === currentRoomId) {
        playNotificationSound('message');
    }
    
    addMessage(messageData, isOwnMessage);
});

socket.on('user_joined', (data) => {
    if (data.room_id === currentRoomId) {
        showNotification(`${data.username} joined ${data.room_name}`, 'info');
        // Play join sound
        playNotificationSound('join');
        // Refresh room users
        loadRoomOnlineUsers(currentRoomId);
    }
});

socket.on('user_left', (data) => {
    if (data.room_id === currentRoomId) {
        showNotification(`${data.username} left ${data.room_name}`, 'info');
        // Refresh room users
        loadRoomOnlineUsers(currentRoomId);
    }
});

socket.on('user_typing', (data) => {
    const currentUserId = parseInt(document.querySelector('.sidebar-header .user-avatar')?.dataset.userId || '0');
    if (data.room_id === currentRoomId && data.user_id !== currentUserId) {
        const typingIndicator = document.getElementById('typing-indicator');
        const typingText = document.getElementById('typing-text');
        if (typingIndicator && typingText) {
            typingText.textContent = `${data.username} is typing...`;
            typingIndicator.style.display = 'flex';
        }
    }
});

socket.on('stop_typing', (data) => {
    if (data.room_id === currentRoomId) {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }
});

socket.on('user_status', (data) => {
    updateUserStatus(data.user_id, data.is_online);
});

socket.on('online_users', (data) => {
    // Handle both old format (array) and new format (object with room_id and users)
    if (Array.isArray(data)) {
        updateOnlineUsersList(data);
    } else if (data && data.users) {
        // Only update if it's for the current room
        if (data.room_id === currentRoomId) {
            updateOnlineUsersList(data.users);
        }
    }
});

socket.on('room_members_update', (data) => {
    if (data.room_id === currentRoomId && data.members) {
        updateOnlineUsersList(data.members);
    }
});

socket.on('room_joined', (data) => {
    console.log('Joined room:', data);
    if (data.members) {
        updateOnlineUsersList(data.members);
    }
    // Request room-specific online users
    if (currentRoomId) {
        socket.emit('request_online_users', { room_id: currentRoomId });
    }
});

socket.on('rooms_list', (rooms) => {
    // This event is deprecated - we use refreshRoomsList() instead
    // But keep it for backward compatibility
    updateRoomsList(rooms);
});

socket.on('room_joined', (data) => {
    console.log('Joined room:', data);
});

socket.on('room_left', (data) => {
    console.log('Left room:', data);
});

socket.on('message_deleted', (data) => {
    const messageId = data.message_id;
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        messageElement.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            messageElement.remove();
        }, 300);
    }
});

socket.on('room_deleted', (data) => {
    const roomId = data.room_id;
    const roomName = data.room_name;
    
    // Remove room from UI
    const roomElement = document.querySelector(`[data-room-id="${roomId}"]`);
    if (roomElement) {
        roomElement.style.transition = 'opacity 0.3s ease-out';
        roomElement.style.opacity = '0';
        setTimeout(() => {
            roomElement.remove();
        }, 300);
    }
    
    // If deleted room was currently active, clear the chat
    if (currentRoomId === roomId) {
        const messagesList = document.getElementById('messages-list');
        if (messagesList) {
            messagesList.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">💬</div>
                    <h3>Room Deleted</h3>
                    <p>The room "${escapeHtml(roomName)}" has been deleted.</p>
                </div>
            `;
        }
        currentRoomId = null;
        const roomNameElement = document.getElementById('current-room-name');
        if (roomNameElement) {
            roomNameElement.textContent = 'Select a room';
        }
    }
    
    showNotification(`Room "${roomName}" has been deleted`, 'info');
    
    // Refresh rooms list
    refreshRoomsList();
});

socket.on('message_deleted', (data) => {
    const messageId = data.message_id;
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        messageElement.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            messageElement.remove();
        }, 300);
    }
});

socket.on('room_deleted', (data) => {
    const roomId = data.room_id;
    const roomName = data.room_name;
    
    // Remove room from UI
    const roomElement = document.querySelector(`[data-room-id="${roomId}"]`);
    if (roomElement) {
        roomElement.style.transition = 'opacity 0.3s ease-out';
        roomElement.style.opacity = '0';
        setTimeout(() => {
            roomElement.remove();
        }, 300);
    }
    
    // If deleted room was currently active, clear the chat
    if (currentRoomId === roomId) {
        const messagesList = document.getElementById('messages-list');
        if (messagesList) {
            messagesList.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">💬</div>
                    <h3>Room Deleted</h3>
                    <p>The room "${escapeHtml(roomName)}" has been deleted.</p>
                </div>
            `;
        }
        currentRoomId = null;
        document.getElementById('current-room-name').textContent = 'Select a room';
    }
    
    showNotification(`Room "${roomName}" has been deleted`, 'info');
    
    // Refresh rooms list
    refreshRoomsList();
});

// Update Online Users List - Room Specific
function updateOnlineUsersList(users) {
    const usersList = document.getElementById('users-list');
    const onlineCount = document.getElementById('online-count');
    
    if (!usersList) return;
    
    if (onlineCount) {
        onlineCount.textContent = users.length > 0 ? `${users.length} in room` : 'No one in room';
    }
    
    usersList.innerHTML = '';
    
    if (!users || users.length === 0) {
        usersList.innerHTML = `
            <div class="empty-state">
                <p>No users in this room</p>
            </div>
        `;
        return;
    }
    
    users.forEach(user => {
        const userItem = document.createElement('div');
        userItem.className = 'user-item';
        userItem.dataset.userId = user.id;
        
        const isOnline = user.is_online !== false; // Default to true if not specified
        
            const userAvatar = getUserAvatar({
                profile_picture: user.profile_picture,
                display_name: user.display_name,
                username: user.username,
                id: user.id
            }, 'small');
            
            userItem.innerHTML = `
                <div class="user-avatar-container">
                    ${userAvatar}
                </div>
                <span class="username">${escapeHtml(user.display_name || user.username)}</span>
                <span class="status-indicator ${isOnline ? 'online' : 'offline'}"></span>
            `;
        
        usersList.appendChild(userItem);
    });
}

// Update Rooms List - Only show joined rooms
function updateRoomsList(rooms) {
    const roomsList = document.getElementById('rooms-list');
    if (!roomsList) return;
    
    // Get current user ID from sidebar
    const currentUserId = parseInt(document.querySelector('#sidebar-user-avatar')?.dataset?.userId || '0');
    
    // Filter to only show rooms user has joined (has messages in)
    // This is handled server-side, but we can also filter client-side
    const joinedRooms = rooms.filter(room => {
        // Only show rooms that are in the list (meaning user has joined)
        return true;
    });
    
    roomsList.innerHTML = '';
    
    if (joinedRooms.length === 0) {
        roomsList.innerHTML = `
            <div class="empty-state">
                <p>No rooms joined yet</p>
                <p class="empty-hint">Join a room by ID to start chatting</p>
            </div>
        `;
        return;
    }
    
    joinedRooms.forEach(room => {
        const roomItem = document.createElement('div');
        roomItem.className = `room-item ${room.id === currentRoomId ? 'active' : ''}`;
        roomItem.dataset.roomId = room.id;
        roomItem.dataset.roomName = room.name;
        roomItem.dataset.createdBy = room.created_by || 0;
        roomItem.style.cursor = 'pointer';
        
        // Add delete button if user is the creator
        const canDelete = room.created_by === currentUserId;
        const deleteButton = canDelete ? `
            <button class="room-delete-btn" onclick="event.stopPropagation(); event.preventDefault(); window.deleteRoom(${room.id}, '${escapeHtml(room.name).replace(/'/g, "\\'")}'); return false;" title="Delete room">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        ` : '';
        
        roomItem.innerHTML = `
            <div class="room-icon">💬</div>
            <div class="room-info">
                <div class="room-name">${escapeHtml(room.name)}</div>
                <div class="room-id">ID: ${room.id}</div>
                ${room.description ? `<div class="room-description">${escapeHtml(room.description)}</div>` : ''}
            </div>
            ${deleteButton}
        `;
        
        // Add click handler to entire room item
        roomItem.addEventListener('click', (e) => {
            // Don't navigate if clicking delete button or its children
            if (e.target.closest('.room-delete-btn') || e.target.classList.contains('room-delete-btn')) {
                e.stopPropagation();
                e.preventDefault();
                return false;
            }
            joinRoom(room.id, room.name);
        });
        
        // Also add explicit handler to delete button if it exists
        if (canDelete) {
            const deleteBtn = roomItem.querySelector('.room-delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    deleteRoom(room.id, room.name);
                    return false;
                });
            }
        }
        
        roomsList.appendChild(roomItem);
    });
}

// Refresh rooms list after joining
async function refreshRoomsList() {
    try {
        const response = await fetch('/api/rooms', {
            credentials: 'include'  // Include cookies/session for authentication
        });
        const rooms = await response.json();
        updateRoomsList(rooms);
    } catch (error) {
        console.error('Error refreshing rooms list:', error);
    }
}

// Update User Status
function updateUserStatus(userId, isOnline) {
    const userItem = document.querySelector(`.user-item[data-user-id="${userId}"]`);
    if (userItem) {
        const statusIndicator = userItem.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
        }
    }
}

// Update sidebar profile picture
function updateSidebarProfilePicture(userData = null) {
    // Check if profile was just updated
    const profileUpdated = sessionStorage.getItem('profileUpdated');
    const updatedProfile = sessionStorage.getItem('updatedProfile');
    const updatedPicture = sessionStorage.getItem('updatedProfilePicture');
    
    if (profileUpdated === 'true' && updatedProfile) {
        try {
            userData = JSON.parse(updatedProfile);
            if (updatedPicture) {
                userData.profile_picture = updatedPicture;
            }
            sessionStorage.removeItem('profileUpdated');
            sessionStorage.removeItem('updatedProfile');
            sessionStorage.removeItem('updatedProfilePicture');
        } catch (e) {
            console.error('Error parsing updated profile:', e);
        }
    }
    
    const loadProfile = userData ? Promise.resolve(userData) : fetch('/api/profile', {
        credentials: 'include'  // Include cookies/session for authentication
    }).then(response => response.json());
    
    loadProfile
        .then(user => {
            const avatarContainer = document.getElementById('sidebar-user-avatar');
            if (!avatarContainer) return;
            
            let img = document.getElementById('sidebar-profile-img');
            const placeholder = document.getElementById('sidebar-profile-placeholder');
            
            if (user.profile_picture) {
                if (img) {
                    img.src = user.profile_picture + '?t=' + Date.now(); // Cache bust
                    img.style.display = 'block';
                    if (placeholder) placeholder.style.display = 'none';
                } else {
                    // Create img element if it doesn't exist
                    img = document.createElement('img');
                    img.id = 'sidebar-profile-img';
                    img.src = user.profile_picture;
                    img.alt = user.display_name || user.username;
                    img.style.cssText = 'width: 100%; height: 100%; object-fit: cover;';
                    img.onerror = function() {
                        this.style.display = 'none';
                        if (placeholder) placeholder.style.display = 'flex';
                    };
                    if (placeholder) placeholder.style.display = 'none';
                    avatarContainer.insertBefore(img, avatarContainer.firstChild);
                }
            } else {
                if (img) img.style.display = 'none';
                if (placeholder) {
                    placeholder.style.display = 'flex';
                    placeholder.textContent = (user.display_name || user.username || 'U')[0].toUpperCase();
                }
            }
            
            // Update username/display name
            const usernameElement = document.querySelector('.user-details h3');
            if (usernameElement) {
                const nameText = user.display_name || user.username;
                const statusIndicator = usernameElement.querySelector('.status-indicator');
                usernameElement.innerHTML = `
                    ${escapeHtml(nameText)}
                    ${statusIndicator ? statusIndicator.outerHTML : '<span class="status-indicator online"></span>'}
                `;
            }
        })
        .catch(error => {
            console.error('Error loading profile:', error);
        });
}

// DOM Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme toggle
    initThemeToggle();
    
    // Load and update sidebar profile picture
    updateSidebarProfilePicture();
    
    // Initialize emoji picker
    initEmojiPicker();
    
    // Mobile navigation
    const toggleRoomsBtn = document.getElementById('toggle-rooms-sidebar');
    const toggleUsersBtn = document.getElementById('toggle-users-sidebar');
    const toggleGifSearchBtn = document.getElementById('toggle-gif-search');
    const closeUsersSidebarBtn = document.getElementById('close-users-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (toggleRoomsBtn) {
        toggleRoomsBtn.addEventListener('click', () => toggleSidebar('rooms-sidebar'));
    }
    
    if (toggleUsersBtn) {
        toggleUsersBtn.addEventListener('click', () => toggleSidebar('users-sidebar'));
    }
    
    if (toggleGifSearchBtn) {
        toggleGifSearchBtn.addEventListener('click', () => {
            openModal('gif-modal');
            searchGIFs();
        });
    }
    
    // File attachment handling
    const attachmentBtn = document.getElementById('attachment-btn');
    const fileInput = document.getElementById('file-input');
    
    if (attachmentBtn && fileInput) {
        attachmentBtn.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            if (files.length === 0) return;
            
            for (const file of files) {
                await uploadAndSendFile(file);
            }
            
            // Reset file input
            fileInput.value = '';
        });
    }
    
    if (closeUsersSidebarBtn) {
        // Add multiple event listeners to ensure it works
        closeUsersSidebarBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeSidebar('users-sidebar');
            return false;
        };
        closeUsersSidebarBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeSidebar('users-sidebar');
        }, {capture: true});
        closeUsersSidebarBtn.addEventListener('mousedown', (e) => {
            e.preventDefault();
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', () => {
            closeSidebar('rooms-sidebar');
            closeSidebar('users-sidebar');
        });
    }
    
    // Message form
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    
    if (messageForm) {
        messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (messageInput && messageInput.value.trim() && currentRoomId) {
                socket.emit('send_message', {
                    content: messageInput.value.trim(),
                    room_id: currentRoomId,
                    message_type: 'text'
                });
                messageInput.value = '';
                clearTypingTimeout();
                isTyping = false;
            }
        });
    }
    
    // Typing indicator
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            if (!currentRoomId) return;
            
            if (!isTyping) {
                isTyping = true;
                socket.emit('typing', { room_id: currentRoomId });
            }
            
            clearTypingTimeout();
            typingTimeout = setTimeout(() => {
                socket.emit('stop_typing', { room_id: currentRoomId });
                isTyping = false;
            }, 1000);
        });
    }
    
    // Emoji button
    const emojiBtn = document.getElementById('emoji-btn');
    if (emojiBtn) {
        emojiBtn.addEventListener('click', () => openModal('emoji-modal'));
    }
    
    // GIF button
    const gifBtn = document.getElementById('gif-btn');
    const headerGifBtn = document.getElementById('header-gif-btn');
    
    if (gifBtn) {
        gifBtn.addEventListener('click', () => {
            openModal('gif-modal');
            searchGIFs();
        });
    }
    
    if (headerGifBtn) {
        headerGifBtn.addEventListener('click', () => {
            openModal('gif-modal');
            searchGIFs();
        });
    }
    
    // GIF search
    const gifSearchInput = document.getElementById('gif-search-input');
    const gifSearchBtn = document.getElementById('gif-search-btn');
    const gifTabs = document.querySelectorAll('.gif-tab');
    
    if (gifSearchBtn) {
        gifSearchBtn.addEventListener('click', () => {
            if (gifSearchInput) {
                searchGIFs(gifSearchInput.value);
            }
        });
    }
    
    if (gifSearchInput) {
        gifSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchGIFs(gifSearchInput.value);
            }
        });
    }
    
    gifTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            gifTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            if (tab.dataset.tab === 'trending') {
                searchGIFs();
            } else {
                if (gifSearchInput) gifSearchInput.focus();
            }
        });
    });
    
    // Voice recording
    const voiceRecordBtn = document.getElementById('voice-record-btn');
    const voiceStartBtn = document.getElementById('voice-start-btn');
    const voiceStopBtn = document.getElementById('voice-stop-btn');
    const voiceCloseBtn = document.getElementById('voice-close');
    
    if (voiceRecordBtn) {
        voiceRecordBtn.addEventListener('click', () => openModal('voice-modal'));
    }
    
    if (voiceStartBtn) {
        voiceStartBtn.addEventListener('click', startVoiceRecording);
    }
    
    if (voiceStopBtn) {
        voiceStopBtn.addEventListener('click', stopVoiceRecording);
    }
    
    if (voiceCloseBtn) {
        voiceCloseBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                stopVoiceRecording();
            }
            closeModal('voice-modal');
            resetVoiceRecorder();
        });
    }
    
    // Modal close buttons
    const emojiClose = document.getElementById('emoji-close');
    const gifClose = document.getElementById('gif-close');
    
    if (emojiClose) {
        emojiClose.addEventListener('click', () => closeModal('emoji-modal'));
    }
    
    if (gifClose) {
        gifClose.addEventListener('click', () => closeModal('gif-modal'));
    }
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Join room by ID form
    const toggleJoinRoom = document.getElementById('toggle-join-room');
    const joinRoomForm = document.getElementById('join-room-form');
    const cancelJoinRoom = document.getElementById('cancel-join-room');
    
    if (toggleJoinRoom) {
        toggleJoinRoom.addEventListener('click', () => {
            if (joinRoomForm) {
                joinRoomForm.style.display = joinRoomForm.style.display === 'none' ? 'flex' : 'none';
            }
        });
    }
    
    if (cancelJoinRoom) {
        cancelJoinRoom.addEventListener('click', () => {
            if (joinRoomForm) {
                joinRoomForm.style.display = 'none';
                const roomIdInput = document.getElementById('room-id-input');
                if (roomIdInput) roomIdInput.value = '';
            }
        });
    }
    
    if (joinRoomForm) {
        joinRoomForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const roomIdInput = document.getElementById('room-id-input');
            
            if (!roomIdInput || !roomIdInput.value.trim()) {
                showNotification('Please enter a room ID', 'error');
                return;
            }
            
            const roomId = parseInt(roomIdInput.value.trim());
            if (isNaN(roomId)) {
                showNotification('Invalid room ID. Please enter a number.', 'error');
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('room_id', roomId);
                
                const response = await fetch('/join-room', {
                    method: 'POST',
                    credentials: 'include',  // Include cookies/session for authentication
                    body: formData
                });
                
                if (response.ok) {
                    // Fetch room details and join
                    const roomsResponse = await fetch('/api/rooms', {
                        credentials: 'include'  // Include cookies/session for authentication
                    });
                    const rooms = await roomsResponse.json();
                    const room = rooms.find(r => r.id === roomId);
                    
                    if (room) {
                        joinRoom(room.id, room.name);
                        showNotification(`Joined room: ${room.name} (ID: ${room.id})`, 'success');
                        if (roomIdInput) roomIdInput.value = '';
                        if (joinRoomForm) joinRoomForm.style.display = 'none';
                        // Refresh rooms list
                        refreshRoomsList();
                    } else {
                        showNotification('Room not found. Please check the room ID.', 'error');
                    }
                } else {
                    const responseData = await response.text();
                    showNotification('Failed to join room', 'error');
                }
            } catch (error) {
                console.error('Error joining room:', error);
                showNotification('Failed to join room', 'error');
            }
        });
    }
    
    // Create room form
    const toggleCreateRoom = document.getElementById('toggle-create-room');
    const createRoomForm = document.getElementById('create-room-form');
    const cancelCreateRoom = document.getElementById('cancel-create-room');
    
    if (toggleCreateRoom) {
        toggleCreateRoom.addEventListener('click', () => {
            if (createRoomForm) {
                createRoomForm.style.display = createRoomForm.style.display === 'none' ? 'flex' : 'none';
            }
        });
    }
    
    if (cancelCreateRoom) {
        cancelCreateRoom.addEventListener('click', () => {
            if (createRoomForm) {
                createRoomForm.style.display = 'none';
                const roomNameInput = document.getElementById('room-name-input');
                const roomDescInput = document.getElementById('room-description-input');
                if (roomNameInput) roomNameInput.value = '';
                if (roomDescInput) roomDescInput.value = '';
            }
        });
    }
    
    if (createRoomForm) {
        createRoomForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const roomNameInput = document.getElementById('room-name-input');
            const roomDescInput = document.getElementById('room-description-input');
            
            if (!roomNameInput || !roomNameInput.value.trim() || roomNameInput.value.trim().length < 3) {
                showNotification('Room name must be at least 3 characters', 'error');
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('room_name', roomNameInput.value.trim());
                formData.append('description', roomDescInput ? roomDescInput.value.trim() : '');
                
                const response = await fetch('/create-room', {
                    method: 'POST',
                    credentials: 'include',  // Include cookies/session for authentication
                    body: formData
                });
                
                if (response.ok) {
                    // Reload page to show new room in list
                    window.location.reload();
                } else {
                    showNotification('Failed to create room', 'error');
                }
            } catch (error) {
                console.error('Error creating room:', error);
                showNotification('Failed to create room', 'error');
            }
        });
    }
    
    // Check for room_id in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const roomIdParam = urlParams.get('room_id');
    
    if (roomIdParam) {
        // Try to join room from URL parameter
        const roomId = parseInt(roomIdParam);
        if (!isNaN(roomId)) {
            // Fetch room details
            fetch('/api/rooms', {
                credentials: 'include'  // Include cookies/session for authentication
            })
                .then(response => response.json())
                .then(rooms => {
                    const room = rooms.find(r => r.id === roomId);
                    if (room) {
                        joinRoom(room.id, room.name);
                    } else {
                        showNotification('Room not found. Please join by ID.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error fetching rooms:', error);
                });
        }
    }
    // Don't auto-join any room - user must join by ID
    
    // Load user's joined rooms from server
    refreshRoomsList();
    
    // Periodically update room online users if in a room
    setInterval(() => {
        if (currentRoomId) {
            socket.emit('request_online_users', { room_id: currentRoomId });
        }
    }, 10000);
});

// Clear typing timeout
function clearTypingTimeout() {
    if (typingTimeout) {
        clearTimeout(typingTimeout);
        typingTimeout = null;
    }
}

// Handle page visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && currentRoomId) {
        socket.emit('request_online_users');
        loadMessages(currentRoomId);
    }
});
