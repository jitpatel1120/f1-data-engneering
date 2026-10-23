from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


import extract
import transform

with TemporaryDirectory() as temp_dir:
    test_root = Path(temp_dir)
    raw_dir = test_root / "data" / "raw" / "drivers"
    raw_dir.mkdir(parents=True)

    # Existing completed extraction
    old_file = raw_dir / "drivers_offset_0.json"
    old_file.write_text(
        json.dumps({"old_data": True}),
        encoding="utf-8"
    )
    marker = raw_dir / "drivers_COMPLETED"
    marker.touch()

    # Valid new API response
    new_data = {
        "MRData": {
            "limit": "100",
            "offset": "0",
            "total": "1",
            "DriverTable": {
                "Drivers": [{"driverId": "verstappen"}]
            }
        }
    }

    response = Mock()
    response.status_code = 200
    response.json.return_value = new_data

    # Simulate failure when publishing the staged file
    with (
        patch.object(extract, "PROJECT_ROOT", test_root),
        patch.object(transform, "PROJECT_ROOT", test_root),
        patch.object(extract.requests, "get", return_value=response),
        patch.object(extract.time, "sleep"),
        patch.object(extract.shutil, "move", side_effect=OSError("Simulated disk error"))
    ):
        try:
            extract.extract_endpoint("drivers", mode="refresh")
        except OSError as e:
            print("TEST 1 PASSED: Refresh failed as expected:", e)
        else:
            raise AssertionError("Refresh should have failed")

        assert not marker.exists()
        print("TEST 2 PASSED: Completion marker is absent")

        try:
            transform.transform_drivers()
        except RuntimeError as e:
            print("TEST 3 PASSED: Transformation blocked:", e)
        else:
            raise AssertionError("Transformation should have been blocked")
    
    # Retry refresh after the simulated failure
    with (
        patch.object(extract, "PROJECT_ROOT", test_root),
        patch.object(transform, "PROJECT_ROOT", test_root),
        patch.object(extract.requests, "get", return_value=response),
        patch.object(extract.time, "sleep")
    ):
        extract.extract_endpoint("drivers", mode="refresh")

        # Verify successful recovery
        assert marker.exists()

        with old_file.open("r", encoding="utf-8") as f:
            recovered_data = json.load(f)

        assert recovered_data == new_data

        # Verify transformation now succeeds
        drivers = transform.transform_drivers()

        assert len(drivers) == 1
        assert drivers[0]["driver_id"] == "verstappen"

        print("TEST 4 PASSED: Refresh recovered successfully")
        print("TEST 5 PASSED: Transformation succeeded after recovery")