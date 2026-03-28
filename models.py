from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

# Association table for many-to-many relationship between service_tickets and mechanics
service_mechanics = db.Table('service_mechanics',
    db.Column('ticket_id', db.Integer, db.ForeignKey('service_tickets.id'), primary_key=True),
    db.Column('mechanic_id', db.Integer, db.ForeignKey('mechanics.id'), primary_key=True)
)

# Association table for many-to-many relationship between service_tickets and inventory
service_ticket_parts = db.Table(
    'service_ticket_parts',
    db.Column('ticket_id', db.Integer, db.ForeignKey('service_tickets.id'), primary_key=True),
    db.Column('inventory_id', db.Integer, db.ForeignKey('inventory.id'), primary_key=True),
)

# Customer Model
class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # One-to-Many relationship: One customer can have many service tickets
    service_tickets = db.relationship('ServiceTicket', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'

# ServiceTicket Model
class ServiceTicket(db.Model):
    __tablename__ = 'service_tickets'

    id = db.Column(db.Integer, primary_key=True)
    VIN = db.Column(db.String(255), nullable=False)
    service_date = db.Column(db.String(255), nullable=False)
    service_desc = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    # Many-to-Many relationship: A ticket can have multiple mechanics, and a mechanic can work on multiple tickets
    mechanics = db.relationship('Mechanic', secondary=service_mechanics, backref='service_tickets', lazy=True)
    # Many-to-Many relationship: A ticket can require multiple parts, and parts can be used on many tickets
    parts = db.relationship('Inventory', secondary=service_ticket_parts, backref='service_tickets', lazy=True)

    def __repr__(self):
        return f'<ServiceTicket {self.id} - VIN: {self.VIN}>'

# Mechanic Model
class Mechanic(db.Model):
    __tablename__ = 'mechanics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Mechanic {self.name}>'


class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Inventory {self.name}>'

# Member Model
class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Member {self.name}>'
