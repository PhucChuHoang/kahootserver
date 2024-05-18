# events.py
from flask_socketio import join_room, leave_room, send, emit
from app import socketio

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(f'{username} has entered the room.', to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f'{username} has left the room.', to=room)

@socketio.on('join_room')
def handle_join_room(data):
    session_code = data['session_code']
    username = data['username']
    join_room(session_code)
    send(f'{username} has joined the room.', to=session_code)