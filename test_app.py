import pytest
import json
from app import app, db, seed_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        seed_data()
        with app.test_client() as client:
            yield client

# ── Tests Health ──────────────────────────────────────────────
def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.get_json()['status'] == 'healthy'

def test_info(client):
    res = client.get('/api/info')
    assert res.status_code == 200
    assert res.get_json()['version'] == '2.0.0'

# ── Tests Produits ────────────────────────────────────────────
def test_get_products(client):
    res = client.get('/api/products')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] == True
    assert data['total'] > 0

def test_get_product_by_id(client):
    res = client.get('/api/products/1')
    assert res.status_code == 200
    assert res.get_json()['product']['id'] == 1

def test_create_product(client):
    payload = {
        "name": "Souris Gaming",
        "price": 499.99,
        "stock": 10,
        "category": "Informatique",
        "description": "Souris 12000 DPI RGB"
    }
    res = client.post('/api/products',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 201
    assert res.get_json()['product']['name'] == 'Souris Gaming'

def test_create_product_missing_fields(client):
    res = client.post('/api/products',
                      data=json.dumps({"name": "Test"}),
                      content_type='application/json')
    assert res.status_code == 400

def test_update_product(client):
    payload = {"price": 9999.99, "stock": 100}
    res = client.put('/api/products/1',
                     data=json.dumps(payload),
                     content_type='application/json')
    assert res.status_code == 200
    assert res.get_json()['product']['price'] == 9999.99

def test_delete_product(client):
    res = client.delete('/api/products/1')
    assert res.status_code == 200
    assert res.get_json()['success'] == True

# ── Tests Commandes ───────────────────────────────────────────
def test_create_order(client):
    payload = {
        "customer": "Amina Alaoui",
        "email": "amina@gmail.com",
        "items": [{"product_id": 1, "quantity": 1}]
    }
    res = client.post('/api/orders',
                      data=json.dumps(payload),
                      content_type='application/json')
    assert res.status_code == 201
    assert res.get_json()['order']['status'] == 'confirmed'

def test_get_orders(client):
    res = client.get('/api/orders')
    assert res.status_code == 200
    assert res.get_json()['success'] == True

# ── Tests Stats ───────────────────────────────────────────────
def test_stats(client):
    res = client.get('/api/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'total_products' in data
    assert 'total_orders' in data
    assert 'total_revenue' in data
