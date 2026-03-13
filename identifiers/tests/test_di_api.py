import pytest
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from identifiers.models import DI


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@example.com', password='Pass1234')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email='other@example.com', password='Pass1234')


@pytest.fixture
def di_record(user):
    return DI.objects.create(owner=user, value='(01)01234567890123')


@pytest.fixture
def other_di(other_user):
    return DI.objects.create(owner=other_user, value='(01)98765432109876')


@pytest.mark.django_db
class TestDICRUD:
    def test_list_returns_only_own_records(self, api_client, user, di_record, other_di):
        api_client.force_authenticate(user=user)
        r = api_client.get('/api/v1/dis/')
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['value'] == '(01)01234567890123'

    def test_list_pagination(self, api_client, user):
        for i in range(25):
            DI.objects.create(owner=user, value=f'(01)0000000000000{i:02d}')
        api_client.force_authenticate(user=user)
        r = api_client.get('/api/v1/dis/')
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert 'results' in data
        assert len(data['results']) == 20
        assert 'next' in data
        assert data['next'] is not None

    def test_list_requires_auth(self, api_client):
        r = api_client.get('/api/v1/dis/')
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create(self, api_client, user):
        api_client.force_authenticate(user=user)
        r = api_client.post(
            '/api/v1/dis/',
            {'value': '(01)01234567890123'},
            format='json',
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()
        assert data['value'] == '(01)01234567890123'
        assert 'id' in data
        assert DI.objects.filter(owner=user).count() == 1

    def test_create_requires_auth(self, api_client):
        r = api_client.post(
            '/api/v1/dis/',
            {'value': '(01)01234567890123'},
            format='json',
        )
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_own(self, api_client, user, di_record):
        api_client.force_authenticate(user=user)
        r = api_client.get(f'/api/v1/dis/{di_record.id}/')
        assert r.status_code == status.HTTP_200_OK
        assert r.json()['value'] == '(01)01234567890123'

    def test_retrieve_other_forbidden(self, api_client, user, other_di):
        api_client.force_authenticate(user=user)
        r = api_client.get(f'/api/v1/dis/{other_di.id}/')
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_update_own(self, api_client, user, di_record):
        api_client.force_authenticate(user=user)
        r = api_client.patch(
            f'/api/v1/dis/{di_record.id}/',
            {'value': '(01)99999999999999'},
            format='json',
        )
        assert r.status_code == status.HTTP_200_OK
        di_record.refresh_from_db()
        assert di_record.value == '(01)99999999999999'

    def test_update_other_forbidden(self, api_client, user, other_di):
        api_client.force_authenticate(user=user)
        r = api_client.patch(
            f'/api/v1/dis/{other_di.id}/',
            {'value': '(01)99999999999999'},
            format='json',
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_own(self, api_client, user, di_record):
        api_client.force_authenticate(user=user)
        r = api_client.delete(f'/api/v1/dis/{di_record.id}/')
        assert r.status_code == status.HTTP_204_NO_CONTENT
        assert not DI.objects.filter(id=di_record.id).exists()

    def test_delete_other_forbidden(self, api_client, user, other_di):
        api_client.force_authenticate(user=user)
        r = api_client.delete(f'/api/v1/dis/{other_di.id}/')
        assert r.status_code == status.HTTP_404_NOT_FOUND
        assert DI.objects.filter(id=other_di.id).exists()
