import os
import psycopg
from dotenv import load_dotenv
import argparse

load_dotenv()

from transform import (
    transform_drivers,
    transform_constructors,
    transform_circuits,
    transform_races,
    transform_results,
    transform_qualifying,
    transform_laps,
    transform_pitstops,
    transform_sprint_results
)



def load_drivers(cursor):
    drivers = transform_drivers()


    drivers_upsert_query = """
        INSERT INTO f1.drivers (
            driver_id,
            permanent_number,
            code,
            given_name,
            family_name,
            date_of_birth,
            nationality
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (driver_id) DO UPDATE
        SET
            permanent_number = EXCLUDED.permanent_number,
            code = EXCLUDED.code,
            given_name = EXCLUDED.given_name,
            family_name = EXCLUDED.family_name,
            date_of_birth = EXCLUDED.date_of_birth,
            nationality = EXCLUDED.nationality;
        """

    driver_parameters = [
        (
            driver["driver_id"],
            driver.get("permanent_number"),
            driver.get("code"),
            driver["given_name"],
            driver["family_name"],
            driver["date_of_birth"],
            driver.get("nationality")
        )
        for driver in drivers
    ]
    
    cursor.executemany(drivers_upsert_query, driver_parameters)

    return len(driver_parameters)


def load_constructors(cursor):

    constructors = transform_constructors()


    constructors_upsert_query = """
        INSERT INTO f1.constructors (
            constructor_id,
            name,
            nationality
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (constructor_id) DO UPDATE
        SET
            name = EXCLUDED.name,
            nationality = EXCLUDED.nationality;
        """

    constructor_parameters = [
        (
            constructor["constructor_id"],
            constructor["name"],
            constructor.get("nationality")
        )
        for constructor in constructors
    ]

    cursor.executemany(constructors_upsert_query, constructor_parameters)

    return len(constructor_parameters)


def load_circuits(cursor):
    
    circuits = transform_circuits()

    circuits_upsert_query = """
        INSERT INTO f1.circuits (
            circuit_id,
            name,
            latitude,
            longitude,
            locality,
            country
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (circuit_id) DO UPDATE
        SET
            name = EXCLUDED.name,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            locality = EXCLUDED.locality,
            country = EXCLUDED.country;
        """

    circuit_parameters = [
        (
            circuit["circuit_id"],
            circuit["name"],
            circuit['latitude'],
            circuit["longitude"],
            circuit.get("locality"),
            circuit.get("country")
        )
        for circuit in circuits
    ]

    cursor.executemany(circuits_upsert_query, circuit_parameters)

    return len(circuit_parameters)



def load_races(cursor):

    races = transform_races()

    races_upsert_query = """
        INSERT INTO f1.races (
            season,
            round,
            race_name,
            circuit_id,
            date,
            time
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round) DO UPDATE
        SET
            race_name = EXCLUDED.race_name,
            circuit_id = EXCLUDED.circuit_id,
            date = EXCLUDED.date,
            time = EXCLUDED.time;
        """


    race_parameters = [
        (
            race["season"],
            race["round"],
            race['race_name'],
            race["circuit_id"],
            race["date"],
            race.get("time")
        )
        for race in races
    ]

    cursor.executemany(races_upsert_query, race_parameters)

    return len(race_parameters)



def load_results(cursor):

    results = transform_results()

    results_upsert_query = """
        INSERT INTO f1.results (
            season,
            round,
            position,
            points,
            driver_id,
            constructor_id,
            grid,
            laps,
            status,
            time_millis,
            fastest_lap_time_millis
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round, driver_id) DO UPDATE
        SET
            position = EXCLUDED.position,
            points = EXCLUDED.points,
            constructor_id = EXCLUDED.constructor_id,
            grid = EXCLUDED.grid,
            laps = EXCLUDED.laps,
            status = EXCLUDED.status,
            time_millis = EXCLUDED.time_millis,
            fastest_lap_time_millis = EXCLUDED.fastest_lap_time_millis;
        """

    result_parameters = [
        (
            result["season"],
            result["round"],
            result['position'],
            result["points"],
            result["driver_id"],
            result["constructor_id"],
            result["grid"],
            result["laps"],
            result.get('status'),
            result.get("time_millis"),
            result.get("fastest_lap_time_millis")
        )
        for result in results
    ]

    cursor.executemany(results_upsert_query, result_parameters)

    return len(result_parameters)


def load_qualifying(cursor):
    
    qualifying_result = transform_qualifying()

    qualifying_upsert_query = """
        INSERT INTO f1.qualifying (
            season,
            round,
            position,
            driver_id,
            constructor_id,
            q1_millis, 
            q2_millis,
            q3_millis
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round, driver_id) DO UPDATE
        SET
            position = EXCLUDED.position,
            constructor_id = EXCLUDED.constructor_id,
            q1_millis = EXCLUDED.q1_millis,
            q2_millis = EXCLUDED.q2_millis,
            q3_millis = EXCLUDED.q3_millis;
        """


    qualifying_parameters = [
        (
            qualifying["season"],
            qualifying["round"],
            qualifying['position'],
            qualifying["driver_id"],
            qualifying["constructor_id"],
            qualifying.get('q1_millis'),
            qualifying.get("q2_millis"),
            qualifying.get("q3_millis")
        )
        for qualifying in qualifying_result
    ]

    cursor.executemany(qualifying_upsert_query, qualifying_parameters)

    return len(qualifying_parameters)

def load_laps(cursor):

    laps = transform_laps()

    laps_upsert_query = """
        INSERT INTO f1.laps (
            season,
            round,
            lap_number,
            driver_id,
            lap_time_millis,
            position
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round, lap_number, driver_id) DO UPDATE
        SET
            lap_time_millis = EXCLUDED.lap_time_millis,
            position = EXCLUDED.position;
        """

    lap_parameters = [
        (
            lap["season"],
            lap["round"],
            lap["lap_number"],
            lap["driver_id"],
            lap["lap_time_millis"],
            lap["position"]
        )
        for lap in laps
    ]

    cursor.executemany(laps_upsert_query, lap_parameters)

    return len(lap_parameters)

def load_pitstops(cursor):

    pitstops = transform_pitstops()

    pitstops_upsert_query = """
        INSERT INTO f1.pitstops (
            season,
            round,
            lap_number,
            driver_id,
            stop,
            time,
            duration_millis
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round, driver_id, stop) DO UPDATE
        SET
            lap_number = EXCLUDED.lap_number,
            time = EXCLUDED.time,
            duration_millis = EXCLUDED.duration_millis;
        """

    pitstop_parameters = [
        (
            pitstop["season"],
            pitstop["round"],
            pitstop['lap_number'],
            pitstop["driver_id"],
            pitstop["stop"],
            pitstop.get('time'),
            pitstop.get("duration_millis")
        )
        for pitstop in pitstops
    ]

    cursor.executemany(pitstops_upsert_query, pitstop_parameters)

    return len(pitstop_parameters)


def load_sprint_results(cursor):

    sprint_results = transform_sprint_results()


    sprint_results_upsert_query = """
        INSERT INTO f1.sprint_results (
            season,
            round,
            position,
            points,
            driver_id,
            constructor_id,
            grid,
            laps,
            status,
            time_millis,
            fastest_lap_time_millis
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (season, round, driver_id) DO UPDATE
        SET
            position = EXCLUDED.position,
            points = EXCLUDED.points,
            constructor_id = EXCLUDED.constructor_id,
            grid = EXCLUDED.grid,
            laps = EXCLUDED.laps,
            status = EXCLUDED.status,
            time_millis = EXCLUDED.time_millis,
            fastest_lap_time_millis = EXCLUDED.fastest_lap_time_millis;
        """

    sprint_result_parameters = [
        (
            result["season"],
            result["round"],
            result['position'],
            result["points"],
            result["driver_id"],
            result["constructor_id"],
            result["grid"],
            result["laps"],
            result.get('status'),
            result.get("time_millis"),
            result.get("fastest_lap_time_millis")
        )
        for result in sprint_results
    ]

    cursor.executemany(sprint_results_upsert_query, sprint_result_parameters)

    return len(sprint_result_parameters)



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
    "--table",
    choices=["drivers", "constructors", "races", "circuits", "results", "qualifying", "laps", "pitstops", "sprint_results", "all"],
    default="all",
    help="Select which table to load (default: all)"
    )

    args = parser.parse_args()

    load_functions = {
        "drivers": load_drivers,
        "constructors": load_constructors,
        "circuits": load_circuits,
        "races": load_races,
        "results": load_results,
        "qualifying": load_qualifying,
        "laps": load_laps,
        "pitstops": load_pitstops,
        "sprint_results": load_sprint_results
    }


    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    ) as conn:
        with conn.cursor() as cursor:
            if args.table == "all":
                for name, function in load_functions.items():
                    count = function(cursor)
                    print(f"Processed {name}: {count} rows")
            else:
                count = load_functions[args.table](cursor)
                print(f"Processed {args.table}: {count} rows")


if __name__ == "__main__":
    main()

