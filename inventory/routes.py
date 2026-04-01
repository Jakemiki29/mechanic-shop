
from flask import jsonify, request

from auth import token_required
from models import Inventory, db

from . import inventory_bp
from .schemas import inventories_schema, inventory_schema


@inventory_bp.route('/', methods=['POST'])
@token_required
def create_inventory_part(_customer_id):
    """Create a new inventory part.
    ---
    tags:
      - Inventory
    summary: Add an inventory part
    description: >
      Creates a new inventory part with a name and price.
      Requires a valid customer JWT token.
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        description: Inventory part data
        schema:
          $ref: '#/definitions/InventoryPayload'
    responses:
      201:
        description: Inventory part created successfully
        schema:
          $ref: '#/definitions/InventoryResponse'
        examples:
          application/json:
            id: 5
            name: "Oil Filter"
            price: 12.99
      400:
        description: Missing required fields or validation error
        examples:
          application/json:
            error: "name and price are required"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
    """
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
    """List all inventory parts.
    ---
    tags:
      - Inventory
    summary: List all inventory parts
    description: Returns an array of every inventory part, ordered by ID ascending.
    responses:
      200:
        description: Array of inventory parts
        schema:
          type: array
          items:
            $ref: '#/definitions/InventoryResponse'
        examples:
          application/json:
            - id: 5
              name: "Oil Filter"
              price: 12.99
            - id: 6
              name: "Brake Pads"
              price: 45.00
    """
    parts = Inventory.query.order_by(Inventory.id.asc()).all()
    return jsonify(inventories_schema.dump(parts)), 200


@inventory_bp.route('/<int:part_id>', methods=['GET'])
def get_inventory_part(part_id):
    """Retrieve a single inventory part by ID.
    ---
    tags:
      - Inventory
    summary: Get an inventory part by ID
    description: Returns the inventory part whose primary key matches the supplied ID.
    parameters:
      - in: path
        name: part_id
        type: integer
        required: true
        description: The unique ID of the inventory part
    responses:
      200:
        description: Inventory part record
        schema:
          $ref: '#/definitions/InventoryResponse'
        examples:
          application/json:
            id: 5
            name: "Oil Filter"
            price: 12.99
      404:
        description: Inventory part not found
        examples:
          application/json:
            error: "Inventory part not found"
    """
    part = Inventory.query.get(part_id)
    if not part:
        return jsonify({'error': 'Inventory part not found'}), 404
    return jsonify(inventory_schema.dump(part)), 200


@inventory_bp.route('/<int:part_id>', methods=['PUT'])
@token_required
def update_inventory_part(_customer_id, part_id):
    """Update an inventory part.
    ---
    tags:
      - Inventory
    summary: Update an inventory part
    description: >
      Partially or fully updates the name and/or price of an inventory part.
      Requires a valid customer JWT token.  All body fields are optional;
      omitted fields retain their current values.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: part_id
        type: integer
        required: true
        description: The unique ID of the part to update
      - in: body
        name: body
        required: true
        description: Fields to update (all optional)
        schema:
          $ref: '#/definitions/InventoryUpdatePayload'
    responses:
      200:
        description: Inventory part updated successfully
        schema:
          $ref: '#/definitions/InventoryResponse'
        examples:
          application/json:
            id: 5
            name: "Premium Oil Filter"
            price: 15.99
      400:
        description: Validation error
        examples:
          application/json:
            error: "Bad request"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      404:
        description: Inventory part not found
        examples:
          application/json:
            error: "Inventory part not found"
    """
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
    """Delete an inventory part.
    ---
    tags:
      - Inventory
    summary: Delete an inventory part
    description: Permanently removes the inventory part with the given ID. Requires a valid customer JWT token.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: part_id
        type: integer
        required: true
        description: The unique ID of the part to delete
    responses:
      200:
        description: Inventory part deleted successfully
        examples:
          application/json:
            message: "Inventory part deleted successfully"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      404:
        description: Inventory part not found
        examples:
          application/json:
            error: "Inventory part not found"
    """
    try:
        part = Inventory.query.get(part_id)
        if not part:
            return jsonify({'error': 'Inventory part not found'}), 404

        db.session.delete(part)
        db.session.commit()
        return jsonify({'message': 'Inventory part deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
