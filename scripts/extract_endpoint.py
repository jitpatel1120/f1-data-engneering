import json
import requests
from pathlib import Path
import time

REQUEST_DELAY = 0.5
LIMIT = 100
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_RETRIES = 5
API_BASE_URL = "https://api.jolpi.ca/ergast/f1"

def extract_endpoint(endpoint: str, season: int = None, round_number: int = None):
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
    if completed_marker.exists():
        print(f"{file_prefix} has already been completely extracted. Skipping extraction.")
        return

    offset = 0

    while True:
        # Build path for this page
        output_path = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / endpoint
            / f"{file_prefix}_offset_{offset}.json"
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
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
            completed_marker.touch()
            print(f"Completed extraction for {file_prefix}.")
            break


def backfill_races(start_season: int, end_season: int):
    for season in range(start_season, end_season + 1):
        extract_endpoint("races", season=season)

def backfill_round_endpoint(endpoint: str, start_season: int, end_season: int):
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
            extract_endpoint(endpoint, season=season, round_number=race["round"])


if __name__ == "__main__":
    # extract_endpoint("drivers")
    # extract_endpoint("constructors")
    # extract_endpoint("circuits")
    # extract_endpoint("races", season=2026)
    # extract_endpoint("results", season=2025)
    # extract_endpoint("qualifying", season=2025)
    # extract_endpoint("laps", season=2025, round_number=1)
    # extract_endpoint("pitstops", season=2025, round_number=1)
    # extract_endpoint("sprint", season=2025)
    # backfill_races(2024, 2026)
    # backfill_round_endpoint("laps", 2025, 2025)
    # backfill_round_endpoint("pitstops", 2025, 2025)
    