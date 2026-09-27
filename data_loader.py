import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# import the csv to sql database

df_vehicles=pd.read_csv(r"C:\Telematics\source_file\vehicles.csv", parse_dates=["purchase_date"])
df_drivers=pd.read_csv(r"C:\Telematics\source_file\drivers.csv", parse_dates=["join_date"])
df_trips=pd.read_csv(r"C:\Telematics\source_file\trips.csv", parse_dates=["start_time","end_time"])
df_sensor_events=pd.read_csv(r"C:\Telematics\source_file\sensor_events.csv", parse_dates=["event_time"])
df_maintenance=pd.read_csv(r"C:\Telematics\source_file\maintenance_logs.csv", parse_dates=["service_date"])

# Establishing connection to the database

host="127.0.5.1"        # server IP
user="for_telematics"        # MySQL username
password="Password@123"    # MySQL password
database="vehicle_telematics" 
port=3300
print(repr(password))
password_encoded = quote_plus(password)
print(repr(password_encoded))
connection_string = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}"
engine = create_engine(connection_string)
# Testing Connecting
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT VERSION();"))
        print(f"Connected successfully. MySQL version: {result.fetchone()[0]}")
    with engine.connect() as conn:
            for table in ["vehicles", "drivers", "trips", "sensor_events", "maintenance_logs"]:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                print(f"{table}: {count} rows in database")
except Exception as e:
    print(f"Connection failed: {e}")
    raise SystemExit("Fix connection details above before continuing.")

finally:
    engine.dispose()
    print("Connection closed.")

# TABLES
create_tables_sql = """
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT PRIMARY KEY,
    vehicle_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50),
    fuel_type VARCHAR(20),
    purchase_date DATE
);
 
CREATE TABLE IF NOT EXISTS drivers (
    driver_id INT PRIMARY KEY,
    driver_name VARCHAR(100),
    license_number VARCHAR(50) UNIQUE,
    join_date DATE
);
 
CREATE TABLE IF NOT EXISTS trips (
    trip_id INT PRIMARY KEY,
    vehicle_id INT,
    driver_id INT,
    start_time DATETIME,
    end_time DATETIME,
    start_lat DECIMAL(9,6),
    start_long DECIMAL(9,6),
    end_lat DECIMAL(9,6),
    end_long DECIMAL(9,6),
    distance_km DECIMAL(6,2),
    fuel_used_liters DECIMAL(6,2),
    idle_minutes INT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);
 
CREATE TABLE IF NOT EXISTS sensor_events (
    event_id INT PRIMARY KEY,
    trip_id INT,
    event_type VARCHAR(30),
    event_time DATETIME,
    speed_at_event DECIMAL(5,2),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
);
 
CREATE TABLE IF NOT EXISTS maintenance_logs (
    maintenance_id INT PRIMARY KEY,
    vehicle_id INT,
    service_date DATE,
    odometer_reading INT,
    service_type VARCHAR(100),
    cost DECIMAL(8,2),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
);
"""
 
with engine.connect() as conn:
    for statement in create_tables_sql.split(";"):
        if statement.strip():
            conn.execute(text(statement))
    conn.commit()
print("Tables created (or already existed).")
 
# INSERT INTO MYSQL 
try:
    df_vehicles.to_sql("vehicles", engine, if_exists="append", index=False)
    print(f"Inserted {len(df_vehicles)} rows into vehicles")
 
    df_drivers.to_sql("drivers", engine, if_exists="append", index=False)
    print(f"Inserted {len(df_drivers)} rows into drivers")
 
    df_trips.to_sql("trips", engine, if_exists="append", index=False)
    print(f"Inserted {len(df_trips)} rows into trips")
 
    df_sensor_events.to_sql("sensor_events", engine, if_exists="append", index=False)
    print(f"Inserted {len(df_sensor_events)} rows into sensor_events")
 
    df_maintenance.to_sql("maintenance_logs", engine, if_exists="append", index=False)
    print(f"Inserted {len(df_maintenance)} rows into maintenance_logs")
 
    print("\nAll data loaded successfully.")
 
except Exception as e:
    print(f"Error while insert")