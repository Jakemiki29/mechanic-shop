import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, jsonify, request
from flask_swagger import swagger as get_swagger_spec
from flask_swagger_ui import get_swaggerui_blueprint

from config import ProductionConfig
from customer import customer_bp
from extensions import cache, limiter
from inventory import inventory_bp
from mechanic import mechanic_bp
from member_schemas import member_schema, members_schema
from models import Member, db, ma
from service_ticket import service_ticket_bp


def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(customer_bp, url_prefix="/customers")
    app.register_blueprint(mechanic_bp, url_prefix="/mechanics")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(service_ticket_bp, url_prefix="/service-tickets")

    # ── Swagger UI ────────────────────────────────────────────────────────────
    SWAGGER_URL = "/docs"
    API_URL = "/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "Mechanic Shop API"},
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # ── Schema definitions (shared across all blueprints) ────────────────────
    _SWAGGER_TEMPLATE = {
        "definitions": {
            # Members
            "MemberPayload": {
                "type": "object",
                "required": ["name", "email", "phone"],
                "properties": {
                    "name": {"type": "string", "example": "Alice Smith"},
                    "email": {"type": "string", "example": "alice@example.com"},
                    "phone": {"type": "string", "example": "555-9876"},
                },
            },
            "MemberResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Alice Smith"},
                    "email": {"type": "string", "example": "alice@example.com"},
                    "phone": {"type": "string", "example": "555-9876"},
                },
            },
            "MemberUpdatePayload": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Alice Updated"},
                    "email": {"type": "string", "example": "alice_new@example.com"},
                    "phone": {"type": "string", "example": "555-0000"},
                },
            },
            # Customers
            "CustomerPayload": {
                "type": "object",
                "required": ["name", "email", "phone", "password"],
                "properties": {
                    "name": {"type": "string", "example": "Jane Doe"},
                    "email": {"type": "string", "example": "jane@example.com"},
                    "phone": {"type": "string", "example": "555-1234"},
                    "password": {"type": "string", "example": "secret123"},
                },
            },
            "CustomerResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Jane Doe"},
                    "email": {"type": "string", "example": "jane@example.com"},
                    "phone": {"type": "string", "example": "555-1234"},
                },
            },
            "CustomerUpdatePayload": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Jane Updated"},
                    "email": {"type": "string", "example": "jane_new@example.com"},
                    "phone": {"type": "string", "example": "555-0000"},
                    "password": {"type": "string", "example": "newpassword123"},
                },
            },
            "LoginPayload": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "example": "jane@example.com"},
                    "password": {"type": "string", "example": "secret123"},
                },
            },
            "TokenResponse": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                    "customer_id": {"type": "integer", "example": 1},
                },
            },
            "MyTicketResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "VIN": {"type": "string", "example": "1HGCM82633A123456"},
                    "service_date": {"type": "string", "example": "2026-03-15"},
                    "service_desc": {"type": "string", "example": "Oil change and tire rotation"},
                    "customer_id": {"type": "integer", "example": 1},
                    "mechanic_ids": {"type": "array", "items": {"type": "integer"}, "example": [2, 3]},
                },
            },
            # Mechanics
            "MechanicPayload": {
                "type": "object",
                "required": ["name", "email", "phone", "salary"],
                "properties": {
                    "name": {"type": "string", "example": "Carlos Rivera"},
                    "email": {"type": "string", "example": "carlos@shop.com"},
                    "phone": {"type": "string", "example": "555-2020"},
                    "salary": {"type": "number", "format": "float", "example": 55000.00},
                },
            },
            "MechanicResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Carlos Rivera"},
                    "email": {"type": "string", "example": "carlos@shop.com"},
                    "phone": {"type": "string", "example": "555-2020"},
                    "salary": {"type": "number", "format": "float", "example": 55000.00},
                },
            },
            "MechanicUpdatePayload": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Carlos Updated"},
                    "email": {"type": "string", "example": "carlos_new@shop.com"},
                    "phone": {"type": "string", "example": "555-9999"},
                    "salary": {"type": "number", "format": "float", "example": 60000.00},
                },
            },
            "MechanicRankResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Carlos Rivera"},
                    "email": {"type": "string", "example": "carlos@shop.com"},
                    "phone": {"type": "string", "example": "555-2020"},
                    "salary": {"type": "number", "format": "float", "example": 55000.00},
                    "ticket_count": {"type": "integer", "example": 5},
                },
            },
            # Service Tickets
            "ServiceTicketPayload": {
                "type": "object",
                "required": ["VIN", "service_date", "service_desc", "customer_id"],
                "properties": {
                    "VIN": {"type": "string", "example": "1HGCM82633A123456"},
                    "service_date": {"type": "string", "example": "2026-03-15"},
                    "service_desc": {"type": "string", "example": "Oil change and tire rotation"},
                    "customer_id": {"type": "integer", "example": 1},
                },
            },
            "ServiceTicketResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "VIN": {"type": "string", "example": "1HGCM82633A123456"},
                    "service_date": {"type": "string", "example": "2026-03-15"},
                    "service_desc": {"type": "string", "example": "Oil change and tire rotation"},
                    "customer_id": {"type": "integer", "example": 1},
                    "mechanic_ids": {"type": "array", "items": {"type": "integer"}, "example": [2, 3]},
                    "part_ids": {"type": "array", "items": {"type": "integer"}, "example": [5, 7]},
                },
            },
            "AssignmentResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Mechanic assigned successfully"},
                    "ticket": {"$ref": "#/definitions/ServiceTicketResponse"},
                },
            },
            "EditTicketPayload": {
                "type": "object",
                "properties": {
                    "add_ids": {
                        "type": "array", "items": {"type": "integer"}, "example": [3, 4],
                        "description": "IDs of mechanics to add to this ticket",
                    },
                    "remove_ids": {
                        "type": "array", "items": {"type": "integer"}, "example": [2],
                        "description": "IDs of mechanics to remove from this ticket",
                    },
                },
            },
            # Inventory
            "InventoryPayload": {
                "type": "object",
                "required": ["name", "price"],
                "properties": {
                    "name": {"type": "string", "example": "Oil Filter"},
                    "price": {"type": "number", "format": "float", "example": 12.99},
                },
            },
            "InventoryResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 5},
                    "name": {"type": "string", "example": "Oil Filter"},
                    "price": {"type": "number", "format": "float", "example": 12.99},
                },
            },
            "InventoryUpdatePayload": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Premium Oil Filter"},
                    "price": {"type": "number", "format": "float", "example": 15.99},
                },
            },
        }
    }

    @app.route("/swagger.json")
    def swagger_spec():
        """Serve the OpenAPI 2.0 (Swagger) specification for this API."""
        swag = get_swagger_spec(app, template=_SWAGGER_TEMPLATE)
        swag["info"]["title"] = "Mechanic Shop API"
        swag["info"]["description"] = (
            "REST API for managing a mechanic shop — customers, mechanics, "
            "service tickets, inventory, and loyalty members."
        )
        swag["info"]["version"] = "1.0.0"
        swag["securityDefinitions"] = {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Bearer token. Example value: Bearer eyJhbGci...",
            }
        }
        swagger_host = os.environ.get("SWAGGER_HOST")
        if swagger_host:
            swag["host"] = swagger_host
            swag["schemes"] = ["https"]
        return jsonify(swag)

    @app.route("/", methods=["GET"])
    def home():
        return (
            jsonify(
                {
                    "message": "Mechanic Shop API is running",
                    "endpoints": [
                        "/customers",
                        "/customers/login",
                        "/customers/my-tickets",
                        "/members",
                        "/mechanics",
                        "/inventory",
                        "/mechanics/most-tickets",
                        "/service-tickets",
                    ],
                }
            ),
            200,
        )

    @app.route("/members", methods=["POST"])
    def create_member():
        """Create a new loyalty member.
        ---
        tags:
          - Members
        summary: Create a new loyalty member
        description: >
          Registers a new loyalty-programme member with a name, email address,
          and phone number.  Members are distinct from customer accounts and do
          not require a password.
        parameters:
          - in: body
            name: body
            required: true
            description: Member data
            schema:
              $ref: '#/definitions/MemberPayload'
        responses:
          201:
            description: Member created successfully
            schema:
              $ref: '#/definitions/MemberResponse'
            examples:
              application/json:
                id: 1
                name: "Alice Smith"
                email: "alice@example.com"
                phone: "555-9876"
          400:
            description: Bad request — missing fields or validation error
            examples:
              application/json:
                error: "Missing required field"
        """
        try:
            data = request.get_json() or {}
            new_member = Member()
            new_member.name = data["name"]
            new_member.email = data["email"]
            new_member.phone = data["phone"]
            db.session.add(new_member)
            db.session.commit()
            return jsonify(member_schema.dump(new_member)), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/members", methods=["GET"])
    def get_members():
        """Retrieve all loyalty members.
        ---
        tags:
          - Members
        summary: List all loyalty members
        description: Returns an array of every loyalty-programme member currently stored in the database.
        responses:
          200:
            description: A list of members
            schema:
              type: array
              items:
                $ref: '#/definitions/MemberResponse'
            examples:
              application/json:
                - id: 1
                  name: "Alice Smith"
                  email: "alice@example.com"
                  phone: "555-9876"
                - id: 2
                  name: "Bob Jones"
                  email: "bob@example.com"
                  phone: "555-4321"
        """
        members = Member.query.all()
        return jsonify(members_schema.dump(members)), 200

    @app.route("/members/<int:member_id>", methods=["GET"])
    def get_member(member_id):
        """Retrieve a single loyalty member by ID.
        ---
        tags:
          - Members
        summary: Get a loyalty member by ID
        description: Returns the loyalty-programme member whose primary key matches the supplied ID.
        parameters:
          - in: path
            name: member_id
            type: integer
            required: true
            description: The unique ID of the member
        responses:
          200:
            description: Member found
            schema:
              $ref: '#/definitions/MemberResponse'
            examples:
              application/json:
                id: 1
                name: "Alice Smith"
                email: "alice@example.com"
                phone: "555-9876"
          404:
            description: Member not found
            examples:
              application/json:
                error: "Member not found"
        """
        member = Member.query.get(member_id)
        if not member:
            return jsonify({"error": "Member not found"}), 404
        return jsonify(member_schema.dump(member)), 200

    @app.route("/members/<int:member_id>", methods=["PUT"])
    def update_member(member_id):
        """Update a loyalty member.
        ---
        tags:
          - Members
        summary: Update a loyalty member
        description: Partially or fully updates a loyalty-programme member's name, email, or phone. All fields are optional; omitted fields retain their current values.
        parameters:
          - in: path
            name: member_id
            type: integer
            required: true
            description: The unique ID of the member to update
          - in: body
            name: body
            required: true
            description: Fields to update (all optional)
            schema:
              $ref: '#/definitions/MemberUpdatePayload'
        responses:
          200:
            description: Member updated successfully
            schema:
              $ref: '#/definitions/MemberResponse'
            examples:
              application/json:
                id: 1
                name: "Alice Updated"
                email: "alice_new@example.com"
                phone: "555-0000"
          400:
            description: Validation error
            examples:
              application/json:
                error: "Bad request"
          404:
            description: Member not found
            examples:
              application/json:
                error: "Member not found"
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return jsonify({"error": "Member not found"}), 404

            data = request.get_json() or {}
            member.name = data.get("name", member.name)
            member.email = data.get("email", member.email)
            member.phone = data.get("phone", member.phone)

            db.session.commit()
            return jsonify(member_schema.dump(member)), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/members/<int:member_id>", methods=["DELETE"])
    def delete_member(member_id):
        """Delete a loyalty member.
        ---
        tags:
          - Members
        summary: Delete a loyalty member
        description: Permanently removes the loyalty-programme member with the given ID from the database.
        parameters:
          - in: path
            name: member_id
            type: integer
            required: true
            description: The unique ID of the member to delete
        responses:
          200:
            description: Member deleted successfully
            examples:
              application/json:
                message: "Member deleted successfully"
          404:
            description: Member not found
            examples:
              application/json:
                error: "Member not found"
        """
        try:
            member = Member.query.get(member_id)
            if not member:
                return jsonify({"error": "Member not found"}), 404

            db.session.delete(member)
            db.session.commit()
            return jsonify({"message": "Member deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return app


app = create_app(ProductionConfig)
