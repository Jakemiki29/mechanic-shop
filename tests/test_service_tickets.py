import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.pool import StaticPool

from app import app
from extensions import cache
from models import db, Customer, Mechanic, Inventory, ServiceTicket
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


class TestServiceTickets(unittest.TestCase):

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

    def _create_customer(self, email="owner@example.com"):
        with self.app.app_context():
            customer = Customer()
            customer.name = "Ticket Owner"
            customer.email = email
            customer.phone = "555-1111"
            customer.password = generate_password_hash("password")
            db.session.add(customer)
            db.session.commit()
            return customer.id

    def _token_for(self, customer_id):
        with self.app.app_context():
            return encode_token(customer_id)

    def _create_mechanic(self, email="mech@shop.com"):
        with self.app.app_context():
            mechanic = Mechanic()
            mechanic.name = "Test Mechanic"
            mechanic.email = email
            mechanic.phone = "555-2222"
            mechanic.salary = 50000.0
            db.session.add(mechanic)
            db.session.commit()
            return mechanic.id

    def _create_part(self, name="Brake Pads"):
        with self.app.app_context():
            part = Inventory()
            part.name = name
            part.price = 45.00
            db.session.add(part)
            db.session.commit()
            return part.id

    def _create_ticket(self, customer_id):
        with self.app.app_context():
            ticket = ServiceTicket()
            ticket.VIN = "1HGCM82633A123456"
            ticket.service_date = "2026-03-15"
            ticket.service_desc = "Oil change"
            ticket.customer_id = customer_id
            db.session.add(ticket)
            db.session.commit()
            return ticket.id

    # ── POST / ────────────────────────────────────────────────────────────────

    def test_create_service_ticket_success(self):
        customer_id = self._create_customer()
        response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "1HGCM82633A123456",
                "service_date": "2026-03-15",
                "service_desc": "Oil change",
                "customer_id": customer_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["VIN"], "1HGCM82633A123456")
        self.assertIn("mechanic_ids", data)
        self.assertIn("part_ids", data)

    def test_create_service_ticket_missing_fields(self):
        response = self.client.post(
            "/service-tickets/",
            json={"VIN": "1HGCM82633A123456"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_service_ticket_null_customer_id(self):
        """customer_id=None violates the NOT NULL constraint and returns 400."""
        response = self.client.post(
            "/service-tickets/",
            json={
                "VIN": "BADVIN000000000",
                "service_date": "2026-03-15",
                "service_desc": "Oil change",
                "customer_id": None,
            },
        )
        self.assertEqual(response.status_code, 400)

    # ── GET / ─────────────────────────────────────────────────────────────────

    def test_get_service_tickets_empty(self):
        response = self.client.get("/service-tickets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_get_service_tickets_returns_list(self):
        customer_id = self._create_customer()
        self._create_ticket(customer_id)
        response = self.client.get("/service-tickets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)

    # ── PUT /<ticket_id>/assign-mechanic/<mechanic_id> ────────────────────────

    def test_assign_mechanic_success(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("mechanic_ids", response.get_json()["ticket"])

    def test_assign_mechanic_no_token(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mechanic_id = self._create_mechanic()
        response = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
        )
        self.assertEqual(response.status_code, 401)

    def test_assign_mechanic_ticket_not_found(self):
        customer_id = self._create_customer()
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/9999/assign-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    def test_assign_mechanic_mechanic_not_found(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    def test_assign_mechanic_unauthorized(self):
        owner_id = self._create_customer(email="owner@example.com")
        other_id = self._create_customer(email="other@example.com")
        ticket_id = self._create_ticket(owner_id)
        mechanic_id = self._create_mechanic()
        token = self._token_for(other_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    # ── PUT /<ticket_id>/remove-mechanic/<mechanic_id> ────────────────────────

    def test_remove_mechanic_success(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        # Assign first
        self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Then remove
        response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("removed", response.get_json()["message"])

    def test_remove_mechanic_not_assigned(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mechanic_id = self._create_mechanic()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_mechanic_no_token(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mechanic_id = self._create_mechanic()
        response = self.client.put(
            f"/service-tickets/{ticket_id}/remove-mechanic/{mechanic_id}"
        )
        self.assertEqual(response.status_code, 401)

    # ── PUT /<ticket_id>/add-part/<part_id> ───────────────────────────────────

    def test_add_part_to_ticket_success(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        part_id = self._create_part()
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(part_id, response.get_json()["ticket"]["part_ids"])

    def test_add_part_to_ticket_already_added(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        part_id = self._create_part()
        token = self._token_for(customer_id)
        self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Second add should not error
        response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_add_part_to_ticket_part_not_found(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    def test_add_part_to_ticket_no_token(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        part_id = self._create_part()
        response = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}"
        )
        self.assertEqual(response.status_code, 401)

    # ── PUT /<ticket_id>/edit ─────────────────────────────────────────────────

    def test_edit_ticket_mechanics_success(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        mech1_id = self._create_mechanic(email="m1@shop.com")
        mech2_id = self._create_mechanic(email="m2@shop.com")
        token = self._token_for(customer_id)
        # Add mech1, then use edit to swap to mech2
        self.client.put(
            f"/service-tickets/{ticket_id}/assign-mechanic/{mech1_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [mech2_id], "remove_ids": [mech1_id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        mechanic_ids = response.get_json()["mechanic_ids"]
        self.assertIn(mech2_id, mechanic_ids)
        self.assertNotIn(mech1_id, mechanic_ids)

    def test_edit_ticket_mechanics_invalid_payload(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        token = self._token_for(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": "not-a-list"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_ticket_mechanics_no_token(self):
        customer_id = self._create_customer()
        ticket_id = self._create_ticket(customer_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [], "remove_ids": []},
        )
        self.assertEqual(response.status_code, 401)

    def test_edit_ticket_mechanics_ticket_not_found(self):
        customer_id = self._create_customer()
        token = self._token_for(customer_id)
        response = self.client.put(
            "/service-tickets/9999/edit",
            json={"add_ids": [], "remove_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_ticket_mechanics_unauthorized(self):
        owner_id = self._create_customer(email="owner2@example.com")
        other_id = self._create_customer(email="other2@example.com")
        ticket_id = self._create_ticket(owner_id)
        token = self._token_for(other_id)
        response = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            json={"add_ids": [], "remove_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
