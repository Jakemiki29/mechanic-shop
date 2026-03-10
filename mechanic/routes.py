from flask import request, jsonify
from . import mechanic_bp
from .schemas import mechanic_schema, mechanics_schema
from models import db, Mechanic

# Create a new mechanic
@mechanic_bp.route('/', methods=['POST'])
def create_mechanic():
    """Create a new mechanic"""
    try:
        data = request.get_json()
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
def get_mechanics():
    """Retrieve all mechanics"""
    mechanics = Mechanic.query.all()
    return jsonify(mechanics_schema.dump(mechanics)), 200

# Update a mechanic
@mechanic_bp.route('/<int:id>', methods=['PUT'])
def update_mechanic(id):
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
def delete_mechanic(id):
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
