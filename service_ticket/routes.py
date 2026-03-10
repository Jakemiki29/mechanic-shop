from flask import request, jsonify
from . import service_ticket_bp
from .schemas import service_ticket_schema, service_tickets_schema
from models import db, ServiceTicket, Mechanic

# Create a new service ticket
@service_ticket_bp.route('/', methods=['POST'])
def create_service_ticket():
    """Create a new service ticket"""
    try:
        data = request.get_json()
        new_ticket = ServiceTicket(
            VIN=data['VIN'],
            service_date=data['service_date'],
            service_desc=data['service_desc'],
            customer_id=data['customer_id']
        )
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify(service_ticket_schema.dump(new_ticket)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Get all service tickets
@service_ticket_bp.route('/', methods=['GET'])
def get_service_tickets():
    """Retrieve all service tickets"""
    tickets = ServiceTicket.query.all()
    return jsonify(service_tickets_schema.dump(tickets)), 200

# Assign a mechanic to a service ticket
@service_ticket_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
def assign_mechanic(ticket_id, mechanic_id):
    """Adds a relationship between a service ticket and a mechanic"""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        
        mechanic = Mechanic.query.get(mechanic_id)
        if not mechanic:
            return jsonify({'error': 'Mechanic not found'}), 404
        
        # Check if mechanic is already assigned
        if mechanic in ticket.mechanics:
            return jsonify({'message': 'Mechanic already assigned to this ticket'}), 200
        
        # Add mechanic to the service ticket using the relationship attribute
        ticket.mechanics.append(mechanic)
        db.session.commit()
        
        return jsonify({
            'message': 'Mechanic assigned successfully',
            'ticket': service_ticket_schema.dump(ticket)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Remove a mechanic from a service ticket
@service_ticket_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['PUT'])
def remove_mechanic(ticket_id, mechanic_id):
    """Removes the relationship between a service ticket and a mechanic"""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        
        mechanic = Mechanic.query.get(mechanic_id)
        if not mechanic:
            return jsonify({'error': 'Mechanic not found'}), 404
        
        # Check if mechanic is assigned to this ticket
        if mechanic not in ticket.mechanics:
            return jsonify({'error': 'Mechanic is not assigned to this ticket'}), 400
        
        # Remove mechanic from the service ticket using the relationship attribute
        ticket.mechanics.remove(mechanic)
        db.session.commit()
        
        return jsonify({
            'message': 'Mechanic removed successfully',
            'ticket': service_ticket_schema.dump(ticket)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
