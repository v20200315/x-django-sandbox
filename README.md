## x-django-sandbox

A Django 6 + DRF + SimpleJWT sandbox that demonstrates:

- Custom email-based `User`
- Multi-company (multi-tenant) model via memberships
- JWT auth (login / refresh / logout)
- Company creation and staff sub-accounts
- API versioning (`/api/v1/...`)
- Automated API tests with `pytest` / `pytest-django`

---

## Stack

- **Python**: 3.12+
- **Django**: 6.x
- **Django REST Framework**
- **djangorestframework-simplejwt**
- **drf-spectacular** (OpenAPI + Swagger UI)
- **uv** (dependency & environment management)
- **pytest** + **pytest-django**

---

## Project structure (relevant apps)

- `config/` – Django project settings, URLs, WSGI/ASGI
- `accounts/`
  - Custom `User` model (UUID primary key, email login)
  - Authentication API (register, login, refresh, logout, forgot/reset)
  - `CompanyMembership` + `CompanyRole` (links users to companies)
  - `tenant.py` – reads `X-Company-ID` and validates membership
- `companies/`
  - `Company` model
  - Company API (create company, create staff accounts)
- `tests/`
  - `accounts/tests/test_auth_api.py` – end-to-end auth flow
  - `companies/tests/test_companies_api.py` – company + staff flows

---

## Setup

From the project root:

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Apply migrations**

   ```bash
   uv run python manage.py migrate
   ```

3. **Run tests (optional)**

   ```bash
   uv run pytest
   ```

4. **Start the dev server**

   ```bash
   uv run python manage.py runserver
   ```

5. **Open Swagger UI**

   - `http://127.0.0.1:8000/api/schema/swagger-ui/`

All APIs below are available under the `/api/v1/...` prefix.

---

## API overview

### Auth / user (app: `accounts`)

Base path: `/api/v1/auth/`

- **Register** – create a *person* (no company yet)
  - `POST /api/v1/auth/register/`
  - Body:
    ```json
    { "email": "user@example.com", "password": "StrongPass123" }
    ```
  - Response: `201 Created` with `user` and JWT `access` / `refresh` tokens.

- **Login**
  - `POST /api/v1/auth/login/`
  - Body:
    ```json
    { "email": "user@example.com", "password": "StrongPass123" }
    ```
  - Response: `200 OK` with `access` / `refresh`.

- **Refresh token**
  - `POST /api/v1/auth/token/refresh/`
  - Body:
    ```json
    { "refresh": "<refresh_token>" }
    ```
  - Response: `200 OK` with new `access`.

- **Logout (server-side)**
  - `POST /api/v1/auth/logout/`
  - Headers: `Authorization: Bearer <access>`
  - Body:
    ```json
    { "refresh": "<refresh_token>" }
    ```
  - Blacklists the refresh token.

- **Current user + memberships**
  - `GET /api/v1/auth/me/`
  - Headers: `Authorization: Bearer <access>`
  - Response: `UserSerializer` including `memberships`:
    ```json
    {
      "id": "...",
      "email": "user@example.com",
      "memberships": [
        {
          "id": "...",
          "company": { "id": "...", "name": "ACME", "created_at": "..." },
          "role": "owner"
        }
      ]
    }
    ```

- **Forgot password**
  - `POST /api/v1/auth/forgot-password/`
  - Body:
    ```json
    { "email": "user@example.com" }
    ```
  - Always returns `200 OK`; if the email exists, a reset token is generated (hook for emailing).

- **Reset password**
  - `POST /api/v1/auth/reset-password/`
  - Body:
    ```json
    { "token": "<reset_token>", "new_password": "NewPass123" }
    ```
  - Response: `200 OK` on success.

---

### Companies & staff (app: `companies`)

Base path: `/api/v1/companies/`

#### 1. Create a company

- `POST /api/v1/companies/`
- Headers: `Authorization: Bearer <access>`
- Body:
  ```json
  { "name": "ACME" }
  ```
- Behavior:
  - Creates a `Company` row.
  - Creates a `CompanyMembership` with `role = "owner"` for the authenticated user.
- Response:
  ```json
  { "id": "<company_uuid>", "name": "ACME" }
  ```

#### 2. Create a staff sub-account

- `POST /api/v1/companies/staff/`
- Headers:
  - `Authorization: Bearer <access>`
  - `X-Company-ID: <company_uuid>`  ← **explicit active company**
- Body:
  ```json
  {
    "email": "staff@example.com",
    "password": "StaffPass123",
    "role": "staff"
  }
  ```
- Behavior:
  - Uses `X-Company-ID` + `CompanyMembership` to verify:
    - The caller belongs to that company.
    - The caller has role `owner` or `admin`.
  - Creates (or reuses) a global `User` with that email.
  - Creates/updates a `CompanyMembership` for that user & company with the given role.
- Response:
  ```json
  {
    "membership_id": "<uuid>",
    "user_email": "staff@example.com",
    "company_id": "<company_uuid>",
    "role": "staff"
  }
  ```

---

## Typical workflow (end-to-end)

1. **Person registers**
   - `POST /api/v1/auth/register/` with email & password.

2. **Person logs in**
   - `POST /api/v1/auth/login/` → get `access` & `refresh`.

3. **Person creates a company**
   - `POST /api/v1/companies/` with `Authorization: Bearer <access>` and `{ "name": "ACME" }`.
   - Becomes `owner` of `ACME`.

4. **Person views their memberships**
   - `GET /api/v1/auth/me/` with `Authorization: Bearer <access>`.
   - Client sees list of companies + roles (e.g. `ACME` as `owner`).

5. **Owner creates staff accounts for a company**
   - Choose an active company from `me` response (e.g. `company_id = "<ACME_UUID>"`).
   - `POST /api/v1/companies/staff/` with:
     - `Authorization: Bearer <access>`
     - `X-Company-ID: <ACME_UUID>`
     - Body: staff email/password/role.

6. **Staff logs in normally**
   - Staff uses `POST /api/v1/auth/login/` with their email & password.
   - On the frontend, you decide which company context to operate in, using `X-Company-ID` for company-scoped endpoints.

7. **User switches between companies**
   - Call `GET /api/v1/auth/me/` to see all memberships.
   - For each company-scoped request, send the desired `X-Company-ID` header.

---

## Testing

Run all tests:

```bash
uv run pytest
```

Current tests:

- `accounts/tests/test_auth_api.py`
  - Full auth flow: register → login → refresh → logout → forgot/reset.
- `companies/tests/test_companies_api.py`
  - Create company and owner membership.
  - Create staff in that company via `X-Company-ID`.
  - Staff login verification.
   