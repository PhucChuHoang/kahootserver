# shell.py
import eventlet
eventlet.monkey_patch()

from app import app, db
from app.models import User, Quiz, Question, Option, Session, Participant, Response, Score
import code

# Push an application context so that Flask can be used interactively
with app.app_context():
    # Expose Flask app, SQLAlchemy db instance, and models to the shell
    globals().update(locals())
    
    # Start an interactive shell
    banner = "Interactive Flask Shell with App Context\nVariables: app, db, User, Quiz, Question, Option, Session, Participant, Response, Score"
    code.interact(banner=banner, local=globals())
