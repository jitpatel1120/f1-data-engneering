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
    "driver_id": "test_refresh_driver",
    "permanent_number": None,
    "code": "TST",
    "given_name": "Test",
    "family_name": "Driver",
    "date_of_birth": "2000-01-01",
    "nationality": "British"
}

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"]
) as conn:

    with conn.cursor() as cursor:

        with patch.object(load, "transform_drivers", return_value=[test_driver]):
            count = load.load_drivers(cursor)

        assert count == 1

        updated_driver = {
            **test_driver,
            "nationality": "Dutch"
        }

        with patch.object(load, "transform_drivers", return_value=[updated_driver]):
            count = load.load_drivers(cursor)

        assert count == 1

        cursor.execute(
            """
            SELECT nationality
            FROM f1.drivers
            WHERE driver_id = %s
            """,
            ("test_refresh_driver",)
        )

        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "Dutch"

        print("TEST 1 PASSED: Python loader updated the existing driver")
        print("TEST 2 PASSED: No duplicate driver was inserted")

    # Explicit rollback before leaving the connection context
    conn.rollback()

    print("TEST 3 PASSED: Test transaction rolled back")