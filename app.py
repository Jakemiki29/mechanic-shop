from flask import Flask, request, jsonify
from models import db, ma, Customer, ServiceTicket, Mechanic, Member

# Initialize Flask app
app = Flask(__name__)

# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
ma.init_app(app)

# ==================== Marshmallow Schemas ====================
# Schemas are used for serializing, deserializing, and validating data

# Customer Schema
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer  # Using the SQLAlchemy model to create fields used in serialization, deserialization, and validation
    
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)  # Variant that allows for the serialization of many customers

# Member Schema
class MemberSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Member  # Using the SQLAlchemy model to create fields used in serialization, deserialization, and validation
    
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)  # Variant that allows for the serialization of many Users

# ==================== REGISTER BLUEPRINTS ====================
# Import and register blueprints
from mechanic import mechanic_bp
from service_ticket import service_ticket_bp

app.register_blueprint(mechanic_bp, url_prefix='/mechanics')
app.register_blueprint(service_ticket_bp, url_prefix='/service-tickets')

# ==================== CRUD Routes ====================

# Basic home route so the API has a landing page at '/'
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Mechanic Shop API is running',
        'endpoints': [
            '/customers',
            '/members',
            '/mechanics',
            '/service-tickets'
        ]
    }), 200

# ==================== CUSTOMER ROUTES ====================

# Create a new customer
@app.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.get_json()
        new_customer = Customer(
            name=data['name'],
            email=data['email'],
            phone=data['phone']
        )
        db.session.add(new_customer)
        db.session.commit()
        return jsonify(customer_schema.dump(new_customer)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Get all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    """Retrieve all customers"""
    customers = Customer.query.all()
    return jsonify(customers_schema.dump(customers)), 200

# Get a single customer by ID
@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Retrieve a single customer by ID"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify(customer_schema.dump(customer)), 200

# Update a customer
@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update a customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        data = request.get_json()
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        
        db.session.commit()
        return jsonify(customer_schema.dump(customer)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Delete a customer
@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== MEMBER ROUTES ====================

# Create a new member
@app.route('/members', methods=['POST'])
def create_member():
    """Create a new member"""
    try:
        data = request.get_json()
        new_member = Member(
            name=data['name'],
            email=data['email'],
            phone=data['phone']
        )
        db.session.add(new_member)
        db.session.commit()
        return jsonify(member_schema.dump(new_member)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Get all members
@app.route('/members', methods=['GET'])
def get_members():
    """Retrieve all members"""
    members = Member.query.all()
    return jsonify(members_schema.dump(members)), 200

# Get a single member by ID
@app.route('/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    """Retrieve a single member by ID"""
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    return jsonify(member_schema.dump(member)), 200

# Update a member
@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Update a member"""
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Member not found'}), 404
        
        data = request.get_json()
        member.name = data.get('name', member.name)
        member.email = data.get('email', member.email)
        member.phone = data.get('phone', member.phone)
        
        db.session.commit()
        return jsonify(member_schema.dump(member)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Delete a member
@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Delete a member"""
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Member not found'}), 404
        
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Member deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Create all tables
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True)
