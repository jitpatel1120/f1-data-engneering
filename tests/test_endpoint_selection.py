import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import load

mock_conn = MagicMock()
mock_cursor = MagicMock()

mock_conn.__enter__.return_value = mock_conn
mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

with (
    patch.object(sys, "argv", ["load.py", "--endpoints", "drivers"]),
    patch.object(load.psycopg, "connect", return_value=mock_conn),
    patch.object(load, "load_drivers", return_value=881) as drivers,
    patch.object(load, "load_constructors") as constructors,
    patch.object(load, "load_races") as races
):
    load.main()

    drivers.assert_called_once_with(mock_cursor)
    constructors.assert_not_called()
    races.assert_not_called()

    print("TEST 1 PASSED: Drivers loader executed")
    print("TEST 2 PASSED: Unselected loaders were skipped")