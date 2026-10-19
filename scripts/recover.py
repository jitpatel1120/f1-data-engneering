def recover_endpoint(endpoint: str, file_prefix: str):
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    output_dir = PROJECT_ROOT / "data" / "raw" / endpoint
    backup_dir = output_dir / ".backup" / file_prefix


    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
    
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