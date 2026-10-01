from pathlib import Path
import json
from datetime import date
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


if __name__ == "__main__":
    # drivers = transform_drivers()

    # print(f"Transformed {len(drivers)} drivers")
    # print(drivers[0])
    # print(type(drivers[0]["date_of_birth"]))


    # constructor = transform_constructors()
    
    # print(f"Transformed {len(constructor)} constructor")
    # print(constructor[0])

    circuits = transform_circuits()

    print(f"Transformed {len(circuits)} circuits")
    print(circuits[0])
    print(type(circuits[0]["latitude"]))
    print(type(circuits[0]["longitude"]))
