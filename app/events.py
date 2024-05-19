from flask_socketio import join_room, leave_room, send, emit
from app import socketio, db
from app.models import Session, Participant, Response, User
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from datetime import datetime

def jwt_required_socketio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            return f(user_id, *args, **kwargs)
        except Exception as e:
            emit('error', {'message': str(e)})
    return decorated_function

# Dictionary to track responses
response_tracker = {}

@socketio.on('join_session')
@jwt_required_socketio
def handle_join_session(user_id, data):
    print("join_session event received")
    print(f"User ID: {user_id}")
    print(f"Data: {data}")
    
    session_code = data.get('session_code')
    if session_code is None:
        emit('error', {'message': 'session_code is missing'})
        return
    
    session = Session.query.filter_by(code=session_code).first()
    if not session:
        emit('error', {'message': 'Session not found'})
        return
    
    participant = Participant.query.filter_by(session_id=session.id, user_id=user_id).first()
    if not participant:
        emit('error', {'message': 'You must join the session through the main interface before using the socket.'})
        return

    if session.is_started:
        emit('error', {'message': 'Session has already started. You cannot join now.'})
        return

    username = User.query.get(user_id).username
    print(f'{username}: Join room successfully: {session_code}')
    # Join the room
    join_room(session_code)
    send(f'{username} has joined the session.', to=session_code)

    # Emit session update
    participants = Participant.query.filter_by(session_id=session.id).all()
    participant_usernames = [User.query.get(p.user_id).username for p in participants]
    emit('session_update', {
        'host': User.query.get(session.host_id).username,
        'participants': participant_usernames
    }, to=session_code)



@socketio.on('leave_session')
@jwt_required_socketio
def handle_leave_session(user_id, data):
    session_code = data.get('session_code')
    if session_code is None:
        emit('error', {'message': 'session_code is missing'})
        return
    username = User.query.get(user_id).username
    
    session = Session.query.filter_by(code=session_code).first()
    participant = Participant.query.filter_by(session_id=session.id, user_id=user_id).first()
    
    if not session or not participant:
        emit('error', {'message': 'Session or participant not found'})
        return
    
    try:
        # Remove participant from the session
        db.session.delete(participant)
        db.session.commit()
        
        # Leave the room
        leave_room(session_code)
        send(f'{username} has left the session.', to=session_code)
        
        # Emit session update
        participants = Participant.query.filter_by(session_id=session.id).all()
        participant_usernames = [User.query.get(p.user_id).username for p in participants]
        emit('session_update', {
            'host': User.query.get(session.host_id).username,
            'participants': participant_usernames
        }, to=session_code)
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': str(e)})


@socketio.on('start_quiz')
@jwt_required_socketio
def handle_start_quiz(user_id, data):
    session_code = data['session_code']
    session = Session.query.filter_by(code=session_code).first()
    
    if not session:
        emit('error', {'message': 'Session not found'})
        return

    if session.host_id != user_id:
        emit('error', {'message': 'Only the host can start the session.'})
        return

    session.is_started = True
    db.session.commit()
    
    # Initialize the response tracker
    response_tracker[session_code] = {
        'expected_responses': len(session.participants),
        'received_responses': 0,
        'current_question_index': 0
    }
    
    # Announce to all participants that the quiz has started
    send('The quiz has started!', to=session_code)
    
    # Send the first question and its options to all participants
    first_question = session.quiz.questions[0]
    emit('next_question', {
        'question_id': first_question.id,
        'question_text': first_question.text,
        'total': len(session.quiz.questions),
        'options': [{'id': option.id, 'text': option.text, 'is_correct': option.is_correct} for option in first_question.options]
    }, to=session_code)


@socketio.on('submit_answer')
@jwt_required_socketio
def handle_submit_answer(user_id, data):
    session_code = data['session_code']
    question_id = data['question_id']
    option_id = data['option_id']
    
    # Find the session and participant
    session = Session.query.filter_by(code=session_code).first()
    participant = Participant.query.filter_by(session_id=session.id, user_id=user_id).first()
    
    if not session or not participant:
        emit('error', {'message': 'Session or participant not found'})
        return
    
    # Add response to the database
    response = Response(
        session_id=session.id,
        participant_id=participant.id,
        question_id=question_id,
        option_id=option_id,
        response_time=datetime.utcnow()
    )
    db.session.add(response)
    
    try:
        db.session.commit()
        
        # Update response tracker
        response_tracker[session_code]['received_responses'] += 1
        
        # Check if all responses are received
        if response_tracker[session_code]['received_responses'] == response_tracker[session_code]['expected_responses']:
            # Reset received responses count
            response_tracker[session_code]['received_responses'] = 0
            
            # Move to the next question
            response_tracker[session_code]['current_question_index'] += 1
            next_question_index = response_tracker[session_code]['current_question_index']
            
            if next_question_index < len(session.quiz.questions):
                next_question = session.quiz.questions[next_question_index]
                emit('next_question', {
                    'question_id': next_question.id,
                    'question_text': next_question.text,
                    'options': [{'id': option.id, 'text': option.text, 'is_correct': option.is_correct} for option in next_question.options]
                }, to=session_code)
            else:
                send('The quiz has ended!', to=session_code)
                emit('quiz_end', {'message': 'The quiz has ended!'}, to=session_code)
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': str(e)})
