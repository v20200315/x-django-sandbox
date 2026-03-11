import pytest
from rest_framework.test import APIClient

from accounts.models import CompanyMembership, CompanyRole, User
from companies.models import Company


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
        '/api/v1/companies/',
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
        '/api/v1/companies/staff/',
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
        '/api/v1/companies/staff/',
        {'email': 'someone@test.com', 'password': 'Pass12345', 'role': 'staff'},
        format='json',
        HTTP_X_COMPANY_ID='00000000-0000-0000-0000-000000000000',
    )
    assert r.status_code in (400, 403)
