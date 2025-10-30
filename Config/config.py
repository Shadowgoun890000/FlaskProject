import os


class Config:
    """Configuración simplificada para fines académicos"""

    # Configuración MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'turnos_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

    # URI de conexión MySQL
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Deshabilitar características que requieren SECRET_KEY
    WTF_CSRF_ENABLED = False


# Crear instancia de configuración
config = Config()