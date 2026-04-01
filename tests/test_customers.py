import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.pool import StaticPool

from app import app
from extensions import cache
from models import db, Customer
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


class TestCustomers(unittest.TestCase):

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

    def _create_customer(self, name="Jane Doe", email="jane@example.com",
                          phone="555-1234", password="secret"):
        with self.app.app_context():
            customer = Customer()
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.password = generate_password_hash(password)
            db.session.add(customer)
            db.session.commit()
            return customer.id

    def _token_for(self, customer_id):
        with self.app.app_context():
            return encode_token(customer_id)

    # ── POST / ────────────────────────────────────────────────────────────────

    def test_create_customer_success(self):
        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "password": "secret",
        }
        response = self.client.post("/customers/", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["name"], "Jane Doe")
        self.assertEqual(data["email"], "jane@example.com")
        self.assertNotIn("password", data)

    def test_create_customer_missing_fields(self):
        payload = {"name": "No Email"}
        response = self.client.post("/customers/", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_customer_duplicate_email(self):
        self._create_customer(email="dup@example.com")
        payload = {
            "name": "Other",
            "email": "dup@example.com",
            "phone": "555-0000",
            "password": "pass",
        }
        response = self.client.post("/customers/", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already exists", response.get_json()["error"])

    # ── GET / ─────────────────────────────────────────────────────────────────

    def test_get_customers_empty(self):
        response = self.client.get("/customers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_get_customers_returns_list(self):
        self._create_customer()
        response = self.client.get("/customers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    # ── GET /<id> ─────────────────────────────────────────────────────────────

    def test_get_customer_success(self):
        customer_id = self._create_customer()
        response = self.client.get(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], customer_id)

    def test_get_customer_not_found(self):
        response = self.client.get("/customers/9999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    # ── PUT /<id> ─────────────────────────────────────────────────────────────

    def test_update_customer_success(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/customers/{customer_id}",
            json={"name": "Jane Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Jane Updated")

    def test_update_customer_no_token(self):
        customer_id = self._create_customer()
        response = self.client.put(f"/customers/{customer_id}", json={"name": "X"})
        self.assertEqual(response.status_code, 401)

    def test_update_customer_wrong_customer(self):
        id1 = self._create_customer(email="c1@example.com")
        id2 = self._create_customer(name="Bob", email="c2@example.com")
        token = self._token_for(id1)
        response = self.client.put(
            f"/customers/{id2}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_update_customer_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        with self.app.app_context():
            db.session.query(Customer).delete()
            db.session.commit()
        response = self.client.put(
            f"/customers/{customer_id}",
            json={"name": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    # ── DELETE /<id> ─────────────────────────────────────────────────────────

    def test_delete_customer_success(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.delete(
            f"/customers/{customer_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_customer_no_token(self):
        customer_id = self._create_customer()
        response = self.client.delete(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, 401)

    def test_delete_customer_wrong_customer(self):
        id1 = self._create_customer(email="del1@example.com")
        id2 = self._create_customer(name="Bob", email="del2@example.com")
        token = self._token_for(id1)
        response = self.client.delete(
            f"/customers/{id2}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    # ── POST /login ───────────────────────────────────────────────────────────

    def test_login_success(self):
        self._create_customer(email="login@example.com", password="mypassword")
        response = self.client.post(
            "/customers/login",
            json={"email": "login@example.com", "password": "mypassword"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("token", data)
        self.assertIn("customer_id", data)

    def test_login_wrong_password(self):
        self._create_customer(email="wp@example.com", password="correct")
        response = self.client.post(
            "/customers/login",
            json={"email": "wp@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    def test_login_email_not_found(self):
        response = self.client.post(
            "/customers/login",
            json={"email": "nobody@example.com", "password": "pass"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        response = self.client.post("/customers/login", json={"email": "only@example.com"})
        self.assertEqual(response.status_code, 400)

    # ── GET /my-tickets ───────────────────────────────────────────────────────

    def test_my_tickets_no_tickets(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.get(
            "/customers/my-tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_my_tickets_no_token(self):
        response = self.client.get("/customers/my-tickets")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
