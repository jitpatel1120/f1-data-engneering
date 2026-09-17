import json
import requests
import sys
from pathlib import Path


def extract_drivers():
    offset = 0  # Set the offset to 0 for the first page of results
    while True:
        try:
            url = f"https://api.jolpi.ca/ergast/f1/2026/drivers/?offset={offset}"

            response = requests.get(url, timeout=30) #Make request
            response.raise_for_status() #verify request

            data = response.json() #parse JSON

            output_path = Path(f"/workspaces/f1-data-engneering/data/raw/drivers_offset_{offset}.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2) #write JSON to file

            print(f"Drivers extracted successfully to {output_path} for offset {offset}.")

            mrdata = data['MRData']
            limit, offset, total = int(mrdata['limit']), int(mrdata['offset']), int(mrdata['total'])   
            offset += limit  # Increment the offset for the next page of results
        except requests.RequestException as e:
            print(f"An error occurred while extracting the drivers: {e}", file=sys.stderr)
            sys.exit(1)  # Exit the program with a non-zero status code to indicate an error

        except ValueError as e:
            print(f"An error occurred while parsing the JSON: {e}", file=sys.stderr)
            sys.exit(1)  # Exit the program with a non-zero status code to indicate an error

        if offset >= total:
            break 


if __name__ == "__main__":
    extract_drivers()
