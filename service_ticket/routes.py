from flask import request, jsonify

from auth import token_required
from . import service_ticket_bp
from .schemas import service_ticket_schema, service_tickets_schema
from models import db, ServiceTicket, Mechanic, Inventory

# Create a new service ticket
@service_ticket_bp.route('/', methods=['POST'])
def create_service_ticket():
    """Create a new service ticket.
    ---
    tags:
      - Service Tickets
    summary: Create a service ticket
    description: >
      Creates a new service ticket linked to an existing customer.
      Optionally, mechanics and parts can be assigned after creation
      via the dedicated assignment endpoints.
    parameters:
      - in: body
        name: body
        required: true
        description: Service ticket data
        schema:
          $ref: '#/definitions/ServiceTicketPayload'
    responses:
      201:
        description: Service ticket created successfully
        schema:
          $ref: '#/definitions/ServiceTicketResponse'
        examples:
          application/json:
            id: 1
            VIN: "1HGCM82633A123456"
            service_date: "2026-03-15"
            service_desc: "Oil change and tire rotation"
            customer_id: 1
            mechanic_ids: []
            part_ids: []
      400:
        description: Missing required fields or validation error
        examples:
          application/json:
            error: "VIN, service_date, service_desc, and customer_id are required"
    """
    try:
        data = request.get_json()
        required_fields = ['VIN', 'service_date', 'service_desc', 'customer_id']
        if any(field not in data for field in required_fields):
            return jsonify({'error': 'VIN, service_date, service_desc, and customer_id are required'}), 400

        new_ticket = ServiceTicket()
        new_ticket.VIN = data['VIN']
        new_ticket.service_date = data['service_date']
        new_ticket.service_desc = data['service_desc']
        new_ticket.customer_id = data['customer_id']
        db.session.add(new_ticket)
        db.session.commit()
        return jsonify(service_ticket_schema.dump(new_ticket)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Get all service tickets
@service_ticket_bp.route('/', methods=['GET'])
def get_service_tickets():
    """List all service tickets.
    ---
    tags:
      - Service Tickets
    summary: List all service tickets
    description: Returns an array of every service ticket in the database, including their assigned mechanic and part IDs.
    responses:
      200:
        description: Array of service ticket records
        schema:
          type: array
          items:
            $ref: '#/definitions/ServiceTicketResponse'
        examples:
          application/json:
            - id: 1
              VIN: "1HGCM82633A123456"
              service_date: "2026-03-15"
              service_desc: "Oil change and tire rotation"
              customer_id: 1
              mechanic_ids: [2]
              part_ids: [5]
            - id: 2
              VIN: "2T1BURHE0JC013381"
              service_date: "2026-03-20"
              service_desc: "Brake pad replacement"
              customer_id: 2
              mechanic_ids: []
              part_ids: []
    """
    tickets = ServiceTicket.query.all()
    return jsonify(service_tickets_schema.dump(tickets)), 200

# Assign a mechanic to a service ticket
@service_ticket_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
@token_required
def assign_mechanic(customer_id, ticket_id, mechanic_id):
    """Assign a mechanic to a service ticket.
    ---
    tags:
      - Service Tickets
    summary: Assign a mechanic to a ticket
    description: >
      Creates a many-to-many association between the specified service ticket
      and mechanic.  The authenticated customer must own the ticket.
      If the mechanic is already assigned the request succeeds without
      duplicating the relationship.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
        description: The unique ID of the service ticket
      - in: path
        name: mechanic_id
        type: integer
        required: true
        description: The unique ID of the mechanic to assign
    responses:
      200:
        description: Mechanic assigned (or already assigned)
        schema:
          $ref: '#/definitions/AssignmentResponse'
        examples:
          application/json:
            message: "Mechanic assigned successfully"
            ticket:
              id: 1
              VIN: "1HGCM82633A123456"
              service_date: "2026-03-15"
              service_desc: "Oil change"
              customer_id: 1
              mechanic_ids: [2]
              part_ids: []
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
      403:
        description: Authenticated customer does not own this ticket
        examples:
          application/json:
            error: "Unauthorized for this ticket"
      404:
        description: Service ticket or mechanic not found
        examples:
          application/json:
            error: "Service ticket not found"
    """
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
    """Remove a mechanic from a service ticket.
    ---
    tags:
      - Service Tickets
    summary: Remove a mechanic from a ticket
    description: >
      Deletes the many-to-many association between the specified service ticket
      and mechanic.  The authenticated customer must own the ticket.
      Returns 400 if the mechanic is not currently assigned.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
        description: The unique ID of the service ticket
      - in: path
        name: mechanic_id
        type: integer
        required: true
        description: The unique ID of the mechanic to remove
    responses:
      200:
        description: Mechanic removed from ticket
        schema:
          $ref: '#/definitions/AssignmentResponse'
        examples:
          application/json:
            message: "Mechanic removed successfully"
            ticket:
              id: 1
              VIN: "1HGCM82633A123456"
              service_date: "2026-03-15"
              service_desc: "Oil change"
              customer_id: 1
              mechanic_ids: []
              part_ids: []
      400:
        description: Mechanic is not assigned to this ticket
        examples:
          application/json:
            error: "Mechanic is not assigned to this ticket"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      403:
        description: Authenticated customer does not own this ticket
        examples:
          application/json:
            error: "Unauthorized for this ticket"
      404:
        description: Service ticket or mechanic not found
        examples:
          application/json:
            error: "Service ticket not found"
    """
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
    """Add an inventory part to a service ticket.
    ---
    tags:
      - Service Tickets
    summary: Add a part to a ticket
    description: >
      Associates an inventory part with the specified service ticket.
      The authenticated customer must own the ticket.
      If the part is already on the ticket the request succeeds without
      duplicating the relationship.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
        description: The unique ID of the service ticket
      - in: path
        name: part_id
        type: integer
        required: true
        description: The unique ID of the inventory part to add
    responses:
      200:
        description: Part added (or already present)
        schema:
          $ref: '#/definitions/AssignmentResponse'
        examples:
          application/json:
            message: "Part added successfully"
            ticket:
              id: 1
              VIN: "1HGCM82633A123456"
              service_date: "2026-03-15"
              service_desc: "Oil change"
              customer_id: 1
              mechanic_ids: [2]
              part_ids: [5]
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      403:
        description: Authenticated customer does not own this ticket
        examples:
          application/json:
            error: "Unauthorized for this ticket"
      404:
        description: Service ticket or inventory part not found
        examples:
          application/json:
            error: "Inventory part not found"
    """
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
    """Bulk-edit mechanics on a service ticket.
    ---
    tags:
      - Service Tickets
    summary: Bulk add/remove mechanics on a ticket
    description: >
      Add and remove multiple mechanics from a service ticket in a single
      request.  Supply a list of mechanic IDs to add and a list to remove.
      The authenticated customer must own the ticket.
      Mechanics not currently on the ticket are silently skipped during
      removal; mechanics already on the ticket are silently skipped during
      addition.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
        description: The unique ID of the service ticket to edit
      - in: body
        name: body
        required: true
        description: Lists of mechanic IDs to add and remove
        schema:
          $ref: '#/definitions/EditTicketPayload'
    responses:
      200:
        description: Ticket mechanics updated successfully
        schema:
          $ref: '#/definitions/ServiceTicketResponse'
        examples:
          application/json:
            id: 1
            VIN: "1HGCM82633A123456"
            service_date: "2026-03-15"
            service_desc: "Oil change"
            customer_id: 1
            mechanic_ids: [3]
            part_ids: [5]
      400:
        description: add_ids or remove_ids are not lists
        examples:
          application/json:
            error: "add_ids and remove_ids must be lists of mechanic IDs"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      403:
        description: Authenticated customer does not own this ticket
        examples:
          application/json:
            error: "Unauthorized for this ticket"
      404:
        description: Service ticket not found
        examples:
          application/json:
            error: "Service ticket not found"
    """
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
