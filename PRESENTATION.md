# Mechanic Shop API — 4-Minute Presentation Script

---

## BEFORE YOU HIT RECORD

Open **two** PowerShell windows side by side.

**Window 1** will run the Flask server.  
**Window 2** will send API requests.

Run these in Window 2 to start fresh every time you rehearse:

```powershell
.\venv\Scripts\Activate.ps1
Remove-Item instance\users.db -ErrorAction SilentlyContinue
```

> **Important:** After deleting the DB, restart the Flask server (Window 1) so `db.create_all()` runs and rebuilds the schema with all current columns.

---

## ALL COMMANDS IN ORDER — WINDOW 2 (copy-paste ready)

Run each block **one at a time**, in order. Never close Window 2 — the `$token` and `$h` variables must persist across the whole recording.

```powershell
# ── Step 1: Health check ─────────────────────────────────────────────────────
Invoke-RestMethod http://127.0.0.1:5000/
```

```powershell
# ── Step 2: Create a customer ─────────────────────────────────────────────────
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/customers/" `
  -ContentType "application/json" `
  -Body '{"name":"Jake Smith","email":"jake@shop.com","phone":"555-1234","password":"secret123"}'
```

```powershell
# ── Step 3: Login — store token ───────────────────────────────────────────────
$r = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/customers/login" `
  -ContentType "application/json" `
  -Body '{"email":"jake@shop.com","password":"secret123"}'
$token = $r.token
$h = @{ Authorization = "Bearer $token" }
Write-Host "Token stored. Customer ID: $($r.customer_id)"
```

```powershell
# ── Step 4: Create a mechanic ─────────────────────────────────────────────────
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/mechanics/" `
  -ContentType "application/json" `
  -Body '{"name":"Bob Wrench","email":"bob@shop.com","phone":"555-5678","salary":55000}'
```

```powershell
# ── Step 5: Add an inventory part (JWT required) ──────────────────────────────
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/inventory/" `
  -ContentType "application/json" `
  -Headers $h `
  -Body '{"name":"Oil Filter","price":12.99}'
```

```powershell
# ── Step 6: Create a service ticket (JWT required) ────────────────────────────
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/service-tickets/" `
  -ContentType "application/json" `
  -Headers $h `
  -Body '{"VIN":"1HGBH41JXMN109186","service_date":"2026-03-30","service_desc":"Oil change and filter replacement","customer_id":1}'
```

```powershell
# ── Step 7: Assign mechanic to ticket (many-to-many) ─────────────────────────
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:5000/service-tickets/1/assign-mechanic/1" `
  -Headers $h
```

```powershell
# ── Step 8: Add inventory part to ticket (many-to-many) ──────────────────────
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:5000/service-tickets/1/add-part/1" `
  -Headers $h
```

```powershell
# ── Step 9: Update customer (JWT — owner-only) ────────────────────────────────
Invoke-RestMethod -Method Put `
  -Uri "http://127.0.0.1:5000/customers/1" `
  -ContentType "application/json" `
  -Headers $h `
  -Body '{"phone":"555-9999"}'
```

```powershell
# ── Step 10: Paginated customer list ─────────────────────────────────────────
Invoke-RestMethod "http://127.0.0.1:5000/customers/?page=1&per_page=1"
```

```powershell
# ── Step 11: Rate limit demo — 6th request returns 429 ───────────────────────
1..6 | ForEach-Object {
    try {
        Invoke-RestMethod -Method Post `
          -Uri "http://127.0.0.1:5000/customers/login" `
          -ContentType "application/json" `
          -Body '{"email":"jake@shop.com","password":"wrong"}'
    } catch {
        "Request $_ failed: $($_.Exception.Message)"
    }
}
```

```powershell
# ── Step 12: Mechanics ranked by ticket count (cached endpoint) ───────────────
Invoke-RestMethod "http://127.0.0.1:5000/mechanics/most-tickets"
```

---

## RECORDING SCRIPT

---

### [0:00 – 0:15] Introduction (speak only, no commands)

> *"This is my Mechanic Shop REST API built with Flask. It supports full CRUD for customers, mechanics, inventory parts, and service tickets. It uses JWT authentication, rate limiting with Flask-Limiter, caching with Flask-Caching, pagination, and SQLAlchemy with many-to-many relationships."*

---

### [0:15 – 0:30] Start the Server — Window 1

```powershell
.\venv\Scripts\Activate.ps1
flask run
```

> *"The app is running on port 5000. I'll switch to my second terminal now."*

---

### [0:30 – 0:45] Health Check + Create a Customer — Window 2

```powershell
Invoke-RestMethod http://127.0.0.1:5000/
```

> *"The root endpoint confirms the API is live. Now I'll create a customer — the password is hashed automatically using Werkzeug."*

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/customers/" -ContentType "application/json" -Body '{"name":"Jake Smith","email":"jake@shop.com","phone":"555-1234","password":"secret123"}'
```

---

### [0:45 – 1:05] Login and Store JWT

> *"Now I'll log in to receive a JWT. The login route is rate-limited to 5 requests per minute — I'll demonstrate that shortly."*

```powershell
$r = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/customers/login" -ContentType "application/json" -Body '{"email":"jake@shop.com","password":"secret123"}'
$token = $r.token
$h = @{ Authorization = "Bearer $token" }
```

> *"I'm storing the token in a variable. All protected routes require this Bearer token in the Authorization header."*

---

### [1:05 – 1:20] Create a Mechanic

> *"Adding a mechanic to the shop — no auth required for this one."*

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/mechanics/" -ContentType "application/json" -Body '{"name":"Bob Wrench","email":"bob@shop.com","phone":"555-5678","salary":55000}'
```

---

### [1:20 – 1:35] Add an Inventory Part (JWT required)

> *"Adding an inventory part. This endpoint requires a valid JWT."*

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/inventory/" -ContentType "application/json" -Headers $h -Body '{"name":"Oil Filter","price":12.99}'
```

---

### [1:35 – 2:00] Create a Service Ticket (JWT required)

> *"Creating a service ticket — it's tied to the authenticated customer, so the customer_id in the body is validated against the token."*

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/service-tickets/" -ContentType "application/json" -Headers $h -Body '{"VIN":"1HGBH41JXMN109186","service_date":"2026-03-30","service_desc":"Oil change and filter replacement","customer_id":1}'
```

---

### [2:00 – 2:25] Many-to-Many: Assign Mechanic + Add Part

> *"Now the many-to-many relationships. I'll assign the mechanic to the ticket and add the inventory part — both are backed by association tables in the database."*

```powershell
Invoke-RestMethod -Method Put -Uri "http://127.0.0.1:5000/service-tickets/1/assign-mechanic/1" -Headers $h
```

```powershell
Invoke-RestMethod -Method Put -Uri "http://127.0.0.1:5000/service-tickets/1/add-part/1" -Headers $h
```

> *"The response shows the updated ticket now includes the mechanic and the part."*

---

### [2:25 – 2:45] JWT-Protected Update

> *"Updating my customer's phone number — this requires the token, and the token is checked to ensure you can only edit your own account."*

```powershell
Invoke-RestMethod -Method Put -Uri "http://127.0.0.1:5000/customers/1" -ContentType "application/json" -Headers $h -Body '{"phone":"555-9999"}'
```

---

### [2:45 – 3:05] Pagination

> *"The customers endpoint supports pagination. Here I'm requesting page 1 with 1 result per page. The response includes the total count, current page, total pages, and whether there are more pages."*

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/customers/?page=1&per_page=1"
```

> *"The GET customers and GET mechanics endpoints are also cached for 120 seconds with Flask-Caching, so repeated requests skip the database entirely."*

---

### [3:05 – 3:35] Rate Limiting Demo

> *"Now I'll demonstrate rate limiting. The login route allows a maximum of 5 requests per minute per IP. I'll fire off 6 in a loop — the 6th should return a 429 Too Many Requests."*

```powershell
1..6 | ForEach-Object {
    try {
        Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/customers/login" -ContentType "application/json" -Body '{"email":"jake@shop.com","password":"wrong"}'
    } catch {
        "Request $_ - $($_.Exception.Message)"
    }
}
```

> *"Requests 1 through 5 return 401 for wrong credentials. Request 6 returns 429 — the rate limiter kicked in."*

---

### [3:35 – 3:50] Bonus Analytics Endpoint

> *"Finally, a custom query endpoint — mechanics ranked by the number of tickets they've worked on. This is also cached."*

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/mechanics/most-tickets"
```

---

### [3:50 – 4:00] Wrap-Up (speak only)

> *"That's the full Mechanic Shop REST API — JWT auth, rate limiting, caching, pagination, and many-to-many relationships, all built with Flask and SQLAlchemy. Thank you."*

---

## REQUIREMENTS COVERAGE CHECKLIST

| Requirement | Where Demonstrated |
|---|---|
| Full CRUD (customers) | Create [0:30], Update [2:25], + Login/Read/Delete exist |
| JWT Authentication | Login [0:45], protected routes [1:35, 2:00, 2:25] |
| Rate Limiting | Login loop [3:05] |
| Caching | Mentioned + GET /mechanics/most-tickets [3:35] |
| Pagination | GET /customers/?page=1&per_page=1 [2:45] |
| Many-to-Many Relationships | Assign mechanic + add part [2:00] |
| Marshmallow Serialization | Every response is schema-serialized (implicit) |
| Blueprints | 4 blueprints: customers, mechanics, inventory, service-tickets |

---

## TIPS

- **Rehearse twice** before recording — the commands become muscle memory.
- **Zoom in** on the terminal so output is readable on screen.
- **Paste commands** (Ctrl+V in PowerShell) instead of typing live to save time.
- If a command fails because the DB already has data from a rehearsal, run the cleanup again:
  ```powershell
  Remove-Item instance\users.db -ErrorAction SilentlyContinue
  ```
- The token `$r.token` and headers `$h` must be set in the **same PowerShell session** — don't close Window 2 between steps.
