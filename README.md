# Mechanic Shop API

A Flask REST API for managing a mechanic shop, including:
- Customers
- Members
- Mechanics
- Service tickets
- Mechanic assignment to service tickets (many-to-many)
- Inventory parts
- Part assignment to service tickets (many-to-many)

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Marshmallow
- Flask-Limiter
- Flask-Caching
- python-jose (JWT)
- Marshmallow
- SQLite (default local database)

## Project Structure

```text
mechanic-shop/
|-- app.py
|-- models.py
|-- requirements.txt
|-- mechanic/
|   |-- __init__.py
|   |-- routes.py
|   `-- schemas.py
|-- service_ticket/
|   |-- __init__.py
|   |-- routes.py
|   `-- schemas.py
`-- postman/
    `-- mechanic-shop.postman_collection.json
```

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the API

```bash
python app.py
```

When the app starts:
- Database tables are auto-created with `db.create_all()`
- The API runs in debug mode
- Default URL: `http://127.0.0.1:5000`

## Database

- Configured in `app.py` as: `sqlite:///users.db`
- Tables are defined in `models.py`

Main models:
- `Customer`
- `Member`
- `Mechanic`
- `ServiceTicket`
- `Inventory`
- `service_mechanics` (association table for ticket-mechanic many-to-many)
- `service_ticket_parts` (association table for ticket-part many-to-many)

## API Endpoints

### Health/Home

- `GET /`

Returns a basic status message and top-level endpoint list.

### Customers

- `POST /customers`
- `GET /customers?page=1&per_page=10` (paginated + cached)
- `GET /customers/<customer_id>`
- `PUT /customers/<customer_id>` (Bearer token required)
- `DELETE /customers/<customer_id>` (Bearer token required)
- `POST /customers/login` (rate limited: `5 per minute`)
- `GET /customers/my-tickets` (Bearer token required)

Create payload example:

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "555-1234",
  "password": "password123"
}
```

### Members

- `POST /members`
- `GET /members`
- `GET /members/<member_id>`
- `PUT /members/<member_id>`
- `DELETE /members/<member_id>`

Create payload example:

```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "555-5678"
}
```

### Mechanics

Blueprint prefix: `/mechanics`

- `POST /mechanics/`
- `GET /mechanics/` (cached)
- `GET /mechanics/most-tickets` (cached)
- `PUT /mechanics/<id>` (Bearer token required)
- `DELETE /mechanics/<id>` (Bearer token required)

Create payload example:

```json
{
  "name": "Alex Wrench",
  "email": "alex@shop.com",
  "phone": "555-0001",
  "salary": 62000
}
```

### Service Tickets

Blueprint prefix: `/service-tickets`

- `POST /service-tickets/` (Bearer token required)
- `GET /service-tickets/`
- `PUT /service-tickets/<ticket_id>/assign-mechanic/<mechanic_id>` (Bearer token required)
- `PUT /service-tickets/<ticket_id>/remove-mechanic/<mechanic_id>` (Bearer token required)
- `PUT /service-tickets/<ticket_id>/add-part/<part_id>` (Bearer token required)
- `PUT /service-tickets/<ticket_id>/edit` (Bearer token required)

Create payload example:

```json
{
  "VIN": "1HGCM82633A004352",
  "service_date": "2026-03-19",
  "service_desc": "Oil change and tire rotation",
  "customer_id": 1
}
```

### Inventory

Blueprint prefix: `/inventory`

- `POST /inventory/` (Bearer token required)
- `GET /inventory/`
- `GET /inventory/<part_id>`
- `PUT /inventory/<part_id>` (Bearer token required)
- `DELETE /inventory/<part_id>` (Bearer token required)

Create payload example:

```json
{
  "name": "Brake Pad Set",
  "price": 129.99
}
```

## Postman

A ready-made Postman collection is included:

- `postman/mechanic-shop.postman_collection.json`

Import it into Postman to test all endpoints quickly.

## Notes

- Error responses generally return JSON in this shape:

```json
{
  "error": "description"
}
```

- Successful delete responses return a message JSON object.
- Assignment routes prevent duplicate ticket-mechanic assignments.
