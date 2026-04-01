from flask import request, jsonify
from sqlalchemy import func

from auth import token_required
from extensions import cache
from . import mechanic_bp
from .schemas import mechanic_schema, mechanics_schema
from models import Mechanic, db, service_mechanics

# Create a new mechanic
@mechanic_bp.route('/', methods=['POST'])
def create_mechanic():
    """Create a new mechanic.
    ---
    tags:
      - Mechanics
    summary: Add a new mechanic
    description: >
      Creates a mechanic record with name, email, phone, and salary.
      Email addresses must be unique across all mechanics.
    parameters:
      - in: body
        name: body
        required: true
        description: Mechanic data
        schema:
          $ref: '#/definitions/MechanicPayload'
    responses:
      201:
        description: Mechanic created successfully
        schema:
          $ref: '#/definitions/MechanicResponse'
        examples:
          application/json:
            id: 1
            name: "Carlos Rivera"
            email: "carlos@shop.com"
            phone: "555-2020"
            salary: 55000.00
      400:
        description: Missing required fields or email already exists
        examples:
          application/json:
            error: "Email already exists"
    """
    try:
        data = request.get_json() or {}
        required_fields = ['name', 'email', 'phone', 'salary']
        if any(field not in data for field in required_fields):
            return jsonify({'error': 'name, email, phone, and salary are required'}), 400

        if Mechanic.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        new_mechanic = Mechanic(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            salary=data['salary']
        )
        db.session.add(new_mechanic)
        db.session.commit()
        return jsonify(mechanic_schema.dump(new_mechanic)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Get all mechanics
@mechanic_bp.route('/', methods=['GET'])
@cache.cached(timeout=120)
def get_mechanics():
    """List all mechanics.
    ---
    tags:
      - Mechanics
    summary: List all mechanics
    description: Returns an array of every mechanic in the database. Results are cached for 120 seconds.
    responses:
      200:
        description: Array of mechanic records
        schema:
          type: array
          items:
            $ref: '#/definitions/MechanicResponse'
        examples:
          application/json:
            - id: 1
              name: "Carlos Rivera"
              email: "carlos@shop.com"
              phone: "555-2020"
              salary: 55000.00
            - id: 2
              name: "Maria Lopez"
              email: "maria@shop.com"
              phone: "555-3030"
              salary: 60000.00
    """
    mechanics = Mechanic.query.all()
    return jsonify(mechanics_schema.dump(mechanics)), 200

# Update a mechanic
@mechanic_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_mechanic(_customer_id, id):
    """Update a mechanic record.
    ---
    tags:
      - Mechanics
    summary: Update a mechanic
    description: >
      Partially or fully updates the mechanic with the given ID.
      Requires a valid customer JWT token.  All body fields are optional;
      omitted fields retain their current values.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The unique ID of the mechanic to update
      - in: body
        name: body
        required: true
        description: Fields to update (all optional)
        schema:
          $ref: '#/definitions/MechanicUpdatePayload'
    responses:
      200:
        description: Mechanic updated successfully
        schema:
          $ref: '#/definitions/MechanicResponse'
        examples:
          application/json:
            id: 1
            name: "Carlos Updated"
            email: "carlos_new@shop.com"
            phone: "555-9999"
            salary: 60000.00
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
        description: Mechanic not found
        examples:
          application/json:
            error: "Mechanic not found"
    """
    try:
        mechanic = Mechanic.query.get(id)
        if not mechanic:
            return jsonify({'error': 'Mechanic not found'}), 404
        
        data = request.get_json()
        mechanic.name = data.get('name', mechanic.name)
        mechanic.email = data.get('email', mechanic.email)
        mechanic.phone = data.get('phone', mechanic.phone)
        mechanic.salary = data.get('salary', mechanic.salary)
        
        db.session.commit()
        return jsonify(mechanic_schema.dump(mechanic)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Delete a mechanic
@mechanic_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_mechanic(_customer_id, id):
    """Delete a mechanic record.
    ---
    tags:
      - Mechanics
    summary: Delete a mechanic
    description: Permanently removes the mechanic with the given ID. Requires a valid customer JWT token.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The unique ID of the mechanic to delete
    responses:
      200:
        description: Mechanic deleted successfully
        examples:
          application/json:
            message: "Mechanic deleted successfully"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      404:
        description: Mechanic not found
        examples:
          application/json:
            error: "Mechanic not found"
    """
    try:
        mechanic = Mechanic.query.get(id)
        if not mechanic:
            return jsonify({'error': 'Mechanic not found'}), 404
        
        db.session.delete(mechanic)
        db.session.commit()
        return jsonify({'message': 'Mechanic deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mechanic_bp.route('/most-tickets', methods=['GET'])
@cache.cached(timeout=120)
def mechanics_by_ticket_count():
    """List mechanics ranked by number of service tickets worked.
    ---
    tags:
      - Mechanics
    summary: Mechanics ranked by ticket count
    description: >
      Returns all mechanics ordered by the number of service tickets they
      have been assigned to (descending).  Mechanics with no tickets appear
      at the bottom.  Results are cached for 120 seconds.
    responses:
      200:
        description: Mechanics ranked by ticket count
        schema:
          type: array
          items:
            $ref: '#/definitions/MechanicRankResponse'
        examples:
          application/json:
            - id: 2
              name: "Maria Lopez"
              email: "maria@shop.com"
              phone: "555-3030"
              salary: 60000.00
              ticket_count: 8
            - id: 1
              name: "Carlos Rivera"
              email: "carlos@shop.com"
              phone: "555-2020"
              salary: 55000.00
              ticket_count: 5
    """
    ranking = (
        db.session.query(
            Mechanic.id,
            Mechanic.name,
            Mechanic.email,
            Mechanic.phone,
            Mechanic.salary,
            func.count(service_mechanics.c.ticket_id).label('ticket_count'),
        )
        .outerjoin(service_mechanics, Mechanic.id == service_mechanics.c.mechanic_id)
        .group_by(Mechanic.id)
        .order_by(func.count(service_mechanics.c.ticket_id).desc(), Mechanic.id.asc())
        .all()
    )

    return (
        jsonify(
            [
                {
                    'id': mechanic.id,
                    'name': mechanic.name,
                    'email': mechanic.email,
                    'phone': mechanic.phone,
                    'salary': mechanic.salary,
                    'ticket_count': mechanic.ticket_count,
                }
                for mechanic in ranking
            ]
        ),
        200,
    )
