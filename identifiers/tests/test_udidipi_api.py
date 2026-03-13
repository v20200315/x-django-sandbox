import pytest
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from identifiers.models import AI, DI, UDIDIPI


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
def di1(user):
    return DI.objects.create(owner=user, value='(01)01234567890123')


@pytest.fixture
def di2(user):
    return DI.objects.create(owner=user, value='(8017)12345678901234')


@pytest.fixture
def ai17(db):
    return AI.objects.create(code='17', description='Expiry', format_spec='N6')


@pytest.fixture
def ai10(db):
    return AI.objects.create(code='10', description='Batch', format_spec='an..20')


@pytest.fixture
def other_di(other_user):
    return DI.objects.create(owner=other_user, value='(01)99999999999999')


@pytest.mark.django_db
class TestUDIDIPICRUD:
    def test_create_generates_code(self, api_client, user, di1, ai17, ai10):
        api_client.force_authenticate(user=user)
        r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [
                    {'ai_id': str(ai17.id), 'value': '250101'},
                    {'ai_id': str(ai10.id), 'value': 'BATCH001'},
                ],
            },
            format='json',
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()
        assert 'id' in data
        assert 'generated_code' in data
        # GS1 format: (01)01234567890123(17)250101(10)BATCH001
        assert '(01)01234567890123' in data['generated_code']
        assert '(17)250101' in data['generated_code']
        assert '(10)BATCH001' in data['generated_code']
        assert len(data['dis']) == 1
        assert len(data['ai_values']) == 2

    def test_create_multiple_dis(self, api_client, user, di1, di2, ai17):
        api_client.force_authenticate(user=user)
        r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id), str(di2.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        assert r.status_code == status.HTTP_201_CREATED
        data = r.json()
        assert '(01)01234567890123' in data['generated_code']
        assert '(8017)12345678901234' in data['generated_code']
        assert '(17)250101' in data['generated_code']

    def test_create_rejects_other_users_di(self, api_client, user, other_di, ai17):
        api_client.force_authenticate(user=user)
        r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(other_di.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_returns_only_own(self, api_client, user, other_user, di1, ai17):
        api_client.force_authenticate(user=user)
        r1 = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        assert r1.status_code == 201
        api_client.force_authenticate(user=other_user)
        r2 = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [
                    str(DI.objects.create(owner=other_user, value='(01)111').id)
                ],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '251231'}],
            },
            format='json',
        )
        assert r2.status_code == 201
        api_client.force_authenticate(user=user)
        r = api_client.get('/api/v1/udidipi/')
        assert r.status_code == 200
        assert len(r.json()['results']) == 1

    def test_retrieve(self, api_client, user, di1, ai17):
        api_client.force_authenticate(user=user)
        create_r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        udid = create_r.json()['id']
        r = api_client.get(f'/api/v1/udidipi/{udid}/')
        assert r.status_code == 200
        assert r.json()['generated_code']

    def test_update_regenerates_code(self, api_client, user, di1, ai17, ai10):
        api_client.force_authenticate(user=user)
        create_r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        udid = create_r.json()['id']
        r = api_client.put(
            f'/api/v1/udidipi/{udid}/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [
                    {'ai_id': str(ai17.id), 'value': '251231'},
                    {'ai_id': str(ai10.id), 'value': 'LOT2'},
                ],
            },
            format='json',
        )
        assert r.status_code == 200
        assert '(17)251231' in r.json()['generated_code']
        assert '(10)LOT2' in r.json()['generated_code']

    def test_delete(self, api_client, user, di1, ai17):
        api_client.force_authenticate(user=user)
        create_r = api_client.post(
            '/api/v1/udidipi/',
            {
                'di_ids': [str(di1.id)],
                'ai_values': [{'ai_id': str(ai17.id), 'value': '250101'}],
            },
            format='json',
        )
        udid = create_r.json()['id']
        r = api_client.delete(f'/api/v1/udidipi/{udid}/')
        assert r.status_code == status.HTTP_204_NO_CONTENT
        assert not UDIDIPI.objects.filter(id=udid).exists()
