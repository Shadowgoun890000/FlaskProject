from .database import db
from datetime import datetime

class CatalogoAsunto(db.Model):
    __tablename__ = 'catalogo_asuntos'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)  # ej: 'certificacion'
    nombre = db.Column(db.String(150), nullable=False)              # ej: 'Certificación'
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "clave": self.clave, "nombre": self.nombre, "activo": self.activo}
