# API Reference

Base URL: `/api/v1`

All API endpoints require authentication via a Bearer token unless otherwise noted. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## Rate Limits

All endpoints are subject to rate limiting enforced by SlowAPI:

| Endpoint Group     | Rate Limit    |
|--------------------|---------------|
| Auth endpoints     | 5/minute      |
| Invite endpoint    | 3/minute      |
| Dashboard          | 60/minute     |
| All other endpoints | 100/minute   |

## Authentication Endpoints

### POST /auth/register

Register a new user and create a new organization.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "Jane Doe",
  "org_name": "Maritime Shipping Co",
  "industry": "Shipping",
  "invite_emails": ["colleague@example.com"]
}
```

**Response (201):**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

**Headers:**
- `refresh_token` set as httpOnly cookie

**Auth Required:** No

---

### POST /auth/login

Authenticate with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

**Headers:**
- `refresh_token` set as httpOnly cookie

**Auth Required:** No

---

### POST /auth/logout

Invalidate the current session by blacklisting tokens.

**Response (200):**
```json
{
  "message": "Logged out"
}
```

**Auth Required:** Yes (Bearer token + refresh_token cookie)

---

### POST /auth/refresh

Refresh an expired access token using the refresh token cookie.

**Response (200):**
```json
{
  "access_token": "<new_jwt_token>",
  "token_type": "bearer"
}
```

**Headers:**
- Old refresh token blacklisted; new `refresh_token` cookie set

**Auth Required:** Yes (refresh_token cookie only)

---

### GET /auth/me

Get the current user's profile and organization details.

**Response (200):**
```json
{
  "user": {
    "id": "abc123",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "role": "Org Admin",
    "org_id": "org_xyz",
    "is_active": true,
    "created_at": "2026-01-15T10:00:00Z"
  },
  "organization": {
    "_id": "org_xyz",
    "name": "Maritime Shipping Co",
    "industry": "Shipping",
    "created_at": "2026-01-15T10:00:00Z"
  }
}
```

**Auth Required:** Yes

---

### POST /auth/invite

Invite new users to the organization. Invited users always receive the `Operator` role.

**Request Body:**
```json
{
  "emails": ["colleague@example.com"],
  "role": "Operator"
}
```

**Response (200):**
```json
{
  "invited": [
    {"email": "colleague@example.com", "status": "invited", "role": "Operator"},
    {"email": "existing@example.com", "status": "already_exists", "role": "Operator"}
  ]
}
```

**Auth Required:** Yes (Org Admin role required)
**Rate Limit:** 3/minute

---

## Fleet Endpoints

### GET /fleet/ships

List ships for the current organization with search and filtering.

**Query Parameters:**

| Parameter    | Type   | Description                            |
|--------------|--------|----------------------------------------|
| `search`     | string | Search by ship name or IMO number      |
| `vessel_type`| string | Filter by vessel type                  |
| `fuel_type`  | string | Filter by fuel type                    |
| `status`     | string | Filter by status (`active`, `inactive`)|
| `page`       | int    | Page number (default: 1)               |
| `page_size`  | int    | Items per page, max 100 (default: 20)  |

**Response (200):**
```json
{
  "ships": [
    {
      "id": "ship_001",
      "imo_number": "IMO1234567",
      "name": "Ocean Voyager",
      "flag_state": "Panama",
      "vessel_type": "Container",
      "gross_tonnage": 50000.0,
      "dwt": 60000.0,
      "fuel_type": "HFO",
      "status": "active",
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-06-15T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Auth Required:** Yes

---

### POST /fleet/ships

Add a new ship to the fleet.

**Request Body:**
```json
{
  "imo_number": "IMO9876543",
  "name": "New Vessel",
  "flag_state": "Liberia",
  "vessel_type": "Tanker",
  "gross_tonnage": 75000.0,
  "dwt": 85000.0,
  "fuel_type": "MGO",
  "status": "active"
}
```

**Response (201):**
```json
{
  "ship": { ...ship object... },
  "message": "Ship created successfully"
}
```

**Auth Required:** Yes (Fleet Manager or Org Admin role)

---

### GET /fleet/ships/{ship_id}

Get detailed information about a specific ship.

**Path Parameters:**
- `ship_id` (string, required) — The ship ID

**Response (200):**
```json
{
  "ship": { ...ship object... }
}
```

**Auth Required:** Yes

---

### PUT /fleet/ships/{ship_id}

Update ship details.

**Request Body (all fields optional):**
```json
{
  "name": "Updated Vessel Name",
  "status": "inactive"
}
```

**Response (200):**
```json
{
  "ship": { ...updated ship object... },
  "message": "Ship updated successfully"
}
```

**Auth Required:** Yes (Fleet Manager or Org Admin role)

---

### DELETE /fleet/ships/{ship_id}

Soft delete a ship. Associated voyages are also marked as deleted.

**Response (200):**
```json
{
  "message": "Ship soft deleted successfully"
}
```

**Auth Required:** Yes (Org Admin role)

---

## Emissions Endpoints

### POST /emissions/voyages

Create a voyage log and automatically compute emissions using IMO DCS methodology.

**Request Body:**
```json
{
  "asset_id": "ship_001",
  "departure_port": "Singapore",
  "arrival_port": "Rotterdam",
  "departure_date": "2026-06-01T00:00:00Z",
  "arrival_date": "2026-06-15T00:00:00Z",
  "fuel_type": "HFO",
  "fuel_consumed_mt": 150.5,
  "distance_nm": 12500.0,
  "cargo_mt": 20000.0
}
```

**Response (201):**
```json
{
  "voyage": { ...voyage object... },
  "emissions": {
    "id": "emission_001",
    "asset_id": "ship_001",
    "org_id": "org_xyz",
    "voyage_id": "voyage_001",
    "calculation_version": 1,
    "methodology": "IMO",
    "fuel_type": "HFO",
    "fuel_consumed_mt": 150.5,
    "emissions": {
      "co2": 475.25,
      "ch4": 1.43,
      "n2o": 0.38,
      "sox": 3.80,
      "nox": 5.20
    },
    "co2_equivalent": 485.12,
    "calculated_at": "2026-06-01T00:00:00Z",
    "is_current": true
  },
  "message": "Voyage created and emissions computed"
}
```

**Auth Required:** Yes (Operator, Fleet Manager, Org Admin, or Compliance Officer role)

---

### GET /emissions/voyages

List voyage logs for the organization with optional filters.

**Query Parameters:**

| Parameter    | Type   | Description                          |
|--------------|--------|--------------------------------------|
| `asset_id`   | string | Filter by asset/ship ID              |
| `period`     | string | Filter by period (`YYYY` or `YYYY-MM`)|
| `search`     | string | Search by port names                 |
| `page`       | int    | Page number (default: 1)             |
| `page_size`  | int    | Items per page, max 100 (default: 20)|

**Response (200):**
```json
{
  "voyages": [...voyage objects...],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

**Auth Required:** Yes

---

### GET /emissions/voyages/{voyage_id}

Get a single voyage with its complete emissions calculation history.

**Response (200):**
```json
{
  "voyage": { ...voyage object... },
  "emissions_history": [
    {
      "id": "emission_v1",
      "calculation_version": 1,
      "emissions": { ... },
      "calculated_at": "2026-06-01T00:00:00Z",
      "is_current": false
    },
    {
      "id": "emission_v2",
      "calculation_version": 2,
      "emissions": { ... },
      "calculated_at": "2026-06-20T00:00:00Z",
      "is_current": true
    }
  ]
}
```

**Auth Required:** Yes

---

### PUT /emissions/voyages/{voyage_id}

Update a voyage log. Recomputes emissions and creates a new version.

**Request Body (all fields optional, uses VoyageUpdate model):**
```json
{
  "fuel_consumed_mt": 160.0,
  "distance_nm": 13000.0
}
```

**Response (200):**
```json
{
  "voyage": { ...updated voyage... },
  "emissions": { ...new emissions version... },
  "message": "Voyage updated (emissions version 2)"
}
```

**Auth Required:** Yes (Fleet Manager, Org Admin, or Compliance Officer role)

---

### DELETE /emissions/voyages/{voyage_id}

Delete a voyage log and all associated emissions records.

**Response (200):**
```json
{
  "message": "Voyage deleted successfully"
}
```

**Auth Required:** Yes (Fleet Manager or Org Admin role)

---

### GET /emissions/summary

Aggregated emissions analytics for the organization.

**Query Parameters:**

| Parameter   | Type   | Description                          | Default     |
|-------------|--------|--------------------------------------|-------------|
| `period`    | string | Time period (`month`, `quarter`, `year`)| `month`   |
| `group_by`  | string | Group by (`vessel` or `fuel_type`)   | `vessel`    |

**Response (200):**
```json
{
  "total_co2": 1250.75,
  "total_co2e": 1340.20,
  "total_fuel_mt": 420.5,
  "avg_eefi": 15.32,
  "by_fuel_type": {
    "HFO": { "co2": 900.0, "co2e": 960.0, "fuel_mt": 300.0, "voyage_count": 10 },
    "MGO": { "co2": 350.75, "co2e": 380.2, "fuel_mt": 120.5, "voyage_count": 5 }
  },
  "by_pollutant": { "co2": 1250.75, "ch4": 3.8, "n2o": 1.0, "sox": 10.0, "nox": 14.0 },
  "by_vessel": { "ship_001": { "co2": 800.0, "co2e": 855.0, "fuel_mt": 250.0 } },
  "period": "month",
  "group_by": "vessel",
  "voyage_count": 15
}
```

**Auth Required:** Yes

---

## Reports Endpoints

### POST /reports/generate

Queue an IMO DCS Annual Compliance Report for background generation.

**Request Body:**
```json
{
  "year": 2026
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "celery_task_id",
  "status": "queued",
  "message": "Report generation queued",
  "fleet_summary": {
    "total_ships": 5,
    "total_fuel_consumed_mt": 500.0,
    "total_co2_emissions_tonnes": 1500.0,
    "total_transport_work_tonne_miles": 5000000.0
  }
}
```

**Auth Required:** Yes (Compliance Officer or Org Admin role)

---

### GET /reports

List all generated reports for the current organization.

**Response (200):**
```json
{
  "reports": [
    {
      "id": "report_001",
      "org_id": "org_xyz",
      "year": 2026,
      "status": "Generated",
      "report_type": "IMO DCS Annual",
      "generated_at": "2026-06-15T10:00:00Z",
      "task_id": "celery_task_id",
      "fleet_summary": { ... }
    }
  ],
  "total": 1
}
```

**Auth Required:** Yes

---

### GET /reports/{report_id}

Get report details.

**Response (200):**
```json
{
  "report": { ...report object... }
}
```

**Auth Required:** Yes

---

### GET /reports/{report_id}/download

Download the generated PDF report file.

**Response:** PDF file (`application/pdf`)

**Headers:**
- `Content-Disposition: attachment; filename="IMO_DCS_Report_2026_report_id.pdf"`

**Auth Required:** Yes

---

### PATCH /reports/{report_id}/status

Update report status through the lifecycle: Draft → Generated → Submitted.

**Request Body:**
```json
{
  "status": "Submitted"
}
```

**Valid Statuses:** `Draft`, `Generated`, `Submitted`

**Response (200):**
```json
{
  "report_id": "report_001",
  "status": "Submitted",
  "message": "Report status updated from Generated to Submitted"
}
```

**Auth Required:** Yes (Compliance Officer or Org Admin role)

---

## Dashboard Endpoints

### GET /dashboard/summary

Returns fleet summary metrics for the current organization.

**Response (200):**
```json
{
  "total_ships": 10,
  "active_ships": 7,
  "green_count": 5,
  "yellow_count": 3,
  "red_count": 2,
  "total_co2_ytd": 5200.5,
  "total_fuel_ytd": 1750.0,
  "avg_cii_rating": "B"
}
```

**CII Rating Scale:** A (best) through E (worst)

**Auth Required:** Yes (Operator, Fleet Manager, Org Admin, or Compliance Officer role)

---

## Request/Response Schema Reference

### Common Schemas

**ShipCreate:**
```json
{
  "imo_number": "string",
  "name": "string",
  "flag_state": "string",
  "vessel_type": "string (one of: Bulk Carrier, Tanker, Container, Ro-Ro, General Cargo, Gas Carrier)",
  "gross_tonnage": "number",
  "dwt": "number",
  "fuel_type": "string (one of: HFO, MGO, LNG, Methanol)",
  "status": "string (one of: active, inactive)"
}
```

**VoyageCreate:**
```json
{
  "asset_id": "string",
  "departure_port": "string",
  "arrival_port": "string",
  "departure_date": "datetime",
  "arrival_date": "datetime (optional)",
  "fuel_type": "string",
  "fuel_consumed_mt": "number",
  "distance_nm": "number",
  "cargo_mt": "number (optional, default 0)"
}
```

**VoyageUpdate (all fields optional):**
```json
{
  "departure_port": "string (optional)",
  "arrival_port": "string (optional)",
  "departure_date": "datetime (optional)",
  "arrival_date": "datetime (optional)",
  "fuel_type": "string (optional)",
  "fuel_consumed_mt": "number (optional)",
  "distance_nm": "number (optional)",
  "cargo_mt": "number (optional)"
}
```

**ReportCreate:**
```json
{
  "year": 2026
}
```

**ReportStatusUpdate:**
```json
{
  "status": "Draft | Generated | Submitted"
}
```

### Error Responses

All errors follow this format:
```json
{
  "detail": "Error message or array of validation errors"
}
```

Common HTTP status codes:
- `400` — Bad request / validation error
- `401` — Unauthorized (missing or invalid token)
- `403` — Forbidden (insufficient permissions)
- `404` — Resource not found
- `409` — Conflict (duplicate entry)
- `422` — Unprocessable entity (validation error)
- `429` — Rate limit exceeded
- `500` — Internal server error
- `503` — Service degraded (health check failure)
