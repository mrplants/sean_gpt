import pytest
import time

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import docker

from sean_gpt.main import app
from sean_gpt.util.describe import describe
from sean_gpt.config import settings

def wait_for_db_to_be_ready(host, port, user, password, max_attempts=10, delay=1):
    """Waits for the database to be ready to accept connections."""
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try to connect to the database
            with psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port):
                return True  # Successfully connected
        except psycopg2.OperationalError:
            # Connection failed
            time.sleep(delay)
            attempts += 1
    raise RuntimeError("Database did not become ready in time")

@describe(""" Test fixture to start a local postgres database. """)
@pytest.fixture
def local_postgres(request):
    docker_client = docker.from_env()
    container = docker_client.containers.run(
        "postgres:latest",
        detach=True,
        ports={"5432/tcp": 5432},
        environment={
            "POSTGRES_USER": "admin_user",
            "POSTGRES_PASSWORD": "admin_password",
        },
    )
    # print(f'postgres container details: {container.name}')
    # for container_i in docker_client.containers.list():
    #     print(container_i.name)
    #     print(container_i.status)

    # Wait for the container to be ready
    while True:
        container.reload()
        if container.status == "running":
            break
        time.sleep(0.5)

    # Wait for the database to be ready
    if not wait_for_db_to_be_ready('localhost', 5432, "admin_user", "admin_password"):
        raise RuntimeError("Unable to connect to the database")

    # Connect to the PostgreSQL server
    conn = psycopg2.connect(dbname='postgres', user="admin_user", password="admin_password", host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Cursor to perform database operations
    cur = conn.cursor()

    # Create a new user
    cur.execute(f"CREATE USER {settings.api_db_user} WITH ENCRYPTED PASSWORD %s;", (settings.api_db_password,))

    # Create a new database
    cur.execute(f"CREATE DATABASE {settings.api_db_name};")

    conn.close()
    conn = psycopg2.connect(dbname=settings.api_db_name, user="admin_user", password="admin_password", host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Grant the user the ability to create tables in the public schema
    cur.execute(f"GRANT CREATE ON SCHEMA public TO {settings.api_db_user};")

    cur.execute("SELECT datname FROM pg_database;")
    databases = cur.fetchall()
    for db in databases:
        print(f'database: {db[0]}')

    cur.execute("SELECT rolname FROM pg_roles;")
    users = cur.fetchall()
    for user in users:
        print(f'user: {user[0]}')

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = cur.fetchall()
    for table in tables:
        print(f'table: {table[0]}')

    # Close communication with the database
    cur.close()
    conn.close()
    print('postgres container details')
    print(container.id)
    print(container.name)
    print(container.status)
    # print(container.logs().decode('utf-8'))
    # print(container.attrs)
    yield
    container.stop()
    # Only remove the container if the test passed
    # Teardown code here
    if request.session.testsfailed:
        print("Not removing container because test failed.")
    else:
        container.remove()
        print("Removing container because test passed.")

@describe(""" Test fixture to provide a test client for the application. """)
@pytest.fixture
def client(local_postgres) -> TestClient:
    with TestClient(app) as client:
        yield client