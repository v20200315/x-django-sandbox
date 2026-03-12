import pytest
from rest_framework.test import APIClient

from accounts.models import Company, CompanyMembership, CompanyRole, User


@pytest.mark.django_db
def test_create_company_and_staff_flow():
    client = APIClient()

    # 1) Register person (no company yet)
    r = client.post(
        '/api/v1/auth/register/',
        {'email': 'owner@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    assert r.status_code == 201
    owner_id = r.data['user']['id']

    # 2) Login
    r = client.post(
        '/api/v1/auth/login/',
        {'email': 'owner@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    assert r.status_code == 200
    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    # 3) Create company (owner)
    r = client.post(
        '/api/v1/auth/companies/',
        {'name': 'ACME'},
        format='json',
    )
    assert r.status_code == 201
    company_id = r.data['id']

    # DB checks: company + owner membership
    company = Company.objects.get(id=company_id)
    owner = User.objects.get(id=owner_id)
    membership = CompanyMembership.objects.get(user=owner, company=company)
    assert membership.role == CompanyRole.OWNER

    # 4) Create staff in this company
    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'staff@test.com', 'password': 'StaffPass123', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID=company_id,
    )
    assert r.status_code == 201
    staff_email = r.data['user_email']

    staff_user = User.objects.get(email=staff_email)
    staff_membership = CompanyMembership.objects.get(user=staff_user, company=company)
    assert staff_membership.role == CompanyRole.STAFF

    # 5) Staff can log in with the password (since newly created)
    client.credentials()  # clear header
    r = client.post(
        '/api/v1/auth/login/',
        {'email': 'staff@test.com', 'password': 'StaffPass123'},
        format='json',
    )
    assert r.status_code == 200


@pytest.mark.django_db
def test_staff_create_requires_membership_and_owner_role():
    client = APIClient()

    # Register + login as user WITHOUT company
    r = client.post(
        '/api/v1/auth/register/',
        {'email': 'user@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    assert r.status_code == 201

    r = client.post(
        '/api/v1/auth/login/',
        {'email': 'user@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    # Try to create staff with some random company id → should 403 or 400
    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'someone@test.com', 'password': 'Pass12345', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID='00000000-0000-0000-0000-000000000000',
    )
    assert r.status_code in (400, 403)


def _register_and_login(client, email, password):
    r = client.post(
        '/api/v1/auth/register/',
        {'email': email, 'password': password},
        format='json',
    )
    assert r.status_code == 201
    r = client.post(
        '/api/v1/auth/login/',
        {'email': email, 'password': password},
        format='json',
    )
    assert r.status_code == 200
    return r.data['access']


def _create_company(client, name):
    r = client.post('/api/v1/auth/companies/', {'name': name}, format='json')
    assert r.status_code == 201
    return r.data['id']


@pytest.mark.django_db
def test_create_company_requires_auth():
    client = APIClient()
    r = client.post('/api/v1/auth/companies/', {'name': 'ACME'}, format='json')
    assert r.status_code == 401


@pytest.mark.django_db
def test_create_company_rejects_duplicate_name_case_insensitive():
    client = APIClient()
    access = _register_and_login(client, 'owner2@test.com', 'StrongPass123')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    _create_company(client, 'AcMe')

    r = client.post('/api/v1/auth/companies/', {'name': 'acme'}, format='json')
    assert r.status_code == 400
    assert 'name' in r.data


@pytest.mark.django_db
def test_staff_create_requires_x_company_id_header():
    client = APIClient()
    access = _register_and_login(client, 'owner3@test.com', 'StrongPass123')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    _create_company(client, 'HeaderCo')

    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'staff1@test.com', 'password': 'StaffPass123', 'role': 'staff'},
        format='json',
    )
    assert r.status_code == 400
    assert 'X-Company-ID' in r.data


@pytest.mark.django_db
def test_staff_create_rejects_invalid_company_id_header():
    client = APIClient()
    access = _register_and_login(client, 'owner4@test.com', 'StrongPass123')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    _create_company(client, 'InvalidHeaderCo')

    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'staff2@test.com', 'password': 'StaffPass123', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID='not-a-uuid',
    )
    assert r.status_code == 400
    assert 'X-Company-ID' in r.data


@pytest.mark.django_db
def test_staff_role_cannot_create_other_staff():
    client = APIClient()
    owner_access = _register_and_login(client, 'owner5@test.com', 'StrongPass123')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {owner_access}')
    company_id = _create_company(client, 'RoleGateCo')

    # Owner creates a staff user
    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'staff3@test.com', 'password': 'StaffPass123', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID=company_id,
    )
    assert r.status_code == 201

    # Staff logs in and attempts to create another staff user
    client.credentials()
    staff_access = _register_and_login(client, 'staff4@test.com', 'StaffPass123!')
    # Ensure this user is in the company as staff
    staff_user = User.objects.get(email='staff4@test.com')
    company = Company.objects.get(id=company_id)
    CompanyMembership.objects.create(
        user=staff_user,
        company=company,
        role=CompanyRole.STAFF,
    )

    client.credentials(HTTP_AUTHORIZATION=f'Bearer {staff_access}')
    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': 'staff5@test.com', 'password': 'StaffPass123', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID=company_id,
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_staff_create_existing_user_adds_membership_and_updates_role():
    client = APIClient()
    owner_access = _register_and_login(client, 'owner6@test.com', 'StrongPass123')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {owner_access}')
    company_id = _create_company(client, 'MembershipCo')

    # Existing global user in system (not yet member of this company)
    existing = User.objects.create_user('existing@test.com', 'ExistingPass123')

    r = client.post(
        '/api/v1/auth/companies/staff/',
        {'email': existing.email, 'password': 'IgnoredPass123', 'role': 'admin'},
        format='json',
        HTTP_X_COMPANY_ID=company_id,
    )
    assert r.status_code == 201
    assert r.data['role'] == CompanyRole.ADMIN

    membership = CompanyMembership.objects.get(user=existing, company_id=company_id)
    assert membership.role == CompanyRole.ADMIN
