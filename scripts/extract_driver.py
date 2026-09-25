import json
import requests
import sys
from pathlib import Path
import time

REQUEST_DELAY = 0.5
LIMIT = 100
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def extract_endpoint(endpoint: str, season: int = None, round_number: int = None):
    if round_number is not None and season is None:
        raise ValueError("round_number cannot be provided without season")

    offset = 0  # Set the offset to 0 for the first page of results

    if season is None:
        url_base = f"https://api.jolpi.ca/ergast/f1/{endpoint}/"
        file_prefix = endpoint
    elif round_number is None:
            url_base = f"https://api.jolpi.ca/ergast/f1/{season}/{endpoint}/"
            file_prefix = f"{endpoint}_{season}"
    else:
        url_base = f"https://api.jolpi.ca/ergast/f1/{season}/{round_number}/{endpoint}/"
        file_prefix = f"{endpoint}_{season}_{round_number}"

    while True:
        try:
            url = f"{url_base}?limit={LIMIT}&offset={offset}"

            response = requests.get(url, timeout=30) #Make request
            response.raise_for_status() #verify request

            time.sleep(REQUEST_DELAY) #delay to avoid rate limiting
            
            data = response.json() #parse JSON

            output_path = (PROJECT_ROOT/ "data"/ "raw"/ endpoint/ f"{file_prefix}_offset_{offset}.json")            
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2) #write JSON to file

            print(f"{endpoint} extracted successfully to {output_path} for offset {offset}.")

            mrdata = data['MRData']
            limit, offset, total = int(mrdata['limit']), int(mrdata['offset']), int(mrdata['total'])   
            offset += limit  # Increment the offset for the next page of results
        except requests.RequestException as e:
            print(f"An error occurred while extracting the {endpoint}: {e}", file=sys.stderr)
            sys.exit(1)  # Exit the program with a non-zero status code to indicate an error

        except ValueError as e:
            print(f"An error occurred while parsing the JSON: {e}", file=sys.stderr)
            sys.exit(1)  # Exit the program with a non-zero status code to indicate an error

        if offset >= total:
            break 

def backfill_races(start_season: int, end_season: int):
    for season in range(start_season, end_season + 1):

        file_path = PROJECT_ROOT / "data" / "raw" / "races" / f"races_{season}_offset_0.json"

        if not file_path.exists():
            extract_endpoint("races", season=season)
        else:
            print(f"Data for races in season {season} already exists. Skipping extraction.")


def backfill_laps(start_season: int, end_season: int):
    for season in range(start_season, end_season + 1):

        file_path = PROJECT_ROOT / "data" / "raw" / "races" / f"races_{season}_offset_0.json"

        if not file_path.exists():
            extract_endpoint("races", season=season)
            
       
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

            races = data["MRData"]["RaceTable"]["Races"]

        for race in races:
            round_number = race["round"]
            lap_file_path = PROJECT_ROOT / "data" / "raw" / "laps" / f"laps_{season}_{round_number}_offset_0.json"

            if not lap_file_path.exists():
                extract_endpoint("laps", season=season, round_number=round_number)
                #print(f"extracting for round {round_number}")
            else:
                print(f"Lap data for season {season}, round {round_number} already exists. Skipping extraction.")
                    
                    
                    


if __name__ == "__main__":
    #extract_endpoint("drivers")
    #extract_endpoint("constructors")
    #extract_endpoint("circuits")
    #extract_endpoint("races", season=2026)
    #extract_endpoint("results", season=2025)
    #extract_endpoint("qualifying", season=2025)
    #backfill_races(2024, 2026)
    #extract_endpoint("laps", season=2025, round_number=1)
    #backfill_laps(2025, 2025)
