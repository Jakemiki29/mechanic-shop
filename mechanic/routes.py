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
    """Create a new mechanic"""
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
    """Retrieve all mechanics"""
    mechanics = Mechanic.query.all()
    return jsonify(mechanics_schema.dump(mechanics)), 200

# Update a mechanic
@mechanic_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_mechanic(_customer_id, id):
    """Update a specific mechanic based on the id passed in through the url"""
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
    """Delete a specific mechanic based on the id passed in through the url"""
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
    """Return mechanics ordered by how many tickets they worked on."""
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
