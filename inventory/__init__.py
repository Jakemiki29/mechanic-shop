from flask import Blueprint

inventory_bp = Blueprint('inventory', __name__)

# Import routes after blueprint initialization to avoid circular imports
from . import routes
