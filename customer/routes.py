from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from auth import encode_token, token_required
from extensions import cache, limiter
from models import Customer, ServiceTicket, db

from . import customer_bp
from .schemas import customer_schema, customers_schema, login_schema


@customer_bp.route("/", methods=["POST"])
def create_customer():
    """Create a new customer account.
    ---
    tags:
      - Customers
    summary: Register a new customer
    description: >
      Creates a customer account with name, email, phone, and password.
      The password is hashed before storage and is never returned in
      any response.  Email addresses must be unique across all customers.
    parameters:
      - in: body
        name: body
        required: true
        description: Customer registration data
        schema:
          $ref: '#/definitions/CustomerPayload'
    responses:
      201:
        description: Customer account created successfully
        schema:
          $ref: '#/definitions/CustomerResponse'
        examples:
          application/json:
            id: 1
            name: "Jane Doe"
            email: "jane@example.com"
            phone: "555-1234"
      400:
        description: Missing required fields or email already registered
        examples:
          application/json:
            error: "Email already exists"
    """
    try:
        data = request.get_json() or {}
        required_fields = ["name", "email", "phone", "password"]
        if any(field not in data for field in required_fields):
            return jsonify({"error": "name, email, phone, and password are required"}), 400

        if Customer.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400

        new_customer = Customer()
        new_customer.name = data["name"]
        new_customer.email = data["email"]
        new_customer.phone = data["phone"]
        new_customer.password = generate_password_hash(data["password"])
        db.session.add(new_customer)
        db.session.commit()
        return jsonify(customer_schema.dump(new_customer)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@customer_bp.route("/", methods=["GET"])
@cache.cached(timeout=120, query_string=True)
def get_customers():
    """List all customers (paginated).
    ---
    tags:
      - Customers
    summary: List all customers
    description: >
      Returns a paginated list of customer records, ordered by ID ascending.
      Results are cached for 120 seconds.  Use the `page` and `per_page`
      query parameters to control pagination.
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number (1-based)
      - in: query
        name: per_page
        type: integer
        default: 10
        description: Number of results per page (max 100)
    responses:
      200:
        description: Paginated array of customers
        schema:
          type: array
          items:
            $ref: '#/definitions/CustomerResponse'
        examples:
          application/json:
            - id: 1
              name: "Jane Doe"
              email: "jane@example.com"
              phone: "555-1234"
            - id: 2
              name: "Bob Smith"
              email: "bob@example.com"
              phone: "555-5678"
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(max(per_page, 1), 100)

    pagination = Customer.query.order_by(Customer.id.asc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(customers_schema.dump(pagination.items)), 200


@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Retrieve a single customer by ID.
    ---
    tags:
      - Customers
    summary: Get a customer by ID
    description: Returns the customer record whose primary key matches the supplied ID.
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: The unique ID of the customer
    responses:
      200:
        description: Customer record
        schema:
          $ref: '#/definitions/CustomerResponse'
        examples:
          application/json:
            id: 1
            name: "Jane Doe"
            email: "jane@example.com"
            phone: "555-1234"
      404:
        description: Customer not found
        examples:
          application/json:
            error: "Customer not found"
    """
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer_schema.dump(customer)), 200


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
@token_required
def update_customer(auth_customer_id, customer_id):
    """Update a customer account.
    ---
    tags:
      - Customers
    summary: Update a customer account
    description: >
      Updates name, email, phone, and/or password for the specified customer.
      The authenticated token must belong to that same customer — customers
      can only modify their own account.  All body fields are optional;
      omitted fields retain their current values.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: The unique ID of the customer to update
      - in: body
        name: body
        required: true
        description: Fields to update (all optional)
        schema:
          $ref: '#/definitions/CustomerUpdatePayload'
    responses:
      200:
        description: Customer updated successfully
        schema:
          $ref: '#/definitions/CustomerResponse'
        examples:
          application/json:
            id: 1
            name: "Jane Updated"
            email: "jane_new@example.com"
            phone: "555-0000"
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
        description: Token does not belong to this customer
        examples:
          application/json:
            error: "Unauthorized for this customer"
      404:
        description: Customer not found
        examples:
          application/json:
            error: "Customer not found"
    """
    if auth_customer_id != customer_id:
        return jsonify({"error": "Unauthorized for this customer"}), 403

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json() or {}
    customer.name = data.get("name", customer.name)
    customer.email = data.get("email", customer.email)
    customer.phone = data.get("phone", customer.phone)

    if "password" in data and data["password"]:
        customer.password = generate_password_hash(data["password"])

    db.session.commit()
    return jsonify(customer_schema.dump(customer)), 200


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@token_required
def delete_customer(auth_customer_id, customer_id):
    """Delete a customer account.
    ---
    tags:
      - Customers
    summary: Delete a customer account
    description: >
      Permanently removes the customer account with the given ID.
      The authenticated token must belong to that same customer — customers
      can only delete their own account.
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: customer_id
        type: integer
        required: true
        description: The unique ID of the customer to delete
    responses:
      200:
        description: Customer deleted successfully
        examples:
          application/json:
            message: "Customer deleted successfully"
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      403:
        description: Token does not belong to this customer
        examples:
          application/json:
            error: "Unauthorized for this customer"
      404:
        description: Customer not found
        examples:
          application/json:
            error: "Customer not found"
    """
    if auth_customer_id != customer_id:
        return jsonify({"error": "Unauthorized for this customer"}), 403

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200


@customer_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Authenticate a customer and return a JWT token.
    ---
    tags:
      - Customers
    summary: Customer login
    description: >
      Validates the customer's email and password.  On success returns a
      signed JWT Bearer token (valid for 24 hours) and the customer's ID.
      This endpoint is rate-limited to 5 requests per minute per IP.
    parameters:
      - in: body
        name: body
        required: true
        description: Login credentials
        schema:
          $ref: '#/definitions/LoginPayload'
    responses:
      200:
        description: Login successful — returns JWT token
        schema:
          $ref: '#/definitions/TokenResponse'
        examples:
          application/json:
            token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            customer_id: 1
      400:
        description: Validation error — missing or malformed fields
        examples:
          application/json:
            error: "email is required"
      401:
        description: Invalid email or password
        examples:
          application/json:
            error: "Invalid credentials"
    """
    data = request.get_json() or {}
    errors = login_schema.validate(data)
    if errors:
        return jsonify({"error": errors}), 400

    customer = Customer.query.filter_by(email=data["email"]).first()
    if not customer or not check_password_hash(customer.password, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = encode_token(customer.id)
    return jsonify({"token": token, "customer_id": customer.id}), 200


@customer_bp.route("/my-tickets", methods=["GET"])
@token_required
def my_tickets(customer_id):
    """Get service tickets for the authenticated customer.
    ---
    tags:
      - Customers
    summary: My service tickets
    description: >
      Returns all service tickets that belong to the currently authenticated
      customer.  The customer's ID is read from the JWT token — no path
      parameter is needed.
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of service tickets for this customer
        schema:
          type: array
          items:
            $ref: '#/definitions/MyTicketResponse'
        examples:
          application/json:
            - id: 1
              VIN: "1HGCM82633A123456"
              service_date: "2026-03-15"
              service_desc: "Oil change and tire rotation"
              customer_id: 1
              mechanic_ids: [2, 3]
      401:
        description: Missing or invalid Authorization header
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
    """
    tickets = ServiceTicket.query.filter_by(customer_id=customer_id).all()
    return (
        jsonify(
            [
                {
                    "id": ticket.id,
                    "VIN": ticket.VIN,
                    "service_date": ticket.service_date,
                    "service_desc": ticket.service_desc,
                    "customer_id": ticket.customer_id,
                    "mechanic_ids": [mechanic.id for mechanic in ticket.mechanics],
                }
                for ticket in tickets
            ]
        ),
        200,
    )
