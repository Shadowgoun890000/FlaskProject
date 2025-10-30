from .database import db
from datetime import datetime

class SecuenciaTurno(db.Model):
    __tablename__ = 'secuencias_turno'

    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False, unique=True)
    siguiente_numero = db.Column(db.Integer, default=1)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SecuenciaTurno {self.municipio}: {self.siguiente_numero}>'