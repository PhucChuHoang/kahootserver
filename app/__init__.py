from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
socketio = SocketIO(app)

blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in blacklist

from app import routes, models, events