from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


import extract

with TemporaryDirectory() as temp_dir:
    test_root = Path(temp_dir)
    raw_dir = test_root / "data" / "raw" / "drivers"
    raw_dir.mkdir(parents=True)

    # Simulate an existing completed extraction
    old_file = raw_dir / "drivers_offset_0.json"
    old_file.write_text(
        json.dumps({"old_data": True}),
        encoding="utf-8"
    )

    completed_marker = raw_dir / "drivers_COMPLETED"
    completed_marker.touch()

    # Simulate a fresh API response
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

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = new_data
    mock_response.raise_for_status.return_value = None

    with (
        patch.object(extract, "PROJECT_ROOT", test_root),
        patch.object(extract.requests, "get", return_value=mock_response),
        patch.object(extract.time, "sleep")
    ):
        extract.extract_endpoint("drivers", mode="refresh")

    # Verify the new data replaced the old data
    with old_file.open("r", encoding="utf-8") as f:
        published_data = json.load(f)

    assert published_data == new_data
    assert completed_marker.exists()
    assert not (raw_dir / ".staging" / "drivers").exists()

    print("TEST PASSED: Refresh replaced old data successfully")