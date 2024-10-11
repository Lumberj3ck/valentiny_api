# from fastapi.testclient import TestClient
from ..main import app
from ..app_data.database import Base
from .test_user_routes import login_and_get_user
from ..dependencies import get_db
from .database_initialise import TestingSessionLocal, engine
from .utils import create_user, create_domain
from ..app_data import crud
from .test_user_routes import client

import pytest


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()

# client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db


def test_check_subdomain_availability(db_session):
    resp = create_user("test_user", "test_user@gmail.com")
    subdomain = "test"
    domain_name = "test.com"
    create_domain(domain_name, db_session)
    jwt_token = resp.json().get("access_token", "")
    response = client.post(
        "/user/check_subdomain_availability/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"name": subdomain, "domain_name": domain_name},
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {"is_available": True, "message": "This subdomain is available"}


# "You already own this subdomain"

def test_check_subdomain_availability_already_owned(db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    subdomain = "test"
    domain_name = "test.com"
    resp = create_user("test_user", "test_user@gmail.com")

    user = login_and_get_user("test_user", db_session)
    jwt_token = resp.json().get("access_token", "")
    create_domain(domain_name, db_session)

    crud.create_subdomain(db_session, user.id, subdomain, domain_name)

    response = client.post(
        "/user/check_subdomain_availability/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"name": subdomain, "domain_name": domain_name},
    )

    assert response.status_code == 200
    assert response.json() == {"is_available": False, "message": "You already own this subdomain"}

def test_check_subdomain_availability_domain_does_not_exist(db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    resp = create_user("test_user", "test_user@gmail.com")
    jwt_token = resp.json().get("access_token", "")
    
    subdomain = "test"
    non_existent_domain = "nonexistent.com"
    
    response = client.post(
        "/user/check_subdomain_availability/",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"name": subdomain, "domain_name": non_existent_domain},
    )
    
    assert response.status_code == 400
    assert response.json() == {"detail": "The specified domain does not exist"}

def test_this_subdomain_is_not_available(db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    subdomain = "test"
    domain_name = "test.com"
    
    # Create two users
    resp1 = create_user("user1", "user1@gmail.com")
    resp2 = create_user("user2", "user2@gmail.com")
    
    user1 = login_and_get_user("user1", db_session)
    user2 = login_and_get_user("user2", db_session)
    
    jwt_token1 = resp1.json().get("access_token", "")
    jwt_token2 = resp2.json().get("access_token", "")
    
    create_domain(domain_name, db_session)
    
    # User1 creates the subdomain
    crud.create_subdomain(db_session, user1.id, subdomain, domain_name)
    
    # User2 tries to check availability of the same subdomain
    response = client.post(
        "/user/check_subdomain_availability/",
        headers={"Authorization": f"Bearer {jwt_token2}"},
        json={"name": subdomain, "domain_name": domain_name},
    )
    
    assert response.status_code == 200
    assert response.json() == {"is_available": False, "message": "This subdomain is not available"}

def test_get_user_domains(db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a user
    resp = create_user("test_user", "test_user@gmail.com")
    jwt_token = resp.json().get("access_token", "")
    user = login_and_get_user("test_user", db_session)
    
    # Create domains
    domain1 = "test1.com"
    domain2 = "test2.com"
    create_domain(domain1, db_session)
    create_domain(domain2, db_session)
    
    # Create subdomains for the user
    crud.create_subdomain(db_session, user.id, "subdomain1", domain1)
    crud.create_subdomain(db_session, user.id, "subdomain2", domain2)
    
    # Make the request
    response = client.get(
        "/user/domains/",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    
    assert response.status_code == 200
    domains = response.json()
    assert len(domains) == 2
    assert {"name": "subdomain1", "domain_name": domain1} in domains
    assert {"name": "subdomain2", "domain_name": domain2} in domains

def test_get_user_domains_empty(db_session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a user
    resp = create_user("test_user_empty", "test_user_empty@gmail.com")
    jwt_token = resp.json().get("access_token", "")
    
    # Make the request without creating any subdomains
    response = client.get(
        "/user/domains/",
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    
    assert response.status_code == 200
    domains = response.json()
    assert len(domains) == 0

