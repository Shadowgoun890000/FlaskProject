from flask import request, jsonify
from registro.models.database import db
from registro.models.usuario import Usuario
from registro.usuario.serializer.serializer import usuario_schema, usuarios_schema

class UsuarioView:
    def get_usuarios(self):
        try:
            usuarios = Usuario.query.all()
            return jsonify(usuarios_schema.dump(usuarios))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_usuario(self, usuario_id):
        try:
            usuario = Usuario.query.get_or_404(usuario_id)
            return jsonify(usuario_schema.dump(usuario))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def create_usuario(self):
        try:
            data = request.get_json()

            # Verificar si el usuario ya existe por CURP
            usuario_existente = Usuario.query.filter_by(curp=data.get('curp')).first()
            if usuario_existente:
                return jsonify({'error': 'Ya existe un usuario con esta CURP'}), 400

            nuevo_usuario = usuario_schema.load(data)
            db.session.add(nuevo_usuario)
            db.session.commit()

            return jsonify(usuario_schema.dump(nuevo_usuario)), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def update_usuario(self, usuario_id):
        try:
            usuario = Usuario.query.get_or_404(usuario_id)
            data = request.get_json()

            usuario = usuario_schema.load(data, instance=usuario, partial=True)
            db.session.commit()

            return jsonify(usuario_schema.dump(usuario))
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def delete_usuario(self, usuario_id):
        try:
            usuario = Usuario.query.get_or_404(usuario_id)
            db.session.delete(usuario)
            db.session.commit()

            return jsonify({'message': 'Usuario eliminado correctamente'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500