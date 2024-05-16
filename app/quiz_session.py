from flask import render_template, request, jsonify, session
from app import app, db, login_manager
from app.models import *
from app.errors import bad_request, error_response
from flask_login import current_user, login_user, login_required, logout_user
from flask import Flask, request
from flask_socketio import SocketIO

clients = {}

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/game', methods=['POST'])
@socketio.on('connect') 
def handle_connect():
    sid = request.sid
    clients[sid] =  {}
    print(f"Client connected: {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid 
    if sid in clients:
        del clients[sid]
        print(f"Client disconnected: {sid}")
