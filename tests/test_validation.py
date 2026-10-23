from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


import transform

with TemporaryDirectory() as temp_dir:
    test_root = Path(temp_dir)
    raw_dir = test_root / "data" / "raw" / "drivers"
    raw_dir.mkdir(parents=True)

    test_file = raw_dir / "drivers_offset_0.json"
    test_file.write_text("{}", encoding="utf-8")

    with patch.object(transform, "PROJECT_ROOT", test_root):

        # Test 1: Missing completion marker
        try:
            transform.validate_completed_extractions(
                "drivers", "drivers_offset_*.json"
            )
        except RuntimeError as e:
            print("TEST 1 PASSED:", e)
        else:
            raise AssertionError(
                "Validation should reject extraction without a completion marker"
            )

        # Test 2: Completion marker exists
        (raw_dir / "drivers_COMPLETED").touch()

        files = transform.validate_completed_extractions(
            "drivers", "drivers_offset_*.json"
        )

        assert files == [test_file]
        print("TEST 2 PASSED: Completed extraction accepted")