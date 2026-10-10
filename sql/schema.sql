CREATE SCHEMA IF NOT EXISTS f1;

CREATE TABLE f1.drivers (
    driver_id varchar(100) primary key,
    permanent_number varchar(50),
    code varchar(50),    
    given_name varchar(100) not null,
    family_name varchar(100) not null,
    date_of_birth date,
    nationality varchar(50)
);


CREATE TABLE f1.constructors (
    constructor_id varchar(100) primary key,
    name varchar(100) not null,
    nationality varchar(50)
);


CREATE TABLE f1.circuits (
    circuit_id varchar(100) primary key, 
    name varchar(50) not null,
    latitude numeric not null,
    longitude numeric not null,
    locality varchar(50),
    country varchar(50)
);


CREATE TABLE f1.races (
    season int NOT NULL,
    round int NOT NULL, 
    race_name varchar(100) not null,
    circuit_id varchar(100) not null,
    date date not null,
    time time with time zone,
    primary key (season, round),
    FOREIGN KEY (circuit_id) REFERENCES f1.circuits(circuit_id)
);

CREATE TABLE f1.results (
    season int NOT NULL,
    round int NOT NULL,
    position int NOT NULL, 
    points numeric NOT NULL,
    driver_id varchar(100) NOT NULL, 
    constructor_id varchar(100) NOT NULL, 
    grid int NOT NULL,
    laps int NOT NULL,
    status varchar(50),
    time_millis bigint, 
    fastest_lap_time_millis bigint,  
    primary key (season, round, driver_id),
    FOREIGN key(season, round) REFERENCES f1.races(season, round),
    FOREIGN key (driver_id) REFERENCES f1.drivers(driver_id),
    FOREIGN key (constructor_id) REFERENCES f1.constructors(constructor_id)
);

CREATE TABLE f1.qualifying (
    season int NOT NULL, 
    round int NOT NULL,
    position int NOT NULL,
    driver_id varchar(100) NOT NULL,
    constructor_id varchar(100) NOT NULL,
    q1_millis bigint, 
    q2_millis bigint,
    q3_millis bigint,
    primary key(season, round, driver_id),
    FOREIGN key(season, round) REFERENCES f1.races(season, round),
    FOREIGN key (driver_id) REFERENCES f1.drivers(driver_id),
    FOREIGN key (constructor_id) REFERENCES f1.constructors(constructor_id)
);

CREATE TABLE f1.laps (
    season int NOT NULL,
    round int NOT NULL,
    lap_number int NOT NULL,
    driver_id varchar(100) NOT NULL,
    lap_time_millis bigint NOT NULL,
    position int NOT NULL,
    primary key(season, round, driver_id, lap_number),
    FOREIGN key(season, round) REFERENCES f1.races(season, round),
    FOREIGN key (driver_id) REFERENCES f1.drivers(driver_id)
);

CREATE TABLE f1.pitstops (
    season int NOT NULL,
    round int NOT NULL,
    lap_number int NOT NULL, 
    driver_id varchar(100) NOT NULL, 
    stop int NOT NULL,
    time time, 
    duration_millis bigint,
    primary key(season, round, driver_id, stop),
    FOREIGN key(season, round) REFERENCES f1.races(season, round),
    FOREIGN key (driver_id) REFERENCES f1.drivers(driver_id)
);

CREATE TABLE f1.sprint_results (
    season int NOT NULL,
    round int NOT NULL,
    position int NOT NULL, 
    points numeric NOT NULL,
    driver_id varchar(100) NOT NULL, 
    constructor_id varchar(100) NOT NULL, 
    grid int NOT NULL,
    laps int NOT NULL,
    status varchar(50),
    time_millis bigint, 
    fastest_lap_time_millis bigint,  
    primary key (season, round, driver_id),
    FOREIGN key(season, round) REFERENCES f1.races(season, round),
    FOREIGN key (driver_id) REFERENCES f1.drivers(driver_id),
    FOREIGN key (constructor_id) REFERENCES f1.constructors(constructor_id)
);
