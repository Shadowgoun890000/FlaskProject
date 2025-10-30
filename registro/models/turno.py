from .database import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class Turno(db.Model):
    __tablename__ = 'turnos'

    id = db.Column(db.Integer, primary_key=True)
    numero_turno = db.Column(db.String(20), unique=True, nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    municipio = db.Column(db.String(100), nullable=False)
    asunto = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, atendido, cancelado, resuelto

    # Claves foráneas
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    atendido_por = db.Column(db.Integer, db.ForeignKey('administradores.id'))
    fecha_atencion = db.Column(db.DateTime)

    # Restricción única para evitar duplicados
    __table_args__ = (
        UniqueConstraint('usuario_id', 'municipio', 'asunto', 'estado',
                        name='uq_usuario_municipio_asunto_estado'),
    )

    def __repr__(self):
        return f'<Turno {self.numero_turno}>'