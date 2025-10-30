from flask import request, jsonify
from registro.models.database import db
from registro.models.usuario import Usuario
from registro.models.turno import Turno
from registro.turno.serializer.serializer import turno_schema, turnos_schema
import random

class TurnoView:
    def get_turnos(self):
        try:
            turnos = Turno.query.all()
            return jsonify(turnos_schema.dump(turnos))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_turno(self, turno_id):
        try:
            turno = Turno.query.get_or_404(turno_id)
            return jsonify(turno_schema.dump(turno))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def create_turno(self):
        try:
            data = request.get_json()

            # Verificar si el usuario existe
            usuario = Usuario.query.get(data.get('usuario_id'))
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            # Generar número de turno único
            numero_turno = self._generar_numero_turno()

            nuevo_turno = Turno(
                numero_turno=numero_turno,
                nivel=data.get('nivel'),
                municipio=data.get('municipio'),
                asunto=data.get('asunto'),
                usuario_id=data.get('usuario_id')
            )

            db.session.add(nuevo_turno)
            db.session.commit()

            return jsonify(turno_schema.dump(nuevo_turno)), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def update_turno(self, turno_id):
        try:
            turno = Turno.query.get_or_404(turno_id)
            data = request.get_json()

            turno = turno_schema.load(data, instance=turno, partial=True)
            db.session.commit()

            return jsonify(turno_schema.dump(turno))
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def delete_turno(self, turno_id):
        try:
            turno = Turno.query.get_or_404(turno_id)
            db.session.delete(turno)
            db.session.commit()

            return jsonify({'message': 'Turno eliminado correctamente'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def _generar_numero_turno(self):
        while True:
            numero_turno = f"T-{random.randint(100000, 999999)}"
            turno_existente = Turno.query.filter_by(numero_turno=numero_turno).first()
            if not turno_existente:
                return numero_turno