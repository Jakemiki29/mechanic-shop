from flask import Blueprint

mechanic_bp = Blueprint('mechanic', __name__)

# Import routes after blueprint initialization to avoid circular imports
from . import routes
