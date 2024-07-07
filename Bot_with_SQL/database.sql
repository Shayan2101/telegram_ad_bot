CREATE DATABASE Shayan2101$database_name;
USE Shayan2101$database_name
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) NOT NULL UNIQUE);
CREATE TABLE ads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    photo_url TEXT NOT NULL,
    category VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (category) REFERENCES categories(category));