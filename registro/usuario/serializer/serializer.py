from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from registro.models.database import db
from registro.models.usuario import Usuario

class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    # No necesitamos definir campos manualmente, SQLAlchemyAutoSchema los detecta automáticamente

# Crear instancias del schema
usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)
