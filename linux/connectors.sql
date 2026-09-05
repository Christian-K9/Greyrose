CREATE DATABASE IF NOT EXISTS Greyrose_DB;

CREATE USER 'greyrose_user'@'localhost' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE ON greyrose_user.* TO 'greyrose_user'@'localhost';
FLUSH PRIVILEGES;

USE Greyrose_DB;

CREATE TABLE IF NOT EXISTS accepted_ports (
    id int AUTOINCREMENT PRIMARY KEY,
    port int,
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS blocked_ports (
    id int AUTOINCREMENT PRIMARY KEY,
    port int,
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS allow_services (
    id int AUTOINCREMENT PRIMARY KEY,
    name varchar(50),
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS blocked_services (
    id int AUTOINCREMENT PRIMARY KEY,
    name varchar(50),
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS allowed_users (
    id int AUTOINCREMENT PRIMARY KEY,
    name varchar(50),
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS blocked_users (
    id int AUTOINCREMENT PRIMARY KEY,
    name varchar(50),
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS whitelist (
    id int AUTOINCREMENT PRIMARY KEY,
    ip varchar(32),
    time_added CURRENT_TIME
)

CREATE TABLE IF NOT EXISTS blacklist (
    id int AUTOINCREMENT PRIMARY KEY,
    ip varchar(32),
    time_added CURRENT_TIME
)