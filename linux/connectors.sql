CREATE DATABASE IF NOT EXISTS Greyrose_DB;

--greyrose_user

--granted_privileges
USE Greyrose_DB;

CREATE TABLE IF NOT EXISTS accepted_ports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    port INT,
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocked_ports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    port INT,
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS allowed_services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocked_services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS allowed_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocked_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whitelist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(50),
    time_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO allowed_services (name)
VALUES ("Greyrose.service");

INSERT INTO allowed_users (name)
VALUES ("sysadmin");

INSERT INTO allowed_users (name)
VALUES ("root");

INSERT INTO allowed_users (name)
VALUES ("splunkfwd");

INSERT INTO allowed_users (name)
VALUES ("nobody");

INSERT INTO whitelist (ip)
VALUES ("192.0.2.1");

INSERT INTO blacklist (ip)
VALUES ("198.51.100.1");

--start: default_ports

--default_ports