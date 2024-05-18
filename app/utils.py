import secrets
import string
from app.models import Session

def generate_unique_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(length))
        if not Session.query.filter_by(code=code).first():
            break
    return code
