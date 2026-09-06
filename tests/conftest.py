from pathlib import Path
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def processed_dir(project_root: Path) -> Path:
    """Returns the processed data directory path."""
    return project_root / "data" / "processed"


@pytest.fixture
def sample_food_services_df() -> pd.DataFrame:
    """Provides sample DataFrame for food services decomposition testing."""
    return pd.DataFrame(
        {
            "Indicator": [
                "Food Services and Drinking Places - BC - Total",
                "Canada - Drinking Places",
                "Food Services - BC",
            ],
            "Value": [100.0, 50.0, 75.0],
        }
    )


@pytest.fixture
def sample_tourism_sector_df() -> pd.DataFrame:
    """Provides sample DataFrame for tourism sector indicator decomposition testing."""
    return pd.DataFrame(
        {
            "Indicator": [
                "Employment in key tourism industries (000s) - Accommodation",
                "Hotel Industry - Occupancy Rate",
                "Hotel Industry - Average Room Rate",
                "Consumer Price Index - Restaurant meals (2017=100)",
            ],
            "Value": [12.5, 68.4, 185.50, 112.3],
        }
    )


@pytest.fixture
def sample_transportation_df() -> pd.DataFrame:
    """Provides sample DataFrame for transportation indicator decomposition testing."""
    return pd.DataFrame(
        {
            "Indicator": [
                "Air Passenger Traffic - Vancouver - Enplaned & Deplaned",
                "Air Passenger Traffic - Victoria - Total",
                "Other Transportation - BC Ferries - Passengers",
            ],
            "Value": [150000, 30000, 450000],
        }
    )


@pytest.fixture
def sample_traveller_entries_df() -> pd.DataFrame:
    """Provides sample DataFrame for traveller entries indicator decomposition testing."""
    return pd.DataFrame(
        {
            "Indicator": [
                "USA - Same Day Automobile",
                "Overseas - Europe Direct",
                "Total Traveller Entries",
            ],
            "Value": [1200, 450, 5000],
        }
    )