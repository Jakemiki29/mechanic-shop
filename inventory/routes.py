
from flask import jsonify, request

from auth import token_required
from models import Inventory, db

from . import inventory_bp
from .schemas import inventories_schema, inventory_schema


@inventory_bp.route('/', methods=['POST'])
@token_required
def create_inventory_part(_customer_id):
    """Create a new inventory part."""
    try:
        data = request.get_json() or {}
        if 'name' not in data or 'price' not in data:
            return jsonify({'error': 'name and price are required'}), 400

        new_part = Inventory()
        new_part.name = data['name']
        new_part.price = data['price']
        db.session.add(new_part)
        db.session.commit()
        return jsonify(inventory_schema.dump(new_part)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/', methods=['GET'])
def get_inventory_parts():
    """Retrieve all inventory parts."""
    parts = Inventory.query.order_by(Inventory.id.asc()).all()
    return jsonify(inventories_schema.dump(parts)), 200


@inventory_bp.route('/<int:part_id>', methods=['GET'])
def get_inventory_part(part_id):
    """Retrieve a single inventory part by ID."""
    part = Inventory.query.get(part_id)
    if not part:
        return jsonify({'error': 'Inventory part not found'}), 404
    return jsonify(inventory_schema.dump(part)), 200


@inventory_bp.route('/<int:part_id>', methods=['PUT'])
@token_required
def update_inventory_part(_customer_id, part_id):
    """Update an inventory part."""
    try:
        part = Inventory.query.get(part_id)
        if not part:
            return jsonify({'error': 'Inventory part not found'}), 404

        data = request.get_json() or {}
        part.name = data.get('name', part.name)
        part.price = data.get('price', part.price)

        db.session.commit()
        return jsonify(inventory_schema.dump(part)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@inventory_bp.route('/<int:part_id>', methods=['DELETE'])
@token_required
def delete_inventory_part(_customer_id, part_id):
    """Delete an inventory part."""
    try:
        part = Inventory.query.get(part_id)
        if not part:
            return jsonify({'error': 'Inventory part not found'}), 404

        db.session.delete(part)
        db.session.commit()
        return jsonify({'message': 'Inventory part deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
