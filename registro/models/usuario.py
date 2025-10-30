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

    # Nuevos campos para control de administradores
    registrado_por = db.Column(db.Integer, db.ForeignKey('administradores.id'))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con turnos
    turnos = db.relationship('Turno', backref='usuario', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Usuario {self.curp}>'