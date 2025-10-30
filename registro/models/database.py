from flask_sqlalchemy import SQLAlchemy

# Inicializar SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    db.init_app(app)

    with app.app_context():
        # Importar modelos aquí para evitar circular imports
        from .usuario import Usuario
        from .turno import Turno

        # Crear todas las tablas
        db.create_all()

        print("✅ Base de datos inicializada correctamente")
        print("✅ Tablas creadas: usuarios, turnos")
