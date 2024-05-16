from flask import request, jsonify, session
from app import app, db, login_manager
from flask_login import current_user, login_user, login_required, logout_user
from app.models import *
from app.errors import bad_request, error_response

@app.route('/login', methods=['POST'])
def login():
    if 'username' not in request.form or 'password' not in request.form:
        return bad_request('username or password is missing')
    user = User.query.filter_by(username=request.form['username']).first()
    if user is None or not user.check_password(request.form['password']):
        return bad_request('invalid username or password')
    login_user(user, remember=True)
    session['user_id'] = user.id
    response = jsonify(user.to_dict())
    response.status_code = 200
    # response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return jsonify({'message': 'logout success'})

@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return error_response(400, 'logout required')
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

@login_manager.unauthorized_handler
def unauthorized():
    return error_response(401, 'login required')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# -------- QUIZ ---------


@app.route('/create/quiz', methods=['POST'])
@login_required
def create_quiz():
    data = request.get_json() or {}
    quiz = Quiz(user_id=current_user.id)
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
@login_required
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # Check if the current user is the owner of the quiz
    if quiz.user_id != current_user.id:
        return error_response(403, 'You do not have permission to access this quiz.')
    
    return jsonify(quiz.to_dict())

@app.route('/quiz/<int:quiz_id>', methods=['PUT'])
@login_required
def update_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # Check if the current user is the owner of the quiz
    if quiz.user_id != current_user.id:
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
@login_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # Check if the current user is the owner of the quiz
    if quiz.user_id != current_user.id:
        return error_response(403, 'You do not have permission to access this quiz.')
    
    db.session.delete(quiz)
    db.session.commit()
    
    return jsonify({'message': 'Quiz deleted successfully'})

@app.route('/quiz/all', methods=['GET'])
@login_required
def get_all_quizzes():
    quizzes = Quiz.query.filter_by(user_id=current_user.id).all()
    return jsonify([quiz.to_dict() for quiz in quizzes])