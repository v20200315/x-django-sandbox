import pytest
from django.core.signing import TimestampSigner
from rest_framework.test import APIClient

from accounts.models import User


@pytest.mark.django_db
def test_register_login_refresh_logout_reset_flow():
    client = APIClient()

    # register
    r = client.post(
        '/api/v1/auth/register/',
        {'email': 'a@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    assert r.status_code == 201
    assert 'access' in r.data and 'refresh' in r.data

    # login
    r = client.post(
        '/api/v1/auth/login/',
        {'email': 'a@test.com', 'password': 'StrongPass123'},
        format='json',
    )
    assert r.status_code == 200
    access = r.data['access']
    refresh = r.data['refresh']

    # refresh
    r = client.post('/api/v1/auth/token/refresh/', {'refresh': refresh}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data

    # logout (blacklist refresh)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r = client.post('/api/v1/auth/logout/', {'refresh': refresh}, format='json')
    assert r.status_code == 205

    # refresh should now fail if blacklist is enabled
    client.credentials()  # clear auth header
    r = client.post('/api/v1/auth/token/refresh/', {'refresh': refresh}, format='json')
    assert r.status_code in (401, 400)

    # forgot password always returns 200
    r = client.post(
        '/api/v1/auth/forgot-password/', {'email': 'a@test.com'}, format='json'
    )
    assert r.status_code == 200

    # reset password using a signed token (same method as your view)
    user = User.objects.get(email='a@test.com')
    token = TimestampSigner().sign(user.pk)
    r = client.post(
        '/api/v1/auth/reset-password/',
        {'token': token, 'new_password': 'NewStrongPass123'},
        format='json',
    )
    assert r.status_code == 200

    # login with new password works
    r = client.post(
        '/api/v1/auth/login/',
        {'email': 'a@test.com', 'password': 'NewStrongPass123'},
        format='json',
    )
    assert r.status_code == 200
