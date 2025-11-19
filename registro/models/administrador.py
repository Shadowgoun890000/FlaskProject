from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

class Administrador(db.Model):
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='operador')  # operador, admin, supervisor
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)

    def set_password(self, password):
        if len(password) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_username(username):
        """Validar formato de username"""
        if len(username) < 3:
            return False, 'El usuario debe tener al menos 3 caracteres'
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, 'El usuario solo puede contener letras, números y guiones bajos'
        return True, ''

    @staticmethod
    def validate_email(email):
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, 'Formato de email inválido'
        return True, ''

    def __repr__(self):
        return f'<Administrador {self.username}>'