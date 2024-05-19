from app import app, db
from app.models import *

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Quiz': Quiz,
        'Question': Question,
        'Option': Option,
        'Session': Session,
        'Participant': Participant,
        'Response': Response,
        'Score': Score
    }