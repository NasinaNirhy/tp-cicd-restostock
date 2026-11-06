from app import app
import pytest


@pytest.fixture
def client():
  app.config["TESTING"] = True
  with app.test_client() as client:
    yield client


def test_home_page(client):
  """Vérifie que le dashboard/accueil s'affiche bien"""
  response = client.get("/")
  assert response.status_code == 200
  assert b"RESTO MANAGER" in response.data


def test_health(client):
  """Route de contrôle obligatoire du TP"""
  response = client.get("/health")
  assert response.status_code == 200
  assert response.get_json() == {"status": "healthy"}


def test_version(client):
  """Route de version obligatoire du TP"""
  response = client.get("/version")
  assert response.status_code == 200
  assert "version" in response.get_json()


def test_add_product_and_movement(client):
  """Vérifie l'ajout d'un produit et l'enregistrement des mouvements"""
  response = client.post(
      "/add_product",
      data={
          "name": "Fromage",
          "category": "Produits laitiers",
          "quantity": 5,
          "unit": "kg",
          "price": 6.0,
          "min_threshold": 2,
          "expiry_date": "2026-07-01",
      },
      follow_redirects=True,
  )
  assert response.status_code == 200
  assert b"Fromage" in response.data


def test_backup(client):
  """Vérifie la fonctionnalité de backup JSON"""
  response = client.get("/backup")
  assert response.status_code == 200
  assert response.headers["Content-Disposition"].startswith("attachment")

def test_404_not_found(client):
    """Vérifie qu'une URL inconnue répond bien avec le statut 404"""
    response = client.get("/route-qui-n-existe-pas-12345")
    assert response.status_code == 404
