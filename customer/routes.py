from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from auth import encode_token, token_required
from extensions import cache, limiter
from models import Customer, ServiceTicket, db

from . import customer_bp
from .schemas import customer_schema, customers_schema, login_schema


@customer_bp.route("/", methods=["POST"])
def create_customer():
    """Create a new customer account."""
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
    """Retrieve paginated customer records."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(max(per_page, 1), 100)

    pagination = Customer.query.order_by(Customer.id.asc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(customers_schema.dump(pagination.items)), 200


@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Retrieve a single customer by ID."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer_schema.dump(customer)), 200


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
@token_required
def update_customer(auth_customer_id, customer_id):
    """Update a customer account for the authenticated owner."""
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
    """Delete a customer account for the authenticated owner."""
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
    """Authenticate a customer and return a JWT token."""
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
    """Return service tickets for the authenticated customer."""
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
