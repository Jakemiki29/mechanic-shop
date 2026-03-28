from models import Inventory, ma


class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory


inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
