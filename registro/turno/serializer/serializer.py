from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from registro.models.database import db
from registro.models.turno import Turno

class TurnoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Turno
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    # No necesitamos definir campos manualmente, SQLAlchemyAutoSchema los detecta automáticamente

# Crear instancias del schema
turno_schema = TurnoSchema()
turnos_schema = TurnoSchema(many=True)
