from .registration_manager import RegistrationManager
from .session_manager import SessionManager, login_required, QRGenerator

# Crear instancias globales
registration_manager = RegistrationManager()