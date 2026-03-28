from models import Member, ma


class MemberSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Member


member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
