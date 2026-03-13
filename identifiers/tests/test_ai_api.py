import pytest
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from identifiers.models import AI


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email='user@example.com', password='Pass1234')


@pytest.fixture
def ai_record(db):
    return AI.objects.create(
        code='01',
        description='GTIN',
        format_spec='N14',
    )


@pytest.fixture
def ai_records(db):
    for i, (code, desc) in enumerate([('01', 'GTIN'), ('17', 'Expiry'), ('10', 'Batch')], 1):
        AI.objects.create(code=code, description=desc, format_spec=f'N{i}')
    return list(AI.objects.all())


@pytest.mark.django_db
class TestAICRUD:
    def test_list_all_users_can_view(self, api_client, user, ai_records):
        api_client.force_authenticate(user=user)
        r = api_client.get('/api/v1/ais/')
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert 'results' in data
        assert len(data['results']) == 3

    def test_list_pagination(self, api_client, user, db):
        for i in range(25):
            AI.objects.create(code=f'{i:02d}', description=f'AI {i}')
        api_client.force_authenticate(user=user)
        r = api_client.get('/api/v1/ais/')
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert 'results' in data
        assert len(data['results']) == 20
        assert 'next' in data
        assert data['next'] is not None

    def test_list_requires_auth(self, api_client, ai_record):
        r = api_client.get('/api/v1/ais/')
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create(self, api_client, user):
        api_client.force_authenticate(user=user)
        r = api_client.post(
            '/api/v1/ais/',
            {'code': '21', 'description': 'Serial', 'format_spec': 'an..20'},
            format='json',
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()
        assert data['code'] == '21'
        assert data['description'] == 'Serial'
        assert AI.objects.filter(code='21').exists()

    def test_retrieve(self, api_client, user, ai_record):
        api_client.force_authenticate(user=user)
        r = api_client.get(f'/api/v1/ais/{ai_record.id}/')
        assert r.status_code == status.HTTP_200_OK
        assert r.json()['code'] == '01'

    def test_update(self, api_client, user, ai_record):
        api_client.force_authenticate(user=user)
        r = api_client.patch(
            f'/api/v1/ais/{ai_record.id}/',
            {'description': 'Global Trade Item Number'},
            format='json',
        )
        assert r.status_code == status.HTTP_200_OK
        ai_record.refresh_from_db()
        assert ai_record.description == 'Global Trade Item Number'

    def test_delete(self, api_client, user, ai_record):
        api_client.force_authenticate(user=user)
        r = api_client.delete(f'/api/v1/ais/{ai_record.id}/')
        assert r.status_code == status.HTTP_204_NO_CONTENT
        assert not AI.objects.filter(id=ai_record.id).exists()
