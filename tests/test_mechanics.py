import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.pool import StaticPool

from app import app
from extensions import cache
from models import db, Customer, Mechanic
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


class TestMechanics(unittest.TestCase):

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

    def _create_mechanic(self, name="Carlos Rivera", email="carlos@shop.com",
                          phone="555-2020", salary=55000.0):
        with self.app.app_context():
            mechanic = Mechanic()
            mechanic.name = name
            mechanic.email = email
            mechanic.phone = phone
            mechanic.salary = salary
            db.session.add(mechanic)
            db.session.commit()
            return mechanic.id

    # ── POST / ────────────────────────────────────────────────────────────────

    def test_create_mechanic_success(self):
        payload = {
            "name": "Carlos Rivera",
            "email": "carlos@shop.com",
            "phone": "555-2020",
            "salary": 55000.0,
        }
        response = self.client.post("/mechanics/", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["name"], "Carlos Rivera")
        self.assertEqual(data["salary"], 55000.0)

    def test_create_mechanic_missing_fields(self):
        payload = {"name": "No Salary"}
        response = self.client.post("/mechanics/", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_mechanic_duplicate_email(self):
        self._create_mechanic(email="dup@shop.com")
        payload = {
            "name": "Other",
            "email": "dup@shop.com",
            "phone": "555-9999",
            "salary": 40000.0,
        }
        response = self.client.post("/mechanics/", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already exists", response.get_json()["error"])

    # ── GET / ─────────────────────────────────────────────────────────────────

    def test_get_mechanics_empty(self):
        response = self.client.get("/mechanics/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_get_mechanics_returns_list(self):
        self._create_mechanic()
        response = self.client.get("/mechanics/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    # ── PUT /<id> ─────────────────────────────────────────────────────────────

    def test_update_mechanic_success(self):
        customer_id = self._create_customer()
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/mechanics/{mechanic_id}",
            json={"salary": 65000.0},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["salary"], 65000.0)

    def test_update_mechanic_no_token(self):
        mechanic_id = self._create_mechanic()
        response = self.client.put(f"/mechanics/{mechanic_id}", json={"salary": 70000.0})
        self.assertEqual(response.status_code, 401)

    def test_update_mechanic_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.put(
            "/mechanics/9999",
            json={"name": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    # ── DELETE /<id> ─────────────────────────────────────────────────────────

    def test_delete_mechanic_success(self):
        customer_id = self._create_customer()
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        response = self.client.delete(
            f"/mechanics/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("deleted", response.get_json()["message"])

    def test_delete_mechanic_no_token(self):
        mechanic_id = self._create_mechanic()
        response = self.client.delete(f"/mechanics/{mechanic_id}")
        self.assertEqual(response.status_code, 401)

    def test_delete_mechanic_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.delete(
            "/mechanics/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    # ── GET /most-tickets ─────────────────────────────────────────────────────

    def test_mechanics_by_ticket_count_empty(self):
        response = self.client.get("/mechanics/most-tickets")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_mechanics_by_ticket_count_with_data(self):
        self._create_mechanic(name="Mech One", email="one@shop.com")
        self._create_mechanic(name="Mech Two", email="two@shop.com")
        response = self.client.get("/mechanics/most-tickets")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)


if __name__ == "__main__":
    unittest.main()
