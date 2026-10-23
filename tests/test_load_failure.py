import os
import sys
from unittest.mock import patch

import psycopg
from dotenv import load_dotenv

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import load

load_dotenv()

test_driver = {
    "driver_id": "test_rollback_driver",
    "permanent_number": None,
    "code": "TST",
    "given_name": "Rollback",
    "family_name": "Test",
    "date_of_birth": "2000-01-01",
    "nationality": "British"
}

# Simulate a failure during the second table load
try:
    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    ) as conn:

        with conn.cursor() as cursor:

            with patch.object(load, "transform_drivers", return_value=[test_driver]):
                load.load_drivers(cursor)

            print("Driver loaded successfully")

            with patch.object(
                load,
                "transform_constructors",
                side_effect=RuntimeError("Simulated transformation failure")
            ):
                load.load_constructors(cursor)

except RuntimeError as e:
    assert str(e) == "Simulated transformation failure"
    print("TEST 1 PASSED: Failure propagated correctly")

# Verify the first table's changes were rolled back
with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"]
) as conn:

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM f1.drivers
            WHERE driver_id = %s
            """,
            ("test_rollback_driver",)
        )

        count = cursor.fetchone()[0]

        assert count == 0

        print("TEST 2 PASSED: Driver insertion was rolled back")