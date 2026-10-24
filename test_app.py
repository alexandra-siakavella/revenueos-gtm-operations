from fastapi.testclient import TestClient
from app.main import app, init_db

client = TestClient(app)


def setup_module():
    init_db()


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_accounts_include_expected_demo_data():
    response = client.get('/api/accounts')
    assert response.status_code == 200
    data = response.json()
    assert data['count'] >= 5
    assert any(a['name'] == 'Brightpath Health' for a in data['accounts'])


def test_reconcile_finds_owner_and_arr_discrepancies():
    response = client.get('/api/reconcile')
    assert response.status_code == 200
    issues = response.json()['issues']
    assert any(i['field'] == 'Owner' for i in issues)
    assert any(i['field'] == 'ARR' for i in issues)


def test_extract_demo_fields():
    response = client.post('/api/extract', json={'notes': 'Proposal is 125000 ARR. Owner is Ava Patel. Stage is Contracting.'})
    assert response.status_code == 200
    data = response.json()['extracted']
    assert data['arr'] == 125000
    assert data['owner'] == 'Ava Patel'
    assert data['stage'] == 'Contracting'


def test_status_update_rejects_invalid_status():
    response = client.patch('/api/accounts/ACC-1001/status', json={'status': 'Definitely done'})
    assert response.status_code == 422
