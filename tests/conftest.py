"""
pytest fixtures for oais module tests
"""
import os
import sys
import sqlite3
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Return project root path"""
    return PROJECT_ROOT


@pytest.fixture(scope="function")
def temp_db():
    """Create temporary SQLite database for testing"""
    import gc

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    # Create test tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # common_user table
    cursor.execute("""
        CREATE TABLE common_user (
            no INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT DEFAULT '',
            name TEXT DEFAULT '',
            company TEXT DEFAULT '',
            team TEXT DEFAULT '',
            position TEXT DEFAULT '',
            permission TEXT DEFAULT 'employee',
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0
        )
    """)

    # districts table
    cursor.execute("""
        CREATE TABLE districts (
            id INTEGER PRIMARY KEY,
            sido VARCHAR(50) NOT NULL,
            sigungu VARCHAR(50) NOT NULL,
            code VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup - force garbage collection to close any lingering connections
    gc.collect()
    try:
        os.unlink(db_path)
    except PermissionError:
        # Windows may still hold the file, ignore for now
        pass


@pytest.fixture
def mock_config(temp_db, monkeypatch):
    """Mock config with temp database"""
    class MockConfig:
        DB_PATH = temp_db
        DEBUG = True

    # Mock the config
    monkeypatch.setattr("oais.config_helper.config.Config", MockConfig)
    return MockConfig


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "id": "testuser",
        "password": "testpass123",
        "email": "test@example.com",
        "name": "Test User",
        "company": "Test Company",
        "team": "Dev Team",
        "position": "Developer",
        "permission": "employee",
        "is_admin": 0,
        "is_active": 1
    }


@pytest.fixture
def admin_user_data():
    """Admin user data for testing"""
    return {
        "id": "admin",
        "password": "adminpass123",
        "email": "admin@example.com",
        "name": "Admin User",
        "company": "Test Company",
        "team": "Admin Team",
        "position": "Manager",
        "permission": "admin",
        "is_admin": 1,
        "is_active": 1
    }
