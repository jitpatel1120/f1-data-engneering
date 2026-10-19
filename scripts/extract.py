import json
import requests
from pathlib import Path
import time
import argparse
import shutil

REQUEST_DELAY = 0.5
LIMIT = 100
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_RETRIES = 5
API_BASE_URL = "https://api.jolpi.ca/ergast/f1"

def extract_endpoint(endpoint: str, season: int = None, round_number: int = None, mode: str="backfill"):
    if round_number is not None and season is None:
        raise ValueError("round_number cannot be provided without season")

    # Build URL and file prefix
    if season is None:
        url_base = f"{API_BASE_URL}/{endpoint}/"
        file_prefix = endpoint

    elif round_number is None:
        url_base = f"{API_BASE_URL}/{season}/{endpoint}/"
        file_prefix = f"{endpoint}_{season}"

    else:
        url_base = f"{API_BASE_URL}/{season}/{round_number}/{endpoint}/"
        file_prefix = f"{endpoint}_{season}_{round_number}"

    # Completion marker for this extraction
    completed_marker = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / endpoint
        / f"{file_prefix}_COMPLETED"
    )

    # If the entire extraction was already completed, don't run it again
    if completed_marker.exists() and mode == "backfill":
        print(f"{file_prefix} has already been completely extracted. Skipping extraction.")
        return
    

    output_dir = PROJECT_ROOT / "data" / "raw" / endpoint
    write_dir = (output_dir / ".staging" / file_prefix if mode == "refresh" else output_dir)

    if mode == "refresh":
        backup_dir = output_dir / ".backup" / file_prefix

        if backup_dir.exists():
            raise RuntimeError(
                f"Backup directory already exists: {backup_dir}. "
                "Check for an interrupted refresh before continuing."
            )

        if write_dir.exists():
            shutil.rmtree(write_dir)

        write_dir.mkdir(parents=True, exist_ok=True)

    offset = 0

    while True:
        # Build path for this page
        output_path = write_dir / f"{file_prefix}_offset_{offset}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == "backfill" and output_path.exists():
            print(
                f"{file_prefix}_offset_{offset} already extracted, "
                f"moving to next offset."
            )

            with output_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            url = f"{url_base}?limit={LIMIT}&offset={offset}"

            # Retry request if rate limited
            for attempt in range(MAX_RETRIES):
                response = requests.get(url, timeout=30)

                if response.status_code == 429:
                    wait_time = 2 ** attempt

                    print(
                        f"Rate limited. Retrying in {wait_time} seconds "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )

                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                break

            else:
                raise requests.HTTPError(
                    f"API remained rate limited after "
                    f"{MAX_RETRIES} attempts: {url}"
                )

            data = response.json()

            # Save raw API response
            with output_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

            print(
                f"{endpoint} extracted successfully to "
                f"{output_path} for offset {offset}."
            )

            # Delay after an API request to reduce rate-limit pressure
            time.sleep(REQUEST_DELAY)

        # Read pagination metadata
        mrdata = data["MRData"]

        limit = int(mrdata["limit"])
        offset = int(mrdata["offset"])
        total = int(mrdata["total"])

        # Calculate next page
        offset += limit

        # Check whether all pages have been extracted
        if offset >= total:
            if mode == "backfill":
                completed_marker.touch()

            print(f"Completed downloading {file_prefix}.")
            break

    if mode == "refresh":
        existing_files = list(
            output_dir.glob(f"{file_prefix}_offset_*.json")
        )

        staged_files = list(
            write_dir.glob(f"{file_prefix}_offset_*.json")
        )

        if not staged_files:
            raise RuntimeError(
                f"No staged files found for {file_prefix}. "
                "Aborting refresh to protect existing data."
            )

        offsets = set()
        expected_total = None
        expected_limit = None

        for file in staged_files:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if "MRData" not in data:
                raise ValueError(
                    f"Invalid API response in {file.name}: missing MRData"
                )

            mrdata = data["MRData"]

            offset = int(mrdata["offset"])
            total = int(mrdata["total"])
            limit = int(mrdata["limit"])

            expected_filename = f"{file_prefix}_offset_{offset}.json"

            if file.name != expected_filename:
                raise RuntimeError(
                    f"Pagination filename mismatch: {file.name}. "
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
            raise ValueError("Pagination limit must be positive")

        expected_offsets = set(range(0, max(expected_total, 1), expected_limit))

        if offsets != expected_offsets:
            raise RuntimeError(
                f"Incomplete pagination for {file_prefix}. "
                f"Expected offsets: {sorted(expected_offsets)}, "
                f"found: {sorted(offsets)}"
            )


        try:
            for file in existing_files:
                destination = backup_dir / file.name
                shutil.move(str(file), str(destination))

        except Exception:
            for file in backup_dir.glob(f"{file_prefix}_offset_*.json"):
                destination = output_dir / file.name
                shutil.move(str(file), str(destination))

            raise

        published_files = []

        try:
            for file in staged_files:
                destination = output_dir / file.name
                shutil.move(str(file), str(destination))
                published_files.append(destination)
        except Exception:
            # Remove any partially published refreshed files
            for file in published_files:
                if file.exists():
                    file.unlink()

            # Restore the original JSON files
            for file in backup_dir.glob(f"{file_prefix}_offset_*.json"):
                destination = output_dir / file.name
                shutil.move(str(file), str(destination))

            raise
        else:
            completed_marker.touch()

            print(f"Successfully published {file_prefix}.")

            try:
                shutil.rmtree(write_dir)
                shutil.rmtree(backup_dir)

            except OSError as e:
                print(
                    f"Warning: Refresh succeeded, but cleanup failed "
                    f"for {file_prefix}: {e}"
                )

def backfill_races(start_season: int, end_season: int, mode: str="backfill"):
    for season in range(start_season, end_season + 1):
        extract_endpoint("races", season=season, mode=mode)

def backfill_round_endpoint(endpoint: str, start_season: int, end_season: int, mode: str="backfill"):
    for season in range(start_season, end_season + 1):

        extract_endpoint("races", season=season)

        # JSON file contains the actual race data we need
        race_data_file = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / "races"
            / f"races_{season}_offset_0.json"
        )

        # Read races to determine the rounds for the season
        with race_data_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        races = data["MRData"]["RaceTable"]["Races"]

        for race in races:
            extract_endpoint(endpoint, season=season, round_number=race["round"], mode=mode)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract Formula 1 data from the Jolpica API"
    )

    parser.add_argument("--mode", choices=["backfill", "refresh"], default="backfill")
    parser.add_argument("--start-season", type=int)
    parser.add_argument("--end-season", type=int)
    parser.add_argument("--endpoints",
    choices=["drivers", "constructors", "races", "circuits", "results", "qualifying", "laps", "pitstops", "sprint"],
    required=True,
    nargs="+"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    season_required = any(
        endpoint not in ("drivers", "constructors", "circuits")
        for endpoint in args.endpoints
    )

    if (args.start_season is None) != (args.end_season is None):
        raise ValueError(
            "Both start season and end season must be provided together"
        )

    if season_required and args.start_season is None:
        raise ValueError(
            "Start season and end season are required for the selected endpoints"
        )

    if (
        args.start_season is not None
        and args.end_season is not None
        and args.start_season > args.end_season
    ):
        raise ValueError("Start season cannot be greater than end season")

    for endpoint in args.endpoints:

        if endpoint in ("drivers", "constructors", "circuits"):
            extract_endpoint(endpoint, mode=args.mode)

        elif endpoint == "races":
            backfill_races(args.start_season, args.end_season, mode=args.mode)

        elif endpoint in ("results", "qualifying", "sprint"):
            for season in range(args.start_season, args.end_season + 1):
                extract_endpoint(endpoint, season=season, mode=args.mode)

        elif endpoint in ("laps", "pitstops"):
            backfill_round_endpoint(endpoint, args.start_season, args.end_season, mode=args.mode)

# def main():
#     args = parse_args()
#     print(args)
#     # extract_endpoint("drivers")
#     # extract_endpoint("constructors")
#     # extract_endpoint("circuits")
#     # extract_endpoint("races", season=2026)
#     # extract_endpoint("results", season=2025)
#     # extract_endpoint("qualifying", season=2025)
#     # extract_endpoint("laps", season=2025, round_number=1)
#     # extract_endpoint("pitstops", season=2025, round_number=1)
#     # extract_endpoint("sprint", season=2025)
#     # backfill_races(2024, 2026)
#     # backfill_round_endpoint("laps", 2025, 2025)
#     # backfill_round_endpoint("pitstops", 2025, 2025)


if __name__ == "__main__":
    main()
    