import os
import datetime
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'this-is-secret-key'
    SECRET_KEY = "aslkdjflasjdlkfjlakjwern128499s"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'your_jwt_secret_key'
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=30)