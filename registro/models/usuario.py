from .database import db
from datetime import datetime


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    curp = db.Column(db.String(18), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    paterno = db.Column(db.String(50), nullable=False)
    materno = db.Column(db.String(50))
    telefono = db.Column(db.String(15))
    celular = db.Column(db.String(15), nullable=False)
    correo = db.Column(db.String(100), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # NUEVO: credenciales de usuario público
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(255))

    # Nuevos campos para control de administradores
    registrado_por = db.Column(db.Integer, db.ForeignKey('administradores.id'))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con turnos
    turnos = db.relationship('Turno', backref='usuario', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        if password and len(password) >= 6:
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Usuario {self.curp}>'