from flask import Blueprint

service_ticket_bp = Blueprint('service_ticket', __name__)

# Import routes after blueprint initialization to avoid circular imports
from . import routes
