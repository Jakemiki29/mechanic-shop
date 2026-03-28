import os

from flask import Flask, jsonify, request

from customer import customer_bp
from extensions import cache, limiter
from inventory import inventory_bp
from mechanic import mechanic_bp
from member_schemas import member_schema, members_schema
from models import Member, db, ma
from service_ticket import service_ticket_bp

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 120

db.init_app(app)
ma.init_app(app)
cache.init_app(app)
limiter.init_app(app)

app.register_blueprint(customer_bp, url_prefix="/customers")
app.register_blueprint(mechanic_bp, url_prefix="/mechanics")
app.register_blueprint(inventory_bp, url_prefix="/inventory")
app.register_blueprint(service_ticket_bp, url_prefix="/service-tickets")


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
    """Create a new member."""
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
    """Retrieve all members."""
    members = Member.query.all()
    return jsonify(members_schema.dump(members)), 200


@app.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    """Retrieve a single member by ID."""
    member = Member.query.get(member_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    return jsonify(member_schema.dump(member)), 200


@app.route("/members/<int:member_id>", methods=["PUT"])
def update_member(member_id):
    """Update a member."""
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
    """Delete a member."""
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({"error": "Member not found"}), 404

        db.session.delete(member)
        db.session.commit()
        return jsonify({"message": "Member deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)
