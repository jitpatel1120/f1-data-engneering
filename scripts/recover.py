from pathlib import Path
import json
import shutil
import hashlib

def calculate_checksum(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()

def recover_endpoint(endpoint: str, file_prefix: str, confirm: bool = False):
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    output_dir = PROJECT_ROOT / "data" / "raw" / endpoint
    backup_dir = output_dir / ".backup" / file_prefix


    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")

    manifest_path = backup_dir / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Backup manifest not found: {manifest_path}"
        )

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("file_prefix") != file_prefix:
        raise RuntimeError(
            f"Backup manifest prefix mismatch for {file_prefix}"
        )
    
    backup_files = list(
        backup_dir.glob(f"{file_prefix}_offset_*.json")
    )

    published_files = list(
        output_dir.glob(f"{file_prefix}_offset_*.json")
    )

    if not backup_files:
        raise RuntimeError(
            f"No backup files found for {file_prefix}. "
            "Cannot safely recover the dataset."
        )

    offsets = set()
    expected_total = None
    expected_limit = None

    for file in backup_files:
        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "MRData" not in data:
            raise ValueError(
                f"Invalid backup file: {file.name}"
            )

        mrdata = data["MRData"]

        offset = int(mrdata["offset"])
        total = int(mrdata["total"])
        limit = int(mrdata["limit"])

        expected_filename = f"{file_prefix}_offset_{offset}.json"

        if file.name != expected_filename:
            raise RuntimeError(
                f"Backup filename mismatch: {file.name}. "
                f"Expected {expected_filename}"
            )

        if expected_total is None:
            expected_total = total
            expected_limit = limit
        elif total != expected_total or limit != expected_limit:
            raise RuntimeError(
                f"Inconsistent pagination metadata in {file.name}"
            )

        offsets.add(offset)
    
    if expected_limit <= 0:
        raise ValueError("Backup pagination limit must be positive")

    expected_offsets = set(
        range(0, max(expected_total, 1), expected_limit)
    )

    if offsets != expected_offsets:
        raise RuntimeError(
            f"Incomplete backup for {file_prefix}. "
            f"Expected offsets: {sorted(expected_offsets)}, "
            f"found: {sorted(offsets)}"
        )

    backup_names = {file.name for file in backup_files}
    active_names = {file.name for file in published_files}

    manifest_files = manifest.get("files")

    if not isinstance(manifest_files, list):
        raise ValueError(
            f"Invalid manifest: 'files' must be a list for {file_prefix}"
        )

    if not all(isinstance(name, str) for name in manifest_files):
        raise ValueError(
            f"Invalid manifest: filenames must be strings"
        )

    expected_backup_names = set(manifest_files)

    if len(expected_backup_names) != len(manifest_files):
        raise ValueError(
            f"Duplicate filenames in manifest for {file_prefix}"
        )

    if backup_names != expected_backup_names:
        missing_files = expected_backup_names - backup_names
        unexpected_files = backup_names - expected_backup_names

        raise RuntimeError(
            f"Backup manifest mismatch for {file_prefix}. "
            f"Missing files: {sorted(missing_files)}. "
            f"Unexpected files: {sorted(unexpected_files)}."
        )

    conflicting_names = backup_names & active_names

    if not confirm:
        print(f"Recovery inspection for {file_prefix}:")
        print(f"Backup files: {len(backup_files)}")
        print(f"Active files: {len(published_files)}")
        print(f"Filename conflicts: {len(conflicting_names)}")
        print("No files were modified.")
        return

    recovery_temp_dir = output_dir / ".recovery_temp" / file_prefix

    if recovery_temp_dir.exists():
        raise RuntimeError(
            f"Recovery temporary directory already exists: {recovery_temp_dir}. "
            "Inspect it before continuing."
        )

    recovery_temp_dir.mkdir(parents=True, exist_ok=False)

    try:
        for file in published_files:
            destination = recovery_temp_dir / file.name
            shutil.move(str(file), str(destination))

    except Exception:
        for file in recovery_temp_dir.glob(f"{file_prefix}_offset_*.json"):
            destination = output_dir / file.name
            shutil.move(str(file), str(destination))

        raise
    
    try:
        # Restore backup files
        for file in backup_files:
            destination = output_dir / file.name
            shutil.copy2(str(file), str(destination))

        # Verify restored files
        for file in backup_files:
            restored_file = output_dir / file.name

            if not restored_file.exists():
                raise RuntimeError(
                    f"Restored file missing: {restored_file.name}"
                )

            if calculate_checksum(file) != calculate_checksum(restored_file):
                raise RuntimeError(
                    f"Checksum mismatch: {restored_file.name}"
                )

    except Exception:
        # Remove restored files, including partial copies
        for file in backup_files:
            destination = output_dir / file.name

            if destination.exists():
                destination.unlink()

        # Restore previously active files
        for file in recovery_temp_dir.glob(f"{file_prefix}_offset_*.json"):
            destination = output_dir / file.name
            shutil.move(str(file), str(destination))

        raise
    
    print(f"Recovery completed successfully for {file_prefix}.")
    print(f"Restored and verified {len(backup_files)} files.")
    print(f"Original backup preserved at: {backup_dir}")
    print(f"Previous active files preserved at: {recovery_temp_dir}")