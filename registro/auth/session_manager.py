from flask import session
from functools import wraps
import base64
import io
import qrcode
from PIL import Image


class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def login_admin(self, admin_id, username):
        session['admin_id'] = admin_id
        session['admin_username'] = username
        session['logged_in'] = True

    def logout_admin(self):
        session.clear()

    def is_logged_in(self):
        return session.get('logged_in', False)

    def get_admin_id(self):
        return session.get('admin_id')

    def get_admin_username(self):
        return session.get('admin_username')


# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_manager = SessionManager()
        if not session_manager.is_logged_in():
            return {'error': 'No autorizado'}, 401
        return f(*args, **kwargs)

    return decorated_function


# Generador de QR Code
class QRGenerator:
    @staticmethod
    def generate_qr_base64(data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"