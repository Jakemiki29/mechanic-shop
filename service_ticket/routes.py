from flask import request, jsonify

from auth import token_required
from . import service_ticket_bp
from .schemas import service_ticket_schema, service_tickets_schema
from models import db, ServiceTicket, Mechanic, Inventory

# Create a new service ticket
@service_ticket_bp.route('/', methods=['POST'])
@token_required
def create_service_ticket(customer_id):
    """Create a new service ticket"""
    try:
        data = request.get_json()

        requested_customer_id = data.get('customer_id')
        if requested_customer_id != customer_id:
            return jsonify({'error': 'You can only create tickets for your own account'}), 403

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
@token_required
def assign_mechanic(customer_id, ticket_id, mechanic_id):
    """Adds a relationship between a service ticket and a mechanic"""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        if ticket.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized for this ticket'}), 403
        
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
@token_required
def remove_mechanic(customer_id, ticket_id, mechanic_id):
    """Removes the relationship between a service ticket and a mechanic"""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        if ticket.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized for this ticket'}), 403
        
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


@service_ticket_bp.route('/<int:ticket_id>/add-part/<int:part_id>', methods=['PUT'])
@token_required
def add_part_to_ticket(customer_id, ticket_id, part_id):
    """Adds a single inventory part to a service ticket."""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        if ticket.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized for this ticket'}), 403

        part = Inventory.query.get(part_id)
        if not part:
            return jsonify({'error': 'Inventory part not found'}), 404

        if part in ticket.parts:
            return jsonify({'message': 'Part already added to this ticket'}), 200

        ticket.parts.append(part)
        db.session.commit()

        return jsonify({
            'message': 'Part added successfully',
            'ticket': service_ticket_schema.dump(ticket)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@service_ticket_bp.route('/<int:ticket_id>/edit', methods=['PUT'])
@token_required
def edit_ticket_mechanics(customer_id, ticket_id):
    """Add and remove mechanics from a ticket in one request."""
    try:
        ticket = ServiceTicket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Service ticket not found'}), 404
        if ticket.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized for this ticket'}), 403

        data = request.get_json() or {}
        add_ids = data.get('add_ids', [])
        remove_ids = data.get('remove_ids', [])

        if not isinstance(add_ids, list) or not isinstance(remove_ids, list):
            return jsonify({'error': 'add_ids and remove_ids must be lists of mechanic IDs'}), 400

        if remove_ids:
            mechanics_to_remove = Mechanic.query.filter(Mechanic.id.in_(remove_ids)).all()
            for mechanic in mechanics_to_remove:
                if mechanic in ticket.mechanics:
                    ticket.mechanics.remove(mechanic)

        if add_ids:
            mechanics_to_add = Mechanic.query.filter(Mechanic.id.in_(add_ids)).all()
            for mechanic in mechanics_to_add:
                if mechanic not in ticket.mechanics:
                    ticket.mechanics.append(mechanic)

        db.session.commit()
        return jsonify(service_ticket_schema.dump(ticket)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
