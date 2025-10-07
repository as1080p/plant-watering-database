# 🌱 Automated Plant Watering Dashboard

A full-stack plant watering monitoring system that tracks soil moisture levels using Arduino sensors and provides a web dashboard using Flask and PostgreSQL. The system allows live monitoring, watering/dewatering actions, and historical moisture logs.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Hardware Components](#hardware-components)
- [Software Components](#software-components)
- [Database Schema](#database-schema)
- [Flask App](#flask-app)
- [Sensor Integration](#sensor-integration)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Queries](#queries)
- [Screenshots](#screenshots)
- [License](#license)

---

## Features

- Live monitoring of soil moisture for each plant.
- Water and dewater plants directly from the dashboard.
- Animated Bootstrap cards with plant images.
- Modal popup showing moisture history graph using Chart.js.
- Historical watering logs with timestamps and methods.
- Automatic sensor readings from Arduino inserted into PostgreSQL.
- Supports multiple plants and multiple sensors (scalable).

---

## Architecture

[Arduino Sensor] --> USB --> Python script --> PostgreSQL --> Flask --> Web Dashboard

Copy code

1. **Arduino Sensor**: Reads soil moisture and sends values via serial.
2. **Python Script (`sensor_To_db.py`)**: Reads serial data and inserts into PostgreSQL.
3. **PostgreSQL Database**: Stores Plant info, Soil readings, Sensor data, and Water logs.
4. **Flask App (`app.py`)**: Fetches data, renders dashboard, handles water/dewater actions, provides API endpoints for live sensor readings.
5. **Frontend**: Bootstrap 5, Chart.js for graphs, animated cards, modals, and live updates.

---

## Hardware Components

- Arduino Uno
- Soil Moisture Sensor
- USB Cable to connect Arduino to PC
- (Optional) Power source for Arduino

**Pin Configuration Example:**

| Arduino Pin | Component         |
|-------------|-----------------|
| A0          | Soil Moisture Sensor Analog Output |
| GND         | Sensor GND      |
| 5V          | Sensor VCC      |

---

## Software Components

- Python 3.13
- Flask
- psycopg2 (PostgreSQL connector)
- PostgreSQL (local or cloud)
- Chart.js (for frontend graphs)
- Bootstrap 5 (for UI)

---

## Database Schema

### Tables

1. **Plant**

CREATE TABLE Plant (
    PlantID SERIAL PRIMARY KEY,
    PlantName VARCHAR(50),
    MoistureThreshold NUMERIC
);

2. **SoilReading**
   
CREATE TABLE SoilReading (
    ReadingID SERIAL PRIMARY KEY,
    PlantID INT REFERENCES Plant(PlantID),
    MoistureValue NUMERIC,
    ReadingTime TIMESTAMP DEFAULT NOW()
);

3. **WaterLog**

CREATE TABLE WaterLog (
    LogID SERIAL PRIMARY KEY,
    PlantID INT REFERENCES Plant(PlantID),
    Amount NUMERIC,
    WateredOn TIMESTAMP DEFAULT NOW(),
    Method VARCHAR(50)
);

4. **SensorData**

CREATE TABLE SensorData (
    SensorID SERIAL PRIMARY KEY,
    MoistureValue NUMERIC,
    ReadingTime TIMESTAMP DEFAULT NOW()
);

## Flask App

app.py contains all routes:

/ - Dashboard with plant cards and live sensor display.

/water - POST route to water a plant.

/dewater - POST route to remove water.

/logs - Historical water logs in a table.

/moisture_history/<plant_id> - API returning moisture readings for Chart.js graphs.

/latest_sensor - API returning latest live sensor reading.

## Sensor Integration

- Connect the soil moisture sensor to Arduino.
- Run sensor_To_db.py to read serial values and insert into PostgreSQL.
- Ensure PostgreSQL is running on correct host and port.
- Flask app fetches the latest sensor data from SensorData table for live updates.

## Installation & Setup

1. Clone Repository
2. Setup Virtual Environment

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

3. Install Dependencies

pip install flask psycopg2-binary

4. Configure Database - Update DB_CONFIG in app.py and sensor_To_db.py with host, port, user, password, and database name.
5. Run Flask App

python app.py

6. Run Arduino Script

python sensor_To_db.py

7. Usage - Open http://127.0.0.1:5000 in a browser.
8. View animated plant cards.
9. Click on a card to view moisture history chart.
10. Water or dewater plants with buttons.
11. Monitor live sensor readings at the top of the dashboard.
12. Check /logs page for historical watering logs.

## Queries Used

- List of Main Queries

a) Create Plant table

CREATE TABLE Plant (
    PlantID SERIAL PRIMARY KEY,
    PlantName VARCHAR(50),
    MoistureThreshold NUMERIC
);

b) Create SoilReading table

CREATE TABLE SoilReading (
    ReadingID SERIAL PRIMARY KEY,
    PlantID INT REFERENCES Plant(PlantID),
    MoistureValue NUMERIC,
    ReadingTime TIMESTAMP DEFAULT NOW()
);


c) Create WaterLog table

CREATE TABLE WaterLog (
    LogID SERIAL PRIMARY KEY,
    PlantID INT REFERENCES Plant(PlantID),
    Amount NUMERIC,
    WateredOn TIMESTAMP DEFAULT NOW(),
    Method VARCHAR(50)
);

d) Create SensorData table

CREATE TABLE SensorData (
    SensorID SERIAL PRIMARY KEY,
    MoistureValue NUMERIC,
    ReadingTime TIMESTAMP DEFAULT NOW()
);

e) Insert sensor reading

INSERT INTO SensorData (MoistureValue) VALUES (23.5);

- Stored Functions

a) Water Plant

CREATE OR REPLACE FUNCTION water_plant(p_plant_id INT, p_amount NUMERIC, p_method VARCHAR)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    curr_moisture NUMERIC;
BEGIN
    INSERT INTO WaterLog (PlantID, Amount, WateredOn, Method)
    VALUES (p_plant_id, p_amount, now(), p_method);
    SELECT MoistureValue INTO curr_moisture
    FROM SoilReading
    WHERE PlantID = p_plant_id
    ORDER BY ReadingTime DESC
    LIMIT 1;
    IF curr_moisture IS NULL THEN
        SELECT MoistureThreshold INTO curr_moisture
        FROM Plant
        WHERE PlantID = p_plant_id;
    END IF;
    INSERT INTO SoilReading (PlantID, MoistureValue, ReadingTime)
    VALUES (p_plant_id, LEAST(curr_moisture + p_amount/50, 100.0), now());
END;
$$;

b) Dewater Plant

CREATE OR REPLACE FUNCTION dewater_plant(p_plant_id INT, p_amount NUMERIC, p_method VARCHAR)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    curr_moisture NUMERIC;
BEGIN
    INSERT INTO WaterLog (PlantID, Amount, WateredOn, Method)
    VALUES (p_plant_id, -p_amount, now(), p_method);
    SELECT MoistureValue INTO curr_moisture
    FROM SoilReading
    WHERE PlantID = p_plant_id
    ORDER BY ReadingTime DESC
    LIMIT 1;
    IF curr_moisture IS NULL THEN
        SELECT MoistureThreshold INTO curr_moisture
        FROM Plant
        WHERE PlantID = p_plant_id;
    END IF;
    INSERT INTO SoilReading (PlantID, MoistureValue, ReadingTime)
    VALUES (p_plant_id, GREATEST(curr_moisture - p_amount/50, 0.0), now());
END;
$$;

- Queries for Flask Dashboard

a) Latest soil reading for dashboard

SELECT p.PlantID, p.PlantName, p.MoistureThreshold, s.MoistureValue
FROM Plant p
JOIN (
    SELECT sr1.PlantID, sr1.MoistureValue, sr1.ReadingTime
    FROM SoilReading sr1
    WHERE sr1.ReadingTime = (
        SELECT MAX(sr2.ReadingTime)
        FROM SoilReading sr2
        WHERE sr2.PlantID = sr1.PlantID
    )
) s ON p.PlantID = s.PlantID
ORDER BY p.PlantName;

b) Water Log History

SELECT p.PlantName, w.Amount, w.WateredOn, w.Method 
FROM WaterLog w 
JOIN Plant p ON w.PlantID = p.PlantID 
ORDER BY w.WateredOn DESC;

c) Moisture history for Chart.js

SELECT MoistureValue, ReadingTime 
FROM SoilReading 
WHERE PlantID = %s 
ORDER BY ReadingTime ASC;

d) Latest sensor reading for live update

SELECT MoistureValue, ReadingTime
FROM SensorData
ORDER BY ReadingTime DESC
LIMIT 1;

- Utility Queries

a) List all tables

SELECT tablename 
FROM pg_tables
WHERE schemaname = 'public';

b) Generate first 10 rows for each table

SELECT 'SELECT * FROM ' || tablename || ' LIMIT 10;' AS query
FROM pg_tables
WHERE schemaname = 'public';

c) View first 10 rows for a specific table

SELECT * FROM Plant LIMIT 10;
SELECT * FROM SoilReading LIMIT 10;
SELECT * FROM WaterLog LIMIT 10;
SELECT * FROM SensorData LIMIT 10;

### Screenshots of output
<img width="1919" height="1140" alt="Screenshot 2025-10-07 231652" src="https://github.com/user-attachments/assets/4e38d292-939b-4713-b074-abfeff639600" />
<img width="1919" height="1138" alt="Screenshot 2025-10-07 231840" src="https://github.com/user-attachments/assets/a345a6ff-fade-471b-89bb-d40e6a747cc0" />
<img width="1200" height="723" alt="Screenshot 2025-10-07 231738" src="https://github.com/user-attachments/assets/cbee2a9f-854e-4eeb-9a62-af7767a0917f" />
<img width="706" height="1133" alt="Screenshot 2025-10-07 231805" src="https://github.com/user-attachments/assets/ab6eb36f-8c26-45da-87d1-0a0e2a6ce029" />
<img width="571" height="262" alt="Screenshot 2025-10-07 232619" src="https://github.com/user-attachments/assets/66486739-ef8b-4c76-a789-278dc4cbb69f" />
<img width="1359" height="436" alt="Screenshot 2025-10-07 232913" src="https://github.com/user-attachments/assets/326f7430-45ce-441d-8159-fcda35bbb41e" />
<img width="747" height="439" alt="Screenshot 2025-10-07 232956" src="https://github.com/user-attachments/assets/bc4ba54d-648a-43f4-87a0-82280e8366b1" />
<img width="957" height="440" alt="Screenshot 2025-10-07 233030" src="https://github.com/user-attachments/assets/5b0d8a5d-636e-444c-a17f-1d4914133bad" />
<img width="638" height="443" alt="Screenshot 2025-10-07 233058" src="https://github.com/user-attachments/assets/d9c9eff3-e05b-462c-b125-5671890778fa" />
<img width="646" height="263" alt="Screenshot 2025-10-07 224410" src="https://github.com/user-attachments/assets/4698e46e-308d-4911-aa3c-8582e7de212a" />


