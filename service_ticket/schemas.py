from marshmallow import fields

from models import ma, ServiceTicket

# ServiceTicket Schema
class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket

    mechanic_ids = fields.Method('get_mechanic_ids')
    part_ids = fields.Method('get_part_ids')

    def get_mechanic_ids(self, obj):
        return [mechanic.id for mechanic in obj.mechanics]

    def get_part_ids(self, obj):
        return [part.id for part in obj.parts]

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
