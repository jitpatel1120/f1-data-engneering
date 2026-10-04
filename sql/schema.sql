CREATE SCHEMA IF NOT EXISTS f1;

CREATE TABLE f1.drivers (
    driver_id varchar(100) primary key,
    permanent_number varchar(50),
    code varchar(50),    
    given_name varchar(100) not null,
    family_name varchar(100) not null,
    date_of_birth date not null,
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