from flask import request, jsonify
from app import app, db
from app.models import *
from app.errors import bad_request, error_response
from app.utils import generate_unique_code
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from app import blacklist
from flask_jwt_extended.exceptions import NoAuthorizationError

@app.route('/uid', methods=['GET'])
@jwt_required()
def get_uid():
    user_id = get_jwt_identity()
    return jsonify({'uid': user_id})

@app.route('/login', methods=['POST'])
def login():
    if 'username' not in request.form or 'password' not in request.form:
        return bad_request('username or password is missing')
    user = User.query.filter_by(username=request.form['username']).first()
    if user is None or not user.check_password(request.form['password']):
        return bad_request('invalid username or password')
    access_token = create_access_token(identity=user.id)
    response = jsonify(access_token=access_token)
    response.status_code = 200
    return response

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    blacklist.add(jti)
    return jsonify({'message': 'logout success'})

@app.route('/register', methods=['POST'])
def register():
    try:
        # Check if there is an active JWT token
        verify_jwt_in_request()
        return error_response(400, 'logout required')
    except NoAuthorizationError:
        # If no active token, continue with registration
        if 'username' not in request.form or 'email' not in request.form or 'password' not in request.form:
            return bad_request('username, email, or password is missing')
        if User.query.filter_by(username=request.form['username']).first():
            return bad_request('username exists')
        if User.query.filter_by(email=request.form['email']).first():
            return bad_request('email exists')
        user = User()
        user.from_dict(request.form, new_user=True)
        db.session.add(user)
        db.session.commit()
        response = jsonify(user.to_dict())
        response.status_code = 201
        return response


# -------- QUIZ ---------


@app.route('/create/quiz', methods=['POST'])
@jwt_required()
def create_quiz():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    quiz = Quiz(user_id=user_id)
    try:
        quiz.from_dict(data, new_quiz=True)
        db.session.add(quiz)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()  # Rollback any changes if an exception occurs
        return bad_request(str(e))
    except Exception as e:
        db.session.rollback()  # Rollback any changes for any other exceptions
        return error_response(500, str(e))
    
    response = jsonify(quiz.to_dict())
    response.status_code = 201
    return response

@app.route('/quiz/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = get_jwt_identity()
    # Check if the current user is the owner of the quiz
    if quiz.user_id != user_id:
        return error_response(403, 'You do not have permission to access this quiz.')
    
    return jsonify(quiz.to_dict())

@app.route('/quiz/<int:quiz_id>', methods=['PUT'])
@jwt_required()
def update_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = get_jwt_identity()
    # Check if the current user is the owner of the quiz
    if quiz.user_id != user_id:
        return error_response(403, 'You do not have permission to access this quiz.')
    
    data = request.get_json() or {}
    if not data:
        return bad_request('No data provided')
    try:
        quiz.from_dict(data)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()  # Rollback any changes if an exception occurs
        return bad_request(str(e))
    except Exception as e:
        db.session.rollback()  # Rollback any changes for any other exceptions
        return error_response(500, str(e))
    
    return jsonify(quiz.to_dict())

@app.route('/quiz/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = get_jwt_identity()
    # Check if the current user is the owner of the quiz
    if quiz.user_id != user_id:
        return error_response(403, 'You do not have permission to access this quiz.')
    
    db.session.delete(quiz)
    db.session.commit()
    
    return jsonify({'message': 'Quiz deleted successfully'})

@app.route('/quiz/all', methods=['GET'])
@jwt_required()
def get_all_quizzes():
    user_id = get_jwt_identity()
    quizzes = Quiz.query.filter_by(user_id=user_id).all()
    return jsonify([quiz.to_dict() for quiz in quizzes])


# -------- SESSION ---------


@app.route('/create/session', methods=['POST'])
@jwt_required()
def create_session():
    data = request.get_json() or {}
    quiz_id = data.get('quiz_id')
    if quiz_id is None:
        return bad_request('quiz_id is missing')
    user_id = get_jwt_identity()
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != user_id:
        return error_response(403, 'You do not have permission to create a session for this quiz.')
    
    session_code = generate_unique_code()  # Implement this function to generate a unique code
    session = Session(quiz_id=quiz.id, host_id=user_id, code=session_code)
    db.session.add(session)
    db.session.commit()
    
    response = jsonify({'session_code': session_code})
    response.status_code = 201
    return response

@app.route('/join/session', methods=['POST'])
@jwt_required()
def join_session():
    data = request.get_json() or {}
    session_code = data.get('session_code')
    if session_code is None:
        return bad_request('session_code is missing')

    session = Session.query.filter_by(code=session_code).first_or_404()

    # Check if the session has already started
    if session.is_started:
        return error_response(400, 'Session has already started. You cannot join now.')
    
    user_id = get_jwt_identity()

    # Add participant to session
    participant = Participant(session_id=session.id, user_id=user_id)
    db.session.add(participant)
    db.session.commit()

    return jsonify({'message': 'Joined session successfully'})