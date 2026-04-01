import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.pool import StaticPool

from app import app
from extensions import cache
from models import db, Customer, Inventory
from auth import encode_token
from werkzeug.security import generate_password_hash


def create_app_for_testing():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    app.config["SECRET_KEY"] = "test-secret"
    app.config["CACHE_TYPE"] = "NullCache"
    app.config["RATELIMIT_ENABLED"] = False
    return app


class TestInventory(unittest.TestCase):

    def setUp(self):
        self.app = create_app_for_testing()
        self.client = self.app.test_client()
        with self.app.app_context():
            cache.init_app(self.app)
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _create_customer(self):
        with self.app.app_context():
            customer = Customer()
            customer.name = "Test User"
            customer.email = "testuser@example.com"
            customer.phone = "555-0000"
            customer.password = generate_password_hash("password")
            db.session.add(customer)
            db.session.commit()
            return customer.id

    def _token_for(self, customer_id):
        with self.app.app_context():
            return encode_token(customer_id)

    def _create_part(self, name="Oil Filter", price=12.99):
        with self.app.app_context():
            part = Inventory()
            part.name = name
            part.price = price
            db.session.add(part)
            db.session.commit()
            return part.id

    # ── POST / ────────────────────────────────────────────────────────────────

    def test_create_inventory_part_success(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.post(
            "/inventory/",
            json={"name": "Oil Filter", "price": 12.99},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["name"], "Oil Filter")
        self.assertEqual(data["price"], 12.99)

    def test_create_inventory_part_missing_fields(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.post(
            "/inventory/",
            json={"name": "No Price"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_inventory_part_no_token(self):
        response = self.client.post(
            "/inventory/",
            json={"name": "Brake Pads", "price": 45.00},
        )
        self.assertEqual(response.status_code, 401)

    # ── GET / ─────────────────────────────────────────────────────────────────

    def test_get_inventory_parts_empty(self):
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_get_inventory_parts_returns_list(self):
        self._create_part()
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    # ── GET /<part_id> ────────────────────────────────────────────────────────

    def test_get_inventory_part_success(self):
        part_id = self._create_part()
        response = self.client.get(f"/inventory/{part_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], part_id)

    def test_get_inventory_part_not_found(self):
        response = self.client.get("/inventory/9999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    # ── PUT /<part_id> ────────────────────────────────────────────────────────

    def test_update_inventory_part_success(self):
        customer_id = self._create_customer()
        part_id = self._create_part()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/inventory/{part_id}",
            json={"price": 19.99},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["price"], 19.99)

    def test_update_inventory_part_no_token(self):
        part_id = self._create_part()
        response = self.client.put(f"/inventory/{part_id}", json={"price": 5.00})
        self.assertEqual(response.status_code, 401)

    def test_update_inventory_part_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.put(
            "/inventory/9999",
            json={"price": 5.00},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    # ── DELETE /<part_id> ─────────────────────────────────────────────────────

    def test_delete_inventory_part_success(self):
        customer_id = self._create_customer()
        part_id = self._create_part()
        token = self._token_for(customer_id)
        response = self.client.delete(
            f"/inventory/{part_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted", response.get_json()["message"])

    def test_delete_inventory_part_no_token(self):
        part_id = self._create_part()
        response = self.client.delete(f"/inventory/{part_id}")
        self.assertEqual(response.status_code, 401)

    def test_delete_inventory_part_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.delete(
            "/inventory/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
