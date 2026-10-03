from pathlib import Path
import json
from datetime import date
from datetime import time
from datetime import timedelta
from decimal import Decimal


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# DRIVER SCHEMA
# driver_id          varchar
# permanent_number   varchar
# code               varchar    
# given_name         varchar
# family_name        varchar
# date_of_birth      date
# nationality        varchar

def transform_drivers():

    wd = PROJECT_ROOT / "data" / "raw" / "drivers"
    drivers = []
    

    for file in wd.glob("drivers_offset_*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_drivers = data["MRData"]["DriverTable"]["Drivers"]

            for driver in raw_drivers:

                drivers.append ( 
                    {
                        "driver_id": driver["driverId"],
                        "given_name": driver.get("givenName"),
                        "family_name": driver.get("familyName"),
                        "date_of_birth": (date.fromisoformat(driver["dateOfBirth"])if driver.get("dateOfBirth")else None),
                        "nationality": driver.get("nationality"), 
                        "permanent_number": driver.get("permanentNumber"),
                        "code": driver.get("code")
                    }
                )

    return drivers
            
# CONSTRUCTOR SCHEMA
# constructor_id          varchar
# constructor_name        varchar
# constructor_nationality varchar
def transform_constructors():

    wd = PROJECT_ROOT / "data" / "raw" / "constructors"
    constructors = []

    for file in wd.glob("constructors_offset_*.json"):
  
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_constructors = data["MRData"]["ConstructorTable"]["Constructors"]

            for constructor in raw_constructors:

                constructors.append(
                    {
                        "constructor_id": constructor["constructorId"],
                        "name": constructor.get("name"),
                        "nationality": constructor.get("nationality")
                    }
                )

    return constructors


#CIRCUITS SCHEMA
# circuit_id varchar
# circuit_name varchar
# latitude decimal 
# longitude decimal
# locality varchar
# country varchar

def transform_circuits():

    wd = PROJECT_ROOT / "data" / "raw" / "circuits"
    circuits = []

    for file in wd.glob("circuits_offset_*.json"):
  
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_circuits = data["MRData"]["CircuitTable"]["Circuits"]

            for circuit in raw_circuits:

                circuits.append(
                    {
                        "circuit_id": circuit["circuitId"],
                        "name": circuit.get("circuitName"),
                        "latitude": (Decimal(circuit.get("Location", {}).get("lat")) if circuit.get("Location", {}).get("lat") else None),
                        "longitude": (Decimal(circuit.get("Location", {}).get("long")) if circuit.get("Location", {}).get("long") else None),
                        "locality": circuit.get("Location", {}).get("locality"),
                        "country": circuit.get("Location", {}).get("country")
                    }
                )

    return circuits


# RACE SCHEMA
# season int
# round int
# race_name varchar
# circuit_id varchar
# date date
# time time
# first_practice_date date
# first_practice_time time
# same for second practice, third practice and qualifying

def transform_races():

    wd = PROJECT_ROOT / "data" / "raw" / "races"
    races = []

    for file in wd.glob("races_*_offset_*.json"):
  
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:

                races.append(
                    {
                        "season": int(race["season"]),
                        "round": int(race["round"]),
                        "race_name": race.get("raceName"),
                        "circuit_id": race["Circuit"]["circuitId"],
                        "date": (date.fromisoformat(race["date"])if race.get("date")else None),
                        "time": (time.fromisoformat(race["time"]) if race.get("time") else None)
                    }
                )

    return races



def sort_key(file):
    parts = file.stem.split("_")
    return int(parts[1]), int(parts[3])

def duration_to_millis(value):
    if not value:
        return None

    parts = value.split(":")

    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    elif len(parts) == 1:
        hours = 0
        minutes = 0
        seconds = parts[0]
    else:
        raise ValueError(f"Invalid duration: {value}")

    return round(
        (
            int(hours) * 3600
            + int(minutes) * 60
            + float(seconds)
        ) * 1000
    )



# RESULT SCHEMA
# season int
# round int
# position int
# points numeric
# driver_id varchar
# constructor_id varchar
# grid int
# laps int
# status varchar
# time_millis bigint
# fastest_lap_time bigint    
def transform_results():

    wd = PROJECT_ROOT / "data" / "raw" / "results"
    results = []

    for file in sorted(wd.glob("results_*_offset_*.json"), key=sort_key):
        
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:

                for result in race["Results"]:

                    result_time_millis = result.get("Time", {}).get("millis")
                    fastest_lap_time = (result.get("FastestLap", {}).get("Time", {}).get("time"))

                    results.append(
                        {
                            "season": int(race["season"]),
                            "round": int(race["round"]),
                            "position": int(result["position"]),
                            "points": Decimal(result["points"]),
                            "driver_id": result["Driver"]["driverId"],
                            "constructor_id": result["Constructor"]["constructorId"],
                            "grid": int(result["grid"]),
                            "laps": int(result["laps"]),
                            "status": result.get("status"),
                            "time_millis": int(result_time_millis) if result_time_millis else None,
                            "fastest_lap_time_millis": duration_to_millis(fastest_lap_time)
                        }
                    )

    return results

# QUALIFYIN SCHEMA
# season int
# round int
# position int
# driver_id varchar
# constructor_id varchar
# Q1_millis time duration in milliseconds
# Q2_millis time duration in milliseconds
# Q3_millis time duration in milliseconds
def transform_qualifying():

    wd = PROJECT_ROOT / "data" / "raw" / "qualifying"
    qualifying_result = []

    for file in sorted(wd.glob("qualifying_*_offset_*.json"), key=sort_key):
        
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:

                for qualifying in race["QualifyingResults"]:

                    qualifying_result.append(
                        {
                            "season": int(race["season"]),
                            "round": int(race["round"]),
                            "position": int(qualifying["position"]),
                            "driver_id": qualifying["Driver"]["driverId"],
                            "constructor_id": qualifying["Constructor"]["constructorId"],
                            "q1_millis": duration_to_millis(qualifying.get("Q1")),
                            "q2_millis": duration_to_millis(qualifying.get("Q2")),
                            "q3_millis": duration_to_millis(qualifying.get("Q3"))
                        }
                    )

    return qualifying_result


# LAP SCHEMA
# season int
# round int
# lap_number int
# driver_id varchar
# position int
# lap_time_millis time duration in milliseconds

def round_sort_key(file):
    parts = file.stem.split("_")
    return int(parts[1]), int(parts[2]), int(parts[4])

def transform_laps():

    wd = PROJECT_ROOT / "data" / "raw" / "laps"
    laps = []

    for file in sorted(wd.glob("laps_*_*_offset_*.json"), key=round_sort_key):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:
                for lap in race["Laps"]:
                    for timing in lap["Timings"]:

                        laps.append(
                            {
                                "season": int(race["season"]),
                                "round": int(race["round"]),
                                "lap_number": int(lap["number"]),
                                "driver_id": timing["driverId"],
                                "lap_time_millis": duration_to_millis(timing["time"]),
                                "position": int(timing["position"])
                            }
                            
                        )
    return laps


# PITSTOP SCHEMA
# season int
# round int
# lap_number int
# driver_id varchar
# stop int
# time time
# duration_millis time duration in milliseconds
def transform_pitstops():

    wd = PROJECT_ROOT / "data" / "raw" / "pitstops"
    pitstops = []

    for file in sorted(wd.glob("pitstops_*_*_offset_*.json"), key=round_sort_key):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:
                for pitstop in race["PitStops"]:
                    pitstops.append(
                        {
                            "season": int(race["season"]),
                            "round": int(race["round"]),
                            "lap_number": int(pitstop["lap"]),
                            "driver_id": pitstop["driverId"],
                            "stop": int(pitstop["stop"]),
                            "time": (time.fromisoformat(pitstop["time"])),
                            "duration_millis": duration_to_millis(pitstop["duration"])
                        }
                        
                    )
    return pitstops


    
# SPRINT SCHEMA
# season int
# round int
# position int
# points numeric
# driver_id varchar
# constructor_id varchar
# grid int
# laps int
# status varchar
# time_millis bigint
# fastest_lap_time bigint  
def transform_sprint_results():

    wd = PROJECT_ROOT / "data" / "raw" / "sprint"
    sprints = []

    for file in sorted(wd.glob("sprint_*_offset_*.json"), key=sort_key):
        
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_races = data["MRData"]["RaceTable"]["Races"]

            for race in raw_races:

                for sprint in race["SprintResults"]:

                    sprint_time_millis = sprint.get("Time", {}).get("millis")
                    fastest_lap_time = (sprint.get("FastestLap", {}).get("Time", {}).get("time"))

                    sprints.append(
                        {
                            "season": int(race["season"]),
                            "round": int(race["round"]),
                            "position": int(sprint["position"]),
                            "points": Decimal(sprint["points"]),
                            "driver_id": sprint["Driver"]["driverId"],
                            "constructor_id": sprint["Constructor"]["constructorId"],
                            "grid": int(sprint["grid"]),
                            "laps": int(sprint["laps"]),
                            "status": sprint.get("status"),
                            "time_millis": int(sprint_time_millis) if sprint_time_millis else None,
                            "fastest_lap_time_millis": duration_to_millis(fastest_lap_time)
                        }
                    )

    return sprints

if __name__ == "__main__":
    # drivers = transform_drivers()

    # print(f"Transformed {len(drivers)} drivers")
    # print(drivers[0])
    # print(type(drivers[0]["date_of_birth"]))


    # constructor = transform_constructors()
    # print(f"Transformed {len(constructor)} constructor")
    # print(constructor[0])


    # circuits = transform_circuits()
    # print(f"Transformed {len(circuits)} circuits")
    # print(circuits[0])
    # print(type(circuits[0]["latitude"]))
    # print(type(circuits[0]["longitude"]))


    # races = transform_races()
    # print(f"Transformed {len(races)} races")
    # print(races[0])
    # for key, value in races[0].items():
    #     print(key, value, type(value))

    # results = transform_results()
    # print(results)

    # qualifying = transform_qualifying()
    # print(qualifying)

    # laps = transform_laps()
    # print(laps)

    # pitstops = transform_pitstops()
    # print(pitstops[0]["time"])
   
    sprints = transform_sprint_results()
    print(f"Transformed {len(sprints)} races")
    print(sprints[0])
    for key, value in sprints[0].items():
        print(key, value, type(value))

