from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # avatar_url = db.Column(db.String(256), nullable=True)
    # bio = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        # self.password_hash = generate_password_hash(password)
        self.password_hash = password

    def check_password(self, password):
        # return check_password_hash(self.password_hash, password)
        return self.password_hash == password
    
    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
        return data
    
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    # category = db.relationship('Category', back_populates='quizzes')

    # db.relationship(): establish a relationship between the Quiz and Question models
    # back_populates='quiz': used to set up a bidirectional relationship: The Question class should 
    #   have a corresponding relationship attr called quiz that references the Quiz object to which each 
    #   Question belongs. The back_populates parameter must be mirrored in the Question class w/ corresponding attr.
    # The cascade option ensures that when a Quiz is deleted, all associated Question objects are also deleted, 
    # and when a Question is deleted, all associated Option objects are also deleted. If an Option or Question 
    # becomes orphaned (i.e., it is no longer associated with a parent Quiz or Question), it is automatically deleted 
    # from the database
    questions = db.relationship('Question', back_populates='quiz', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at,
            'questions': [question.to_dict() for question in self.questions]
        }
    
    def from_dict(self, data, new_quiz=False):
        if new_quiz:
            # "title" and "questions" are required
            # When creating a new quiz, it must have a title and at least 1 question
            if "title" not in data or "questions" not in data:
                raise ValueError('Title and questions are required')
            if data["title"] == "":
                raise ValueError('Title is required')
            if data["questions"] == []:
                raise ValueError('At least 1 question is required')
            setattr(self, "title", data["title"])
            for question_data in data['questions']:
                new_question = Question().from_dict(question_data, self, new_question=True)
                self.questions.append(new_question)
            # self.questions = [Question().from_dict(question_data, self, new_question=True) for question_data in data['questions']]
        else:
            if "title" in data:
                setattr(self, "title", data["title"])
            if "questions" in data:
                existing_question_ids = {question.id: question for question in self.questions}
                for question_data in data['questions']:
                    question_id = question_data.get('id')
                    # updating a quiz requires that request provides question id and option id
                    if question_id is None:
                        # raise ValueError('Question id is missing in the provided data.')
                        self.questions.append(Question().from_dict(question_data, self, new_question=True))
                    # question id must be valid (exist)
                    else:
                        if question_id not in existing_question_ids:
                            print("raise exception")
                            raise ValueError('Question id is invalid.')
                        existing_question_ids[question_id].from_dict(question_data, self)
        return self

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    # type = db.Column(db.String(32), nullable=False, default='multiple_choice')
    quiz = db.relationship('Quiz', back_populates='questions')
    options = db.relationship('Option', back_populates='question', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'text': self.text,
            'options': [option.to_dict() for option in self.options]
        }
    
    def from_dict(self, data, quiz=None, new_question=False):
        if new_question:
            if "text" not in data:
                raise ValueError('Question text is required')
            if "options" not in data:
                raise ValueError('Question options are required')
            if data["options"] == []:
                raise ValueError('At least 1 option is required')
            setattr(self, "text", data["text"])
            if quiz:
                self.quiz = quiz
            for option_data in data['options']:
                new_option = Option().from_dict(option_data, self, new_option=True)
                self.options.append(new_option)
            # self.options = [Option().from_dict(option_data, self, new_option=True) for option_data in data['options']]
        else:
            if "text" in data:
                setattr(self, "text", data["text"])
            if 'options' in data:
                existing_option_ids = {option.id: option for option in self.options}
                for option_data in data['options']:
                    option_id = option_data.get('id')
                    # when updating, option id must be provided
                    if option_id is None:
                        # raise ValueError('Option id is missing in the provided data.')
                        self.options.append(Option().from_dict(option_data, self, new_option=True))
                    # option id must be valid (exist)
                    else:
                        if option_id not in existing_option_ids:
                            raise ValueError('Option id is invalid.')
                        existing_option_ids[option_id].from_dict(option_data, self)
        return self

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question = db.relationship('Question', back_populates='options')

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'text': self.text,
            'is_correct': self.is_correct
        }
    
    def from_dict(self, data, question=None, new_option=False):
        if new_option:
            if "text" not in data:
                raise ValueError('Option text is required')
            if "is_correct" not in data:
                raise ValueError('Option correctness is required')
            setattr(self, "text", data["text"])
            setattr(self, "is_correct", data["is_correct"])
            if question:
                self.question = question
        else:
            for field in ['text', 'is_correct']:
                if field in data:
                    setattr(self, field, data[field])
        return self

# class Session(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
#     host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     end_time = db.Column(db.DateTime)
#     quiz = db.relationship('Quiz')
#     host = db.relationship('User')
#     participants = db.relationship('Participant', back_populates='session', cascade='all, delete-orphan')

# class Participant(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     join_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     session = db.relationship('Session', back_populates='participants')
#     user = db.relationship('User')

# class Score(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
#     participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
#     score = db.Column(db.Integer, nullable=False)
#     session = db.relationship('Session')
#     participant = db.relationship('Participant')

# class Category(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True, nullable=False)
#     quizzes = db.relationship('Quiz', back_populates='category')

# class Leaderboard(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
#     total_score = db.Column(db.Integer, nullable=False, default=0)
#     user = db.relationship('User')
#     quiz = db.relationship('Quiz')

# class Response(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
#     participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
#     question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
#     option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=True)
#     response_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     session = db.relationship('Session')
#     participant = db.relationship('Participant')
#     question = db.relationship('Question')
#     option = db.relationship('Option')

# @login_manager.user_loader
# def load_user(id):
#     return User.query.get(int(id))