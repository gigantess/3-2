import os
import pytest

# Ensure automated tests run in isolated Mock DB mode
os.environ["USE_MOCK_DB"] = "true"

from backend.database import reset_db_client_for_testing
from backend.services.data_service import DataService

@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db_client_for_testing()
    # Seed minimal test data for testing if empty
    ds = DataService()
    items, count = ds.get_items(limit=1)
    if count == 0:
        from backend.scripts.seed_data import seed_database
        seed_database(limit=20)
