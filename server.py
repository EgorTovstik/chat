from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import hashlib
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

USERS_FILE = "users.json"
chat_history = {}
chat_participants = {}

# --- Пользователи ---
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "message": "Имя пользователя и пароль обязательны"}), 400
    if username in users:
        return jsonify({"success": False, "message": "Пользователь уже существует"}), 400

    users[username] = {"password": hash_password(password)}
    save_users(users)
    return jsonify({"success": True})

@app.route('/my_chats/<username>', methods=['GET'])
def my_chats(username):
    user_chats = []
    for room, participants in chat_participants.items():
        if username in participants:
            last_msg = chat_history.get(room, [])
            last_msg_text = last_msg[-1]['text'] if last_msg else ''
            user_chats.append({
                "room": room,
                "participants": participants,
                "last_message": last_msg_text
            })
    return jsonify({"success": True, "chats": user_chats})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "message": "Имя пользователя и пароль обязательны"}), 400
    if username not in users or users[username]["password"] != hash_password(password):
        return jsonify({"success": False, "message": "Неверное имя пользователя или пароль"}), 401
    return jsonify({"success": True})

# --- Socket.IO ---
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('chat history', chat_history.get(room, []), room=request.sid)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)

@socketio.on('send message')
def handle_message(data):
    room = data['room']
    author = data['author']
    text = data['text']
    time = data['time']

    message = {"author": author, "text": text, "time": time}
    chat_history.setdefault(room, []).append(message)
    emit('receive message', message, room=room)

@socketio.on('create chat')
def create_chat(data):
    room = data['room']
    participants = data['participants']  # список участников

    if room not in chat_history:
        chat_history[room] = []
    if room not in chat_participants:
        chat_participants[room] = participants

    emit('chat created', {"room": room, "participants": participants}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
